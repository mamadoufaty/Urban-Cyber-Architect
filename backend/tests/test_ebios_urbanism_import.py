"""Tests synchronisation Urbanisme → biens supports EBIOS (idempotence)."""

import asyncio

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.main import app
from app.models.ebios import EbiosRecord
from app.models.entities import Project, UrbanismEntity
from app.services.ebios.urbanism_import import import_urbanism_supporting_assets


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


@pytest.mark.asyncio
async def test_urbanism_import_is_idempotent(db_session: AsyncSession):
    project = Project(name="Sync test", organization={})
    db_session.add(project)
    await db_session.flush()
    entity = UrbanismEntity(
        project_id=project.id,
        entity_type="ilot_applicatif",
        couche="applicatif",
        label="CRM",
    )
    db_session.add(entity)
    await db_session.commit()
    await db_session.refresh(project)

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    base = f"/api/projects/{project.id}/ebios"

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        assessment_id = (await client.get(f"{base}/assessment")).json()["id"]
        endpoint = f"{base}/assessments/{assessment_id}/workshop2/import-urbanism-assets"

        first = await client.post(endpoint)
        second = await client.post(endpoint)
        third = await client.post(endpoint)

        assert first.status_code == 200
        assert first.json()["imported_count"] == 1
        assert second.json()["imported_count"] == 0
        assert third.json()["imported_count"] == 0

        records = (
            await client.get(f"{base}/assessments/{assessment_id}/records?workshop_number=2")
        ).json()
        assets = [r for r in records if r["record_type"] == "supporting_asset"]
        assert len(assets) == 1
        assert assets[0]["properties"]["urbanism_entity_id"] == str(entity.id)

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_urbanism_import_deduplicates_existing_duplicates(db_session: AsyncSession):
    project = Project(name="Dedup test", organization={})
    db_session.add(project)
    await db_session.flush()
    entity = UrbanismEntity(
        project_id=project.id,
        entity_type="serveur",
        couche="technique",
        label="Serveur A",
    )
    db_session.add(entity)
    await db_session.flush()

    from app.models.ebios import EbiosAssessment

    assessment = EbiosAssessment(project_id=project.id)
    db_session.add(assessment)
    await db_session.flush()

    uid = str(entity.id)
    for label in ("Serveur A copy 1", "Serveur A copy 2"):
        db_session.add(
            EbiosRecord(
                assessment_id=assessment.id,
                workshop_number=2,
                record_type="supporting_asset",
                label=label,
                properties={"urbanism_entity_id": uid, "import_source": "urbanism"},
                status="imported",
            )
        )
    await db_session.commit()

    _, created = await import_urbanism_supporting_assets(db_session, assessment.id, project.id)
    assert created == 0

    result = await db_session.execute(
        select(func.count())
        .select_from(EbiosRecord)
        .where(
            EbiosRecord.assessment_id == assessment.id,
            EbiosRecord.record_type == "supporting_asset",
        )
    )
    assert result.scalar_one() == 1

    record = (
        await db_session.execute(
            select(EbiosRecord).where(
                EbiosRecord.assessment_id == assessment.id,
                EbiosRecord.record_type == "supporting_asset",
            )
        )
    ).scalar_one()
    assert record.label == "Serveur A"
