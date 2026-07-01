"""Tests GRC — Déclaration d'Applicabilité (SoA)."""

import asyncio

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.main import app
from app.models.entities import Project, UrbanismEntity, UrbanismRelation
from app.services.grc.soa_export import export_soa_csv, export_soa_pdf, export_soa_xlsx
from app.services.grc.soa_service import apply_soa_query, build_soa_rows
from tests.test_ebios_workshop5 import _setup_validated_operational


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def db_session() -> AsyncSession:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        yield session
    await engine.dispose()


def test_build_soa_rows_from_measure_links():
    links = [
        {
            "iso_reference": "5.17",
            "associated_measure": "Renforcement MFA",
            "measure_description": "MFA obligatoire",
            "ebios_source": "Scénario op 1",
            "decision": "Réduire",
            "responsible": "RSSI",
            "status": "Planifié",
            "implemented": "Non",
            "comment": "MFA",
        },
        {
            "iso_reference": "8.13",
            "associated_measure": "Sauvegardes",
            "measure_description": "Backup quotidien",
            "ebios_source": "Scénario op 1",
            "decision": "Réduire",
            "responsible": "Admin SI",
            "status": "Terminé",
            "implemented": "Oui",
            "comment": "",
        },
    ]
    rows = build_soa_rows(links)
    by_ref = {r["iso_reference"]: r for r in rows}
    assert by_ref["5.17"]["applicable"] == "Oui"
    assert by_ref["5.17"]["associated_measure"] == "Renforcement MFA"
    assert by_ref["8.13"]["implemented"] == "Oui"
    assert by_ref["5.1"]["applicable"] == "Non"
    assert by_ref["5.17"]["soa_seed"]["audit_ready"] is True


def test_apply_soa_query_filters():
    rows = build_soa_rows(
        [
            {
                "iso_reference": "5.17",
                "associated_measure": "MFA",
                "measure_description": "desc",
                "ebios_source": "S1",
                "decision": "Réduire",
                "responsible": "Alice",
                "status": "Planifié",
                "implemented": "Non",
                "comment": "",
            }
        ]
    )
    filtered, total = apply_soa_query(rows, applicable="Oui", page=1, page_size=10)
    assert total >= 1
    assert all(r["applicable"] == "Oui" for r in filtered)

    searched, total = apply_soa_query(rows, search="mfa", page=1, page_size=10)
    assert total >= 1


def test_soa_export_formats():
    sample = [
        {
            "iso_reference": "5.17",
            "control_name": "Authentication information",
            "applicable": "Oui",
            "justification": "MFA",
            "implemented": "Non",
            "ebios_source": "Scénario 1",
            "associated_measure": "MFA",
            "decision": "Réduire",
            "responsible": "RSSI",
            "status": "Planifié",
            "comment": "",
        }
    ]
    summary = {
        "soa_version": "ISO/IEC 27001:2022 — SoA v1.0",
        "project_name": "Test",
        "generated_at": "2026-06-24",
        "coverage_rate_percent": 0,
    }
    assert "Référence ISO".encode("utf-8-sig") in export_soa_csv(sample)
    assert export_soa_xlsx(sample, summary=summary)[:2] == b"PK"
    assert export_soa_pdf(sample, summary=summary, project_name="Test")[:4] == b"%PDF"


@pytest.mark.asyncio
async def test_soa_api_from_ebios(db_session: AsyncSession):
    project = Project(name="GRC SoA", organization={})
    db_session.add(project)
    await db_session.flush()
    serveur = UrbanismEntity(
        project_id=project.id,
        entity_type="serveur",
        couche="technique",
        label="Serveur QRadar",
    )
    owner = UrbanismEntity(
        project_id=project.id,
        entity_type="acteur",
        couche="organisation",
        label="Responsable SI",
    )
    db_session.add_all([serveur, owner])
    await db_session.flush()
    db_session.add(
        UrbanismRelation(
            project_id=project.id,
            source_id=serveur.id,
            target_id=owner.id,
            relation_type="est_exploité_par",
            category="exploitation",
        )
    )
    await db_session.commit()
    await db_session.refresh(project)

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    base = f"/api/projects/{project.id}"

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        assessment_id = (await client.get(f"{base}/ebios/assessment")).json()["id"]
        await _setup_validated_operational(client, f"{base}/ebios", assessment_id)
        await client.post(f"{base}/ebios/assessments/{assessment_id}/workshop5/generate-treatments")

        soa = await client.get(f"{base}/grc/soa")
        assert soa.status_code == 200
        data = soa.json()
        assert data["metadata"]["read_only"] is True
        assert data["summary"]["total_controls"] >= 1
        applicable = [r for r in data["rows"] if r["applicable"] == "Oui"]
        assert len(applicable) >= 1
        assert applicable[0]["soa_seed"]["certification_ready"] is True

        csv_export = await client.get(f"{base}/grc/soa/export?format=csv")
        assert csv_export.status_code == 200
        assert "text/csv" in csv_export.headers["content-type"]

        xlsx_export = await client.get(f"{base}/grc/soa/export?format=xlsx")
        assert xlsx_export.status_code == 200
        assert xlsx_export.content[:2] == b"PK"

        pdf_export = await client.get(f"{base}/grc/soa/export?format=pdf")
        assert pdf_export.status_code == 200
        assert pdf_export.content[:4] == b"%PDF"

    app.dependency_overrides.clear()
