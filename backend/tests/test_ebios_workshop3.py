"""Tests Atelier 3 EBIOS RM — scénarios stratégiques et progression."""

import asyncio

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.main import app
from app.models.entities import Project, UrbanismEntity
from app.services.ebios.strategic_scenario_generator import (
    WORKFLOW_AUTO,
    WORKFLOW_VALIDATED,
    generate_strategic_scenario,
)
from app.services.ebios.workshop3_service import compute_workshop3_progress, is_scenario_validated


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


def _scenario(validated=False):
    class R:
        pass

    r = R()
    r.record_type = "strategic_scenario"
    r.properties = {"workflow_status": WORKFLOW_VALIDATED if validated else WORKFLOW_AUTO}
    return r


def test_generate_strategic_scenario_content():
    class RiskSource:
        id = "rs-1"
        label = "Cybercriminels"
        properties = {
            "target_objective": "Vol de données",
            "feared_event": "Fuite de données",
            "severity": "Critique",
            "stakeholder_ids": ["s1"],
            "supporting_asset_ids": ["a1"],
        }

    class Stakeholder:
        id = "s1"
        label = "RSSI"

    class Asset:
        id = "a1"
        label = "CRM"

    result = generate_strategic_scenario(RiskSource(), [Stakeholder()], [Asset()])
    assert "Cybercriminels" in result["title"]
    assert result["workflow_status"] == WORKFLOW_AUTO
    assert result["scenario_uid"]
    assert "Fuite de données" in result["narrative_description"]


def test_compute_workshop3_progress():
    assert compute_workshop3_progress([]) == 0
    assert compute_workshop3_progress([_scenario(), _scenario()]) == 0
    assert compute_workshop3_progress([_scenario(validated=True), _scenario()]) == 50
    assert compute_workshop3_progress([_scenario(validated=True), _scenario(validated=True)]) == 100
    assert is_scenario_validated(_scenario(validated=True))


async def _setup_through_workshop2(client, base: str, assessment_id: str) -> tuple[str, str]:
    payloads_w1 = [
        ("security_scope", "Périmètre", {}),
        ("stakeholder", "RSSI", {"role": "RSSI"}),
        ("security_baseline", "PF", {}),
        ("reference_document", "PSSI", {}),
    ]
    stakeholder_id = None
    for record_type, label, props in payloads_w1:
        resp = await client.post(
            f"{base}/assessments/{assessment_id}/records",
            json={"workshop_number": 1, "record_type": record_type, "label": label, "properties": props},
        )
        if record_type == "stakeholder":
            stakeholder_id = resp.json()["id"]

    imported = await client.post(f"{base}/assessments/{assessment_id}/workshop2/import-urbanism-assets")
    asset_id = imported.json()["records"][0]["id"]

    for i in range(4):
        await client.post(
            f"{base}/assessments/{assessment_id}/records",
            json={
                "workshop_number": 2,
                "record_type": "risk_source",
                "label": f"Source {i + 1}",
                "properties": {
                    "target_objective": "Objectif",
                    "feared_event": "Événement",
                    "severity": "Élevée",
                    "stakeholder_ids": [stakeholder_id],
                    "supporting_asset_ids": [asset_id],
                },
            },
        )
    return stakeholder_id, asset_id


@pytest.mark.asyncio
async def test_workshop3_generate_validate_unlock(db_session: AsyncSession):
    project = Project(name="EBIOS W3", organization={})
    db_session.add(project)
    await db_session.flush()
    db_session.add(
        UrbanismEntity(
            project_id=project.id,
            entity_type="ilot_applicatif",
            couche="applicatif",
            label="App",
        )
    )
    await db_session.commit()
    await db_session.refresh(project)

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    base = f"/api/projects/{project.id}/ebios"

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        assessment_id = (await client.get(f"{base}/assessment")).json()["id"]
        await _setup_through_workshop2(client, base, assessment_id)

        workshops = (await client.get(f"{base}/assessments/{assessment_id}/workshops")).json()
        assert workshops[2]["status"] == "available"
        assert workshops[3]["status"] == "locked"

        generated = await client.post(
            f"{base}/assessments/{assessment_id}/workshop3/generate-scenarios"
        )
        assert generated.status_code == 200
        assert generated.json()["generated_count"] == 4
        scenarios = generated.json()["records"]
        assert scenarios[0]["properties"]["workflow_status"] == WORKFLOW_AUTO
        assert scenarios[0]["properties"]["scenario_uid"]

        workshops = (await client.get(f"{base}/assessments/{assessment_id}/workshops")).json()
        assert workshops[2]["progress_percent"] == 0

        for scenario in scenarios:
            props = {**scenario["properties"], "workflow_status": WORKFLOW_VALIDATED}
            patched = await client.patch(
                f"{base}/assessments/{assessment_id}/records/{scenario['id']}",
                json={"properties": props},
            )
            assert patched.status_code == 200

        workshops = (await client.get(f"{base}/assessments/{assessment_id}/workshops")).json()
        assert workshops[2]["progress_percent"] == 100
        assert workshops[2]["status"] == "completed"
        assert workshops[3]["status"] == "available"

        regen = await client.post(
            f"{base}/assessments/{assessment_id}/workshop3/generate-scenarios?regenerate=true"
        )
        assert regen.status_code == 200
        assert regen.json()["generated_count"] == 4

    app.dependency_overrides.clear()
