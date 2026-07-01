"""Tests GRC — Plan de Traitement des Risques (PTR)."""

import asyncio

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.main import app
from app.models.entities import Project, UrbanismEntity, UrbanismRelation
from app.services.grc.ptr_export import export_ptr_csv, export_ptr_pdf, export_ptr_xlsx
from app.services.grc.ptr_service import (
    apply_ptr_query,
    build_ptr_rows,
    derive_progress_percent,
    effective_status,
    normalize_priority,
)
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


def test_normalize_priority_and_progress():
    assert normalize_priority({"priority": "Haute"}, {"criticality": "Élevée"}) == "Élevée"
    assert normalize_priority({"priority": ""}, {"criticality": "Critique"}) == "Critique"
    assert derive_progress_percent({"progress_percent": 75}, "En cours") == 75
    assert derive_progress_percent({}, "Terminé") == 100
    assert effective_status("Planifié", overdue=True) == "En retard"


def test_apply_ptr_query_filters():
    rows = [
        {
            "ptr_id": "ptr-1",
            "responsible": "Alice",
            "organization": "DSI",
            "priority": "Élevée",
            "status": "En cours",
            "treatment_decision": "Réduire",
            "due_date": "",
            "security_measure": "MFA",
            "associated_risk": "R1",
            "risk_source": "Cyber",
            "operational_scenario": "Op1",
            "overdue": False,
            "due_soon": False,
        }
    ]
    filtered, total = apply_ptr_query(rows, responsible="Alice", page=1, page_size=10)
    assert total == 1
    searched, total = apply_ptr_query(rows, search="mfa", page=1, page_size=10)
    assert total == 1


def test_ptr_export_formats():
    sample = [
        {
            "ptr_id": "ptr-1",
            "associated_risk": "Risque 1",
            "risk_source": "Cyber",
            "strategic_scenario": "S1",
            "operational_scenario": "O1",
            "security_measure": "MFA",
            "iso27002_reference": "8.5",
            "responsible": "RSSI",
            "organization": "DSI",
            "priority": "Élevée",
            "budget": 10000,
            "budget_consumed": 2000,
            "due_date": "2026-12-31",
            "status": "En cours",
            "progress_percent": 40,
            "treatment_decision": "Réduire",
            "residual_risk": "Modérée",
            "updated_at": "2026-06-24 10:00",
        }
    ]
    summary = {"project_name": "Test", "total_actions": 1, "global_progress_percent": 40}
    assert "ID PTR".encode("utf-8-sig") in export_ptr_csv(sample) or b"ptr-1" in export_ptr_csv(sample)
    assert export_ptr_xlsx(sample, summary=summary)[:2] == b"PK"
    assert export_ptr_pdf(sample, summary=summary, project_name="Test")[:4] == b"%PDF"


@pytest.mark.asyncio
async def test_ptr_api_from_ebios(db_session: AsyncSession):
    project = Project(name="GRC PTR", organization={})
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

        ptr = await client.get(f"{base}/grc/ptr")
        assert ptr.status_code == 200
        data = ptr.json()
        assert data["metadata"]["limited_edit"] is True
        assert data["summary"]["total_actions"] >= 1
        assert len(data["timeline"]["items"]) >= 0
        row = data["rows"][0]
        assert row["security_measure"]
        assert row["ptr_seed"]["dashboard_ready"] is True

        action_id = row["action_id"]
        patch = await client.patch(
            f"{base}/grc/ptr/actions/{action_id}",
            json={"status": "En cours", "progress_percent": 60},
        )
        assert patch.status_code == 200

        csv_export = await client.get(f"{base}/grc/ptr/export?format=csv")
        assert csv_export.status_code == 200
        assert "text/csv" in csv_export.headers["content-type"]

    app.dependency_overrides.clear()
