"""Tests persistance tracé manuel des relations."""

import asyncio
import uuid

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base
from app.models.entities import Project, UrbanismEntity, UrbanismRelation
from app.services.urbanism_edge_layout import clear_edge_layout, get_relation_layout, save_edge_layout


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
async def test_save_and_clear_relation_layout(db_session: AsyncSession):
    project = Project(name="Layout test", organization={})
    db_session.add(project)
    await db_session.flush()

    src = UrbanismEntity(
        project_id=project.id,
        entity_type="metier",
        couche="metier",
        label="Métier",
    )
    tgt = UrbanismEntity(
        project_id=project.id,
        entity_type="organisation",
        couche="organisation",
        label="DSI",
    )
    db_session.add_all([src, tgt])
    await db_session.flush()

    rel = UrbanismRelation(
        project_id=project.id,
        source_id=src.id,
        target_id=tgt.id,
        relation_type="décide de",
        category="metier",
    )
    db_session.add(rel)
    await db_session.commit()
    await db_session.refresh(rel)

    layout = {
        "mode": "manual",
        "locked": True,
        "pathType": "custom",
        "waypoints": [{"x": 120.0, "y": 240.0}],
        "sourceHandle": "source-left",
        "targetHandle": "target-right",
    }
    saved = await save_edge_layout(db_session, project.id, str(rel.id), layout)
    assert saved["locked"] is True
    assert saved["waypoints"][0]["x"] == 120.0

    await db_session.refresh(rel)
    stored = get_relation_layout(rel.properties)
    assert stored is not None
    assert stored["waypoints"][0]["y"] == 240.0

    await clear_edge_layout(db_session, project.id, str(rel.id))
    await db_session.refresh(rel)
    assert get_relation_layout(rel.properties) is None
