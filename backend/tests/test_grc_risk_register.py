"""Tests GRC — Registre des risques."""

import asyncio

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.main import app
from app.models.entities import Project, UrbanismEntity, UrbanismRelation
from app.services.grc.risk_register_export import (
    export_risk_register_csv,
    export_risk_register_pdf,
    export_risk_register_xlsx,
)
from app.services.grc.risk_register_service import apply_risk_register_query
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


def test_apply_risk_register_query_filters_and_paginates():
    rows = [
        {
            "risk_id": "r1",
            "organization": "DSI",
            "severity": "Critique",
            "criticality": "Critique",
            "treatment_decision": "Réduire",
            "status": "En cours",
            "updated_at": "2026-01-02",
            "supporting_asset": "Serveur",
            "risk_source": "Cyber",
            "strategic_scenario": "S1",
            "operational_scenario": "O1",
            "owner_actor": "Alice",
            "decision_maker": "Bob",
            "retained_measures": [],
        },
        {
            "risk_id": "r2",
            "organization": "RH",
            "severity": "Faible",
            "criticality": "Faible",
            "treatment_decision": "Accepter",
            "status": "Validé",
            "updated_at": "2026-01-01",
            "supporting_asset": "App",
            "risk_source": "Erreur",
            "strategic_scenario": "S2",
            "operational_scenario": "O2",
            "owner_actor": "Carol",
            "decision_maker": "Dan",
            "retained_measures": [],
        },
    ]
    filtered, total = apply_risk_register_query(
        rows, organization="DSI", page=1, page_size=10
    )
    assert total == 1
    assert filtered[0]["risk_id"] == "r1"

    searched, total = apply_risk_register_query(rows, search="rh", page=1, page_size=10)
    assert total == 1
    assert searched[0]["risk_id"] == "r2"


def test_export_formats():
    sample = [
        {
            "risk_id": "eval-1",
            "organization": "DSI",
            "supporting_asset": "Serveur",
            "risk_source": "Cybercriminels",
            "strategic_scenario": "Strat 1",
            "operational_scenario": "Op 1",
            "owner_actor": "RSSI",
            "decision_maker": "DG",
            "severity": "Critique",
            "likelihood": "Élevée",
            "criticality": "Critique",
            "treatment_decision": "Réduire",
            "retained_measures": ["MFA"],
            "retained_measures_text": "MFA",
            "residual_risk": "Modérée",
            "status": "En cours",
            "updated_at": "2026-06-24 10:00",
        }
    ]
    assert b"Identifiant" in export_risk_register_csv(sample)
    assert export_risk_register_xlsx(sample)[:2] == b"PK"
    assert export_risk_register_pdf(sample, project_name="Test")[:4] == b"%PDF"


@pytest.mark.asyncio
async def test_risk_register_api_from_ebios(db_session: AsyncSession):
    project = Project(name="GRC Register", organization={})
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

        register = await client.get(f"{base}/grc/risk-register")
        assert register.status_code == 200
        data = register.json()
        assert data["total"] == 1
        assert data["metadata"]["read_only"] is True
        row = data["rows"][0]
        assert row["risk_source"]
        assert row["operational_scenario"]
        assert row["retained_measure_count"] >= 1
        assert data["metadata"]["extensions_ready"]["heatmap"] is True

        csv_export = await client.get(f"{base}/grc/risk-register/export?format=csv")
        assert csv_export.status_code == 200
        assert "text/csv" in csv_export.headers["content-type"]

        xlsx_export = await client.get(f"{base}/grc/risk-register/export?format=xlsx")
        assert xlsx_export.status_code == 200
        assert xlsx_export.content[:2] == b"PK"

        pdf_export = await client.get(f"{base}/grc/risk-register/export?format=pdf")
        assert pdf_export.status_code == 200
        assert pdf_export.content[:4] == b"%PDF"

    app.dependency_overrides.clear()
