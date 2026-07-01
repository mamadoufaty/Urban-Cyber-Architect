"""Tests Atelier 2 EBIOS RM — sources de risque, import urbanisme et progression."""

import asyncio

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.main import app
from app.models.entities import Project, UrbanismEntity
from app.services.ebios.workshop2_service import compute_workshop2_progress, is_risk_source_complete


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


def _risk_source(label="Source", complete=True):
    class R:
        pass

    r = R()
    r.record_type = "risk_source"
    r.label = label
    props = {
        "target_objective": "Objectif" if complete else "",
        "feared_event": "Événement" if complete else "",
        "severity": "Élevée" if complete else "",
        "stakeholder_ids": ["s1"] if complete else [],
        "supporting_asset_ids": ["a1"] if complete else [],
    }
    r.properties = props
    return r


def test_is_risk_source_complete():
    assert is_risk_source_complete(_risk_source()) is True
    assert is_risk_source_complete(_risk_source(complete=False)) is False


def test_compute_workshop2_progress():
    assert compute_workshop2_progress([]) == 0
    assert compute_workshop2_progress([_risk_source()]) == 25
    assert compute_workshop2_progress([_risk_source(), _risk_source("S2")]) == 50
    sources = [_risk_source(f"S{i}") for i in range(5)]
    assert compute_workshop2_progress(sources) == 100


async def _complete_workshop1(client, base: str, assessment_id: str) -> str:
    """Complète l'atelier 1 et retourne l'id d'une partie prenante."""
    stakeholder_id = None
    payloads = [
        ("security_scope", "Périmètre", {"business_objectives": "Continuité"}),
        ("stakeholder", "RSSI Test", {"role": "RSSI"}),
        ("security_baseline", "Pare-feu", {"status": "En place"}),
        ("reference_document", "PSSI", {"doc_type": "PSSI"}),
    ]
    for record_type, label, props in payloads:
        resp = await client.post(
            f"{base}/assessments/{assessment_id}/records",
            json={"workshop_number": 1, "record_type": record_type, "label": label, "properties": props},
        )
        assert resp.status_code == 201
        if record_type == "stakeholder":
            stakeholder_id = resp.json()["id"]
    return stakeholder_id


@pytest.mark.asyncio
async def test_workshop2_risk_sources_and_unlock(db_session: AsyncSession):
    project = Project(name="EBIOS W2", organization={})
    db_session.add(project)
    await db_session.flush()
    db_session.add(
        UrbanismEntity(
            project_id=project.id,
            entity_type="ilot_applicatif",
            couche="applicatif",
            label="CRM",
        )
    )
    db_session.add(
        UrbanismEntity(
            project_id=project.id,
            entity_type="serveur",
            couche="technique",
            label="Serveur prod",
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
        stakeholder_id = await _complete_workshop1(client, base, assessment_id)

        workshops = (await client.get(f"{base}/assessments/{assessment_id}/workshops")).json()
        assert workshops[1]["status"] == "available"
        assert workshops[2]["status"] == "locked"

        imported = await client.post(
            f"{base}/assessments/{assessment_id}/workshop2/import-urbanism-assets"
        )
        assert imported.status_code == 200
        assert imported.json()["imported_count"] == 2
        asset_id = imported.json()["records"][0]["id"]

        risk_props = {
            "target_objective": "Vol de données clients",
            "feared_event": "Fuite de données personnelles",
            "severity": "Critique",
            "stakeholder_ids": [stakeholder_id],
            "supporting_asset_ids": [asset_id],
            "comment": "Source externe",
        }
        created = await client.post(
            f"{base}/assessments/{assessment_id}/records",
            json={
                "workshop_number": 2,
                "record_type": "risk_source",
                "label": "Cybercriminels",
                "properties": risk_props,
            },
        )
        assert created.status_code == 201
        risk_id = created.json()["id"]

        records = (await client.get(f"{base}/assessments/{assessment_id}/records?workshop_number=2")).json()
        feared_events = [r for r in records if r["record_type"] == "feared_event"]
        assert len(feared_events) == 1
        assert feared_events[0]["properties"]["risk_source_id"] == risk_id

        workshops = (await client.get(f"{base}/assessments/{assessment_id}/workshops")).json()
        assert workshops[1]["progress_percent"] == 25
        assert workshops[1]["status"] == "in_progress"
        assert workshops[2]["status"] == "locked"

        for i in range(3):
            await client.post(
                f"{base}/assessments/{assessment_id}/records",
                json={
                    "workshop_number": 2,
                    "record_type": "risk_source",
                    "label": f"Source {i + 2}",
                    "properties": risk_props,
                },
            )

        workshops = (await client.get(f"{base}/assessments/{assessment_id}/workshops")).json()
        assert workshops[1]["progress_percent"] == 100
        assert workshops[1]["status"] == "completed"
        assert workshops[2]["status"] == "available"

        deleted = await client.delete(f"{base}/assessments/{assessment_id}/records/{risk_id}")
        assert deleted.status_code == 204

        records = (await client.get(f"{base}/assessments/{assessment_id}/records?workshop_number=2")).json()
        assert not any(r["record_type"] == "feared_event" and r["properties"].get("risk_source_id") == risk_id for r in records)

    app.dependency_overrides.clear()
