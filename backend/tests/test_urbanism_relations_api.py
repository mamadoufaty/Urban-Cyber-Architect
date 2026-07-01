"""Régression : relations avec properties NULL ne doivent pas provoquer de 500."""

import asyncio
import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.main import app
from app.models.entities import Project, UrbanismEntity, UrbanismRelation


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
async def test_list_relations_accepts_null_properties(db_session: AsyncSession):
    project = Project(name="Rel props test", organization={})
    db_session.add(project)
    await db_session.flush()

    src = UrbanismEntity(project_id=project.id, entity_type="metier", couche="metier", label="M")
    tgt = UrbanismEntity(project_id=project.id, entity_type="objectif", couche="metier", label="O")
    db_session.add_all([src, tgt])
    await db_session.flush()

    rel = UrbanismRelation(
        project_id=project.id,
        source_id=src.id,
        target_id=tgt.id,
        relation_type="définit",
        category="metier",
        properties=None,
    )
    db_session.add(rel)
    await db_session.commit()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/api/projects/{project.id}/urbanism/relations")
    app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["properties"] == {}
