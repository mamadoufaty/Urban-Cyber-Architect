"""Tests Atelier 1 EBIOS RM — cadrage, progression et déverrouillage."""

import asyncio
import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.main import app
from app.models.entities import Project
from app.services.ebios.workshop1_service import compute_workshop1_progress


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


def _record(record_type: str, label: str = "Test"):
    class R:
        pass

    r = R()
    r.record_type = record_type
    r.label = label
    return r


def test_compute_workshop1_progress_empty():
    assert compute_workshop1_progress([]) == 0


def test_compute_workshop1_progress_full():
    records = [
        _record("security_scope", "Périmètre SI"),
        _record("stakeholder"),
        _record("security_baseline"),
        _record("reference_document"),
    ]
    assert compute_workshop1_progress(records) == 100


def test_compute_workshop1_progress_partial():
    records = [_record("stakeholder"), _record("security_baseline")]
    assert compute_workshop1_progress(records) == 50


@pytest.mark.asyncio
async def test_workshop1_records_and_unlock(db_session: AsyncSession):
    project = Project(name="EBIOS W1", organization={})
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    base = f"/api/projects/{project.id}/ebios"

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        assessment = (await client.get(f"{base}/assessment")).json()
        assessment_id = assessment["id"]

        workshops = (
            await client.get(f"{base}/assessments/{assessment_id}/workshops")
        ).json()
        assert workshops[0]["progress_percent"] == 0
        assert workshops[0]["status"] == "available"
        assert workshops[1]["status"] == "locked"

        async def create_record(record_type: str, label: str, properties: dict | None = None):
            payload = {
                "workshop_number": 1,
                "record_type": record_type,
                "label": label,
                "properties": properties or {},
            }
            return await client.post(f"{base}/assessments/{assessment_id}/records", json=payload)

        r_scope = await create_record(
            "security_scope",
            "Périmètre principal",
            {"business_objectives": "Continuité", "activities": "Support"},
        )
        assert r_scope.status_code == 201

        r_stake = await create_record(
            "stakeholder",
            "Jean Dupont",
            {"role": "RSSI", "organization": "DSI", "involvement_level": "Élevé"},
        )
        assert r_stake.status_code == 201

        r_baseline = await create_record(
            "security_baseline",
            "Pare-feu périmétrique",
            {"domain": "Réseau", "status": "En place", "maturity_level": "3"},
        )
        assert r_baseline.status_code == 201

        workshops = (
            await client.get(f"{base}/assessments/{assessment_id}/workshops")
        ).json()
        assert workshops[0]["progress_percent"] == 75
        assert workshops[0]["status"] == "in_progress"
        assert workshops[1]["status"] == "locked"

        r_doc = await create_record(
            "reference_document",
            "PSSI 2024",
            {"doc_type": "PSSI", "version": "2.1", "owner": "RSSI"},
        )
        assert r_doc.status_code == 201

        workshops = (
            await client.get(f"{base}/assessments/{assessment_id}/workshops")
        ).json()
        assert workshops[0]["progress_percent"] == 100
        assert workshops[0]["status"] == "completed"
        assert workshops[1]["status"] == "available"

        overview = (
            await client.get(f"{base}/assessments/{assessment_id}/overview")
        ).json()
        assert overview["overall_progress_percent"] == 20

        record_id = r_stake.json()["id"]
        deleted = await client.delete(
            f"{base}/assessments/{assessment_id}/records/{record_id}"
        )
        assert deleted.status_code == 204

        workshops = (
            await client.get(f"{base}/assessments/{assessment_id}/workshops")
        ).json()
        assert workshops[0]["progress_percent"] == 75
        assert workshops[0]["status"] == "in_progress"
        assert workshops[1]["status"] == "locked"

    app.dependency_overrides.clear()
