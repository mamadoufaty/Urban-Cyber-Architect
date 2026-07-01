"""Tests Atelier 4 EBIOS RM — scénarios opérationnels."""

import asyncio

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.main import app
from app.models.entities import Project, UrbanismEntity
from app.services.ebios.operational_scenario_generator import (
    WORKFLOW_AUTO,
    WORKFLOW_VALIDATED,
    calculate_criticality,
    generate_operational_scenario,
)
from app.services.ebios.workshop4_service import compute_workshop4_progress, is_operational_validated


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


def _operational(validated=False):
    class R:
        pass

    r = R()
    r.record_type = "operational_scenario"
    r.properties = {
        "workflow_status": WORKFLOW_VALIDATED if validated else WORKFLOW_AUTO,
        "operational_scenario_uid": "uid-1",
    }
    return r


def test_generate_operational_scenario_fields():
    class Strategic:
        id = "strat-1"
        label = "Scénario stratégique — Cybercriminels"
        properties = {
            "risk_source_label": "Cybercriminels",
            "feared_event": "Chiffrement des données",
            "target_objective": "Vol de données",
            "severity": "Critique",
            "likelihood": "Élevée",
                "stakeholder_ids": [],
                "supporting_asset_ids": ["a1"],
                "scenario_uid": "strat-uid",
        }

    class Asset:
        id = "a1"
        label = "Serveur QRadar"

    result = generate_operational_scenario(Strategic(), None, [], [Asset()])
    assert "Cybercriminels" in result["threatening_actor"]
    assert "Phishing" in result["entry_point"]
    assert "Serveur QRadar" in result["target"]
    assert "→" in result["attack_path"]
    assert result["operational_scenario_uid"]
    assert result["calculated_criticality"] == calculate_criticality("Critique", "Élevée")


def test_compute_workshop4_progress():
    assert compute_workshop4_progress([]) == 0
    assert compute_workshop4_progress([_operational(), _operational()]) == 0
    assert compute_workshop4_progress([_operational(validated=True)]) == 100
    assert is_operational_validated(_operational(validated=True))


async def _setup_validated_strategic(client, base: str, assessment_id: str) -> None:
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

    await client.post(
        f"{base}/assessments/{assessment_id}/records",
        json={
            "workshop_number": 2,
            "record_type": "risk_source",
            "label": "Cybercriminels",
            "properties": {
                "target_objective": "Vol de données",
                "feared_event": "Chiffrement",
                "severity": "Critique",
                "stakeholder_ids": [stakeholder_id],
                "supporting_asset_ids": [asset_id],
            },
        },
    )

    gen = await client.post(f"{base}/assessments/{assessment_id}/workshop3/generate-scenarios")
    for scenario in gen.json()["records"]:
        props = {**scenario["properties"], "workflow_status": WORKFLOW_VALIDATED}
        await client.patch(
            f"{base}/assessments/{assessment_id}/records/{scenario['id']}",
            json={"properties": props},
        )


@pytest.mark.asyncio
async def test_workshop4_generate_validate_unlock(db_session: AsyncSession):
    project = Project(name="EBIOS W4", organization={})
    db_session.add(project)
    await db_session.flush()
    db_session.add(
        UrbanismEntity(
            project_id=project.id,
            entity_type="serveur",
            couche="technique",
            label="Serveur QRadar",
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
        await _setup_validated_strategic(client, base, assessment_id)

        workshops = (await client.get(f"{base}/assessments/{assessment_id}/workshops")).json()
        assert workshops[3]["status"] == "available"
        assert workshops[4]["status"] == "locked"

        w4_get = await client.get(f"{base}/assessments/{assessment_id}/workshop4")
        assert w4_get.status_code == 200
        assert w4_get.json()["validated_strategic_count"] == 1
        assert w4_get.json()["operational_count"] == 0

        generated = await client.post(
            f"{base}/assessments/{assessment_id}/workshop4/generate-operational-scenarios"
        )
        assert generated.status_code == 200
        assert generated.json()["generated_count"] == 1
        op = generated.json()["records"][0]
        uid1 = op["properties"]["operational_scenario_uid"]
        assert op["properties"]["workflow_status"] == WORKFLOW_AUTO
        assert "attack_path" in op["properties"]

        second = await client.post(
            f"{base}/assessments/{assessment_id}/workshop4/generate-operational-scenarios"
        )
        assert second.json()["generated_count"] == 0

        validated = await client.patch(
            f"{base}/assessments/{assessment_id}/workshop4/scenarios/{op['id']}",
            json={"set_validated": True},
        )
        assert validated.status_code == 200
        assert validated.json()["properties"]["workflow_status"] == WORKFLOW_VALIDATED

        workshops = (await client.get(f"{base}/assessments/{assessment_id}/workshops")).json()
        assert workshops[3]["progress_percent"] == 100
        assert workshops[3]["status"] == "completed"
        assert workshops[4]["status"] == "available"

        deleted = await client.delete(
            f"{base}/assessments/{assessment_id}/workshop4/scenarios/{op['id']}"
        )
        assert deleted.status_code == 204

        regen = await client.post(
            f"{base}/assessments/{assessment_id}/workshop4/generate-operational-scenarios?regenerate=true"
        )
        assert regen.status_code == 200
        uid2 = regen.json()["records"][0]["properties"]["operational_scenario_uid"]
        assert uid2 != uid1

    app.dependency_overrides.clear()
