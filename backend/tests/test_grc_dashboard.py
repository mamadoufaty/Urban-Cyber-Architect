"""Tests GRC — Dashboard RSSI / COMEX."""

import asyncio

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.main import app
from app.models.entities import Project, UrbanismEntity, UrbanismRelation
from app.services.grc.grc_dashboard_service import (
    build_heatmap,
    compute_comex_summary,
    compute_exposure_by_organization,
    compute_exposure_by_supporting_asset,
    compute_kpis,
    compute_ptr_tracking,
    compute_top_risks,
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


def _sample_rows():
    return [
        {
            "risk_id": "r1",
            "organization": "DSI",
            "supporting_asset": "Serveur A",
            "risk_source": "Cybercriminels",
            "criticality": "Critique",
            "residual_risk": "Élevée",
            "residual_risk_score": 6,
            "initial_risk_score": 12,
            "treatment_decision": "Réduire",
            "status": "En cours",
            "grc_analytics": {"severity_score": 4, "likelihood_score": 3},
        },
        {
            "risk_id": "r2",
            "organization": "DSI",
            "supporting_asset": "Serveur B",
            "risk_source": "Erreur humaine",
            "criticality": "Modérée",
            "residual_risk": "Faible",
            "residual_risk_score": 2,
            "initial_risk_score": 4,
            "treatment_decision": "Accepter",
            "status": "Validé",
            "grc_analytics": {"severity_score": 2, "likelihood_score": 2},
        },
        {
            "risk_id": "r3",
            "organization": "RH",
            "supporting_asset": "Serveur A",
            "risk_source": "Insider",
            "criticality": "Critique",
            "residual_risk": "Critique",
            "residual_risk_score": 12,
            "initial_risk_score": 16,
            "treatment_decision": "Réduire",
            "status": "En cours",
            "grc_analytics": {"severity_score": 4, "likelihood_score": 4},
        },
    ]


def test_compute_kpis():
    rows = _sample_rows()
    ptr = [
        {"category": "planned", "status": "Planifié"},
        {"category": "completed", "status": "Terminé"},
        {"category": "in_progress", "status": "En cours"},
    ]
    measures = [
        {"retained": True, "framework_refs": {"iso27002": "8.5"}},
        {"retained": True, "framework_refs": {"iso27002": ""}},
    ]
    kpis = compute_kpis(rows, ptr, measures)
    assert kpis["total_risks"] == 3
    assert kpis["critical_risks"] == 2
    assert kpis["high_risks"] == 0
    assert kpis["moderate_risks"] == 1
    assert kpis["critical_residual_risks"] == 1
    assert kpis["ptr_open_actions"] == 2
    assert kpis["ptr_completed_actions"] == 1
    assert kpis["treatment_rate_percent"] == pytest.approx(33.3, abs=0.1)
    assert kpis["iso27002_coverage_percent"] == 50.0


def test_build_heatmap():
    heatmap = build_heatmap(_sample_rows())
    assert heatmap["max_count"] >= 1
    assert len(heatmap["cells"]) == 16
    hot_cell = next(c for c in heatmap["cells"] if c["severity_score"] == 4 and c["likelihood_score"] == 4)
    assert hot_cell["count"] == 1
    assert hot_cell["dominant_criticality"] == "Critique"


def test_compute_top_risks():
    top = compute_top_risks(_sample_rows(), limit=2)
    assert len(top) == 2
    assert top[0]["risk_id"] == "r3"
    assert top[0]["criticality"] == "Critique"


def test_exposure_by_organization():
    exposure = compute_exposure_by_organization(_sample_rows())
    assert exposure[0]["label"] == "DSI"
    assert exposure[0]["count"] == 2
    assert exposure[0]["critical_count"] == 1


def test_exposure_by_supporting_asset():
    exposure = compute_exposure_by_supporting_asset(_sample_rows())
    assert exposure[0]["label"] == "Serveur A"
    assert exposure[0]["count"] == 2


def test_compute_ptr_tracking():
    actions = [
        {"action_id": "1", "label": "A1", "status": "Planifié", "due_date": "2099-01-01"},
        {"action_id": "2", "label": "A2", "status": "Terminé", "due_date": ""},
        {"action_id": "3", "label": "A3", "status": "En cours", "due_date": "2020-01-01"},
    ]
    tracking = compute_ptr_tracking(actions)
    assert tracking["planned_count"] == 1
    assert tracking["completed_count"] == 1
    assert tracking["in_progress_count"] == 1
    assert tracking["overdue_count"] == 1


def test_compute_comex_summary():
    comex = compute_comex_summary(_sample_rows(), [], project_name="Métropolis")
    assert comex["global_risk_level"] in ("Faible", "Modérée", "Élevée", "Critique")
    assert "Métropolis" in comex["executive_message"]
    assert comex["decisions_to_arbitrate"] == 2


@pytest.mark.asyncio
async def test_dashboard_rssi_api(db_session: AsyncSession):
    project = Project(name="Métropolis", organization={})
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

        dashboard = await client.get(f"{base}/grc/dashboard-rssi")
        assert dashboard.status_code == 200
        data = dashboard.json()
        assert data["kpis"]["total_risks"] == 1
        assert data["heatmap"]["max_count"] >= 1
        assert len(data["top_risks"]) >= 1
        assert data["metadata"]["read_only"] is True
        assert "Métropolis" in data["comex"]["executive_message"]
        assert data["metadata"]["export_endpoints"]["implemented"] is False

        export_stub = await client.get(f"{base}/grc/dashboard-rssi/export?format=dashboard_pdf")
        assert export_stub.status_code == 501

    app.dependency_overrides.clear()
