"""Tests moteur de corrélation SOC."""

import asyncio
import uuid
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.main import app
from app.models.entities import Project, UrbanismEntity, UrbanismRelation
from app.services.soc.alert_classifier import classify_alert
from app.services.soc.asset_resolver import resolve_agent_to_asset
from app.services.soc.mitre_mapper import map_mitre_from_alert
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


def test_classify_alert_extracts_agent_from_raw():
    alert = classify_alert(
        {
            "id": "a1",
            "timestamp": "2026-06-24T10:00:00Z",
            "rule_id": "5710",
            "rule_level": 10,
            "rule_description": "SSH auth failed",
            "agent_name": "Serveur QRadar",
            "groups": ["authentication_failed", "sshd"],
            "raw": {"agent": {"id": "001", "name": "Serveur QRadar", "ip": "10.0.0.5"}},
        }
    )
    assert alert.agent_ip == "10.0.0.5"
    assert alert.severity_label == "Élevée"
    assert alert.category == "authentication"


def test_asset_resolver_matches_by_ip():
    pid = uuid.uuid4()
    serveur = UrbanismEntity(
        project_id=pid,
        entity_type="serveur",
        couche="technique",
        label="Serveur QRadar",
        properties={"ip": "10.0.0.5"},
    )
    org = UrbanismEntity(
        project_id=serveur.project_id,
        entity_type="organisation",
        couche="organisation",
        label="DSI",
    )
    entities = [serveur, org]
    relations: list[UrbanismRelation] = []
    result = resolve_agent_to_asset(
        agent_id="001",
        agent_name="agent-qradar",
        agent_ip="10.0.0.5",
        entities=entities,
        relations=relations,
    )
    assert result.urbanism_entity_label == "Serveur QRadar"
    assert result.match_method == "ip"
    assert result.confidence >= 0.9


def test_mitre_mapper_from_groups():
    alert = classify_alert(
        {
            "id": "a2",
            "rule_level": 8,
            "groups": ["authentication"],
            "raw": {},
        }
    )
    mitre = map_mitre_from_alert(alert)
    assert mitre["mitre_ready"] is True
    assert "T1078" in mitre["techniques"]


@pytest.mark.asyncio
async def test_soc_correlations_api(db_session: AsyncSession):
    project = Project(name="SOC Corr", organization={})
    db_session.add(project)
    await db_session.flush()
    serveur = UrbanismEntity(
        project_id=project.id,
        entity_type="serveur",
        couche="technique",
        label="Serveur QRadar",
        properties={"ip": "10.0.0.5"},
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

    mock_alerts = {
        "alerts": [
            {
                "id": "alert-1",
                "timestamp": "2026-06-24T12:00:00Z",
                "rule_id": "5710",
                "rule_level": 10,
                "rule_description": "SSH failed",
                "agent_id": "001",
                "agent_name": "Serveur QRadar",
                "agent_ip": "10.0.0.5",
                "full_log": "Failed password",
                "groups": ["authentication"],
                "raw": {"agent": {"id": "001", "name": "Serveur QRadar", "ip": "10.0.0.5"}},
            }
        ],
        "total": 1,
    }

    mock_status = {
        "connected": True,
        "configured": True,
        "wazuh_version": "4.8.0",
        "api_version": "4.8.0",
        "manager": "wazuh-manager",
        "agents_total": 3,
        "agents_active": 2,
    }

    with patch("app.services.soc.correlation_service.get_wazuh_status", AsyncMock(return_value=mock_status)), patch(
        "app.services.soc.correlation_service.get_wazuh_agents",
        AsyncMock(return_value={"total": 3, "agents": []}),
    ), patch("app.services.soc.correlation_service.get_wazuh_alerts", AsyncMock(return_value=mock_alerts)):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            assessment_id = (await client.get(f"{base}/ebios/assessment")).json()["id"]
            await _setup_validated_operational(client, f"{base}/ebios", assessment_id)
            await client.post(f"{base}/ebios/assessments/{assessment_id}/workshop5/generate-treatments")

            response = await client.get(f"/api/soc/correlations?project_id={project.id}")
            assert response.status_code == 200
            data = response.json()
            assert data["summary"]["incidents_count"] == 1
            incident = data["incidents"][0]
            assert incident["supporting_asset"] == "Serveur QRadar"
            assert incident["correlation_seed"]["urbanism_ready"] is True
            assert incident["correlation_seed"]["grc_ready"] is True
            assert incident["read_only"] is True

    app.dependency_overrides.clear()
