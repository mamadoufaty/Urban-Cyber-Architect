"""Tests persistance placement manuel des entités."""

import asyncio
import uuid

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base
from app.models.entities import Project, UrbanismEntity
from app.services.urbanism_entity_layout import (
    clear_entity_layout,
    get_entity_layout,
    save_entity_layout,
    save_entity_layouts_bulk,
)


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
async def test_save_and_clear_entity_layout(db_session: AsyncSession):
    project = Project(name="Entity layout test", organization={})
    db_session.add(project)
    await db_session.flush()

    entity = UrbanismEntity(
        project_id=project.id,
        entity_type="metier",
        couche="metier",
        label="Métier",
    )
    db_session.add(entity)
    await db_session.commit()
    await db_session.refresh(entity)

    saved = await save_entity_layout(db_session, project.id, entity.id, {"x": 123.0, "y": 456.0})
    assert saved["mode"] == "manual"
    assert saved["locked"] is True
    assert saved["x"] == 123.0
    assert saved["y"] == 456.0

    await db_session.refresh(entity)
    stored = get_entity_layout(entity.properties)
    assert stored is not None
    assert stored["y"] == 456.0

    await clear_entity_layout(db_session, project.id, entity.id)
    await db_session.refresh(entity)
    assert get_entity_layout(entity.properties) is None


@pytest.mark.asyncio
async def test_save_entity_layouts_bulk(db_session: AsyncSession):
    project = Project(name="Bulk layout test", organization={})
    db_session.add(project)
    await db_session.flush()

    e1 = UrbanismEntity(project_id=project.id, entity_type="metier", couche="metier", label="A")
    e2 = UrbanismEntity(project_id=project.id, entity_type="organisation", couche="organisation", label="B")
    db_session.add_all([e1, e2])
    await db_session.commit()
    await db_session.refresh(e1)
    await db_session.refresh(e2)

    result = await save_entity_layouts_bulk(
        db_session,
        project.id,
        [
            {"entity_id": e1.id, "layout": {"x": 10.0, "y": 20.0}},
            {"entity_id": e2.id, "layout": {"x": 30.0, "y": 40.0}},
        ],
    )
    assert len(result) == 2
    assert result[0]["layout"]["x"] == 10.0

    await db_session.refresh(e2)
    assert get_entity_layout(e2.properties)["y"] == 40.0
