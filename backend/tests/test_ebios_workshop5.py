"""Tests Atelier 5 EBIOS RM — traitement des risques et PTR."""

import asyncio

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.main import app
from app.models.entities import Project, UrbanismEntity, UrbanismRelation
from app.services.ebios.security_measure_generator import WORKFLOW_VALIDATED as EVAL_VALIDATED
from app.services.ebios.workshop5_service import compute_workshop5_progress, is_evaluation_validated


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


def _evaluation(validated=False):
    class R:
        pass

    r = R()
    r.record_type = "risk_evaluation"
    r.properties = {
        "workflow_status": EVAL_VALIDATED if validated else "Proposé automatiquement",
        "evaluation_uid": "eval-1",
    }
    return r


def test_compute_workshop5_progress():
    assert compute_workshop5_progress([]) == 0
    assert compute_workshop5_progress([_evaluation()]) == 0
    assert compute_workshop5_progress([_evaluation(validated=True)]) == 100


async def _setup_validated_operational(client, base: str, assessment_id: str) -> None:
    stakeholder_id = None
    for record_type, label, props in [
        ("security_scope", "Périmètre", {}),
        ("stakeholder", "RSSI", {"role": "RSSI", "organization": "DSI"}),
        ("security_baseline", "PF", {}),
        ("reference_document", "PSSI", {}),
    ]:
        resp = await client.post(
            f"{base}/assessments/{assessment_id}/records",
            json={"workshop_number": 1, "record_type": record_type, "label": label, "properties": props},
        )
        if record_type == "stakeholder":
            stakeholder_id = resp.json()["id"]

    imported = await client.post(f"{base}/assessments/{assessment_id}/workshop2/import-urbanism-assets")
    records = (await client.get(f"{base}/assessments/{assessment_id}/records")).json()
    asset_id = next(
        r["id"]
        for r in records
        if r["record_type"] == "supporting_asset"
        and r["properties"].get("entity_type") == "serveur"
    )

    await client.post(
        f"{base}/assessments/{assessment_id}/records",
        json={
            "workshop_number": 2,
            "record_type": "risk_source",
            "label": "Cybercriminels ransomware",
            "properties": {
                "target_objective": "Vol de données",
                "feared_event": "Chiffrement des systèmes",
                "severity": "Critique",
                "stakeholder_ids": [stakeholder_id],
                "supporting_asset_ids": [asset_id],
            },
        },
    )

    strategic = await client.post(f"{base}/assessments/{assessment_id}/workshop3/generate-scenarios")
    for s in strategic.json()["records"]:
        props = {**s["properties"], "workflow_status": "Validé"}
        await client.patch(
            f"{base}/assessments/{assessment_id}/records/{s['id']}",
            json={"properties": props},
        )

    operational = await client.post(
        f"{base}/assessments/{assessment_id}/workshop4/generate-operational-scenarios"
    )
    for op in operational.json()["records"]:
        props = {**op["properties"], "workflow_status": "Validé"}
        await client.patch(
            f"{base}/assessments/{assessment_id}/workshop4/scenarios/{op['id']}",
            json={"properties": props, "set_validated": True},
        )


@pytest.mark.asyncio
async def test_workshop5_generate_validate_progress(db_session: AsyncSession):
    project = Project(name="EBIOS W5", organization={})
    db_session.add(project)
    await db_session.flush()
    serveur = UrbanismEntity(
        project_id=project.id,
        entity_type="serveur",
        couche="technique",
        label="Serveur QRadar",
    )
    owner_acteur = UrbanismEntity(
        project_id=project.id,
        entity_type="acteur",
        couche="organisation",
        label="Responsable SI",
    )
    decideur = UrbanismEntity(
        project_id=project.id,
        entity_type="acteur",
        couche="organisation",
        label="Décideur métier",
    )
    organisation = UrbanismEntity(
        project_id=project.id,
        entity_type="organisation",
        couche="organisation",
        label="Direction des Systèmes d'Information",
    )
    db_session.add_all([serveur, owner_acteur, decideur, organisation])
    await db_session.flush()
    db_session.add(
        UrbanismRelation(
            project_id=project.id,
            source_id=serveur.id,
            target_id=owner_acteur.id,
            relation_type="est_exploité_par",
            category="exploitation",
        )
    )
    db_session.add(
        UrbanismRelation(
            project_id=project.id,
            source_id=serveur.id,
            target_id=decideur.id,
            relation_type="décide_pour",
            category="gouvernance",
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
        await _setup_validated_operational(client, base, assessment_id)

        workshops = (await client.get(f"{base}/assessments/{assessment_id}/workshops")).json()
        assert workshops[4]["status"] == "available"

        w5 = await client.get(f"{base}/assessments/{assessment_id}/workshop5")
        assert w5.status_code == 200
        assert w5.json()["validated_operational_count"] == 1
        assert len(w5.json()["urbanism_acteurs"]) >= 2

        generated = await client.post(
            f"{base}/assessments/{assessment_id}/workshop5/generate-treatments"
        )
        assert generated.status_code == 200
        assert generated.json()["generated_count"] == 1
        evaluation = generated.json()["records"][0]
        uid1 = evaluation["properties"]["evaluation_uid"]
        assert evaluation["properties"]["owner_actor"]["label"] == "Responsable SI"
        assert evaluation["properties"]["initial_risk_score"]
        assert evaluation["properties"]["residual_risk_score"]

        w5_data = (await client.get(f"{base}/assessments/{assessment_id}/workshop5")).json()
        assert len(w5_data["evaluations"]) == 1
        assert len(w5_data["evaluations"][0]["measures"]) >= 1
        assert len(w5_data["evaluations"][0]["actions"]) >= 1

        second = await client.post(
            f"{base}/assessments/{assessment_id}/workshop5/generate-treatments"
        )
        assert second.json()["generated_count"] == 0

        validated = await client.patch(
            f"{base}/assessments/{assessment_id}/workshop5/evaluations/{evaluation['id']}",
            json={"set_validated": True},
        )
        assert validated.status_code == 200
        assert validated.json()["properties"]["workflow_status"] == EVAL_VALIDATED

        workshops = (await client.get(f"{base}/assessments/{assessment_id}/workshops")).json()
        assert workshops[4]["progress_percent"] == 100
        assert workshops[4]["status"] == "completed"

        deleted = await client.delete(
            f"{base}/assessments/{assessment_id}/workshop5/evaluations/{evaluation['id']}"
        )
        assert deleted.status_code == 204

        regen = await client.post(
            f"{base}/assessments/{assessment_id}/workshop5/generate-treatments?regenerate=true"
        )
        uid2 = regen.json()["records"][0]["properties"]["evaluation_uid"]
        assert uid2 != uid1

    app.dependency_overrides.clear()
