"""Tests — suppression projet et dépendances."""

from __future__ import annotations

import asyncio

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.main import app as fastapi_app
from app.models.deliverables import Deliverable
from app.models.entities import Project, UrbanismEntity
import app.models.ebios  # noqa: F401
import app.models.deliverables  # noqa: F401


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
async def test_delete_empty_project_returns_204(db_session: AsyncSession):
    project = Project(name="Projet vide")
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    async def override_get_db():
        yield db_session

    fastapi_app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=fastapi_app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.delete(f"/api/projects/{project.id}")
        assert response.status_code == 204

    fastapi_app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_delete_project_with_dependencies_returns_409(db_session: AsyncSession):
    project = Project(name="Projet avec données")
    db_session.add(project)
    await db_session.flush()
    db_session.add(
        UrbanismEntity(
            project_id=project.id,
            entity_type="acteur",
            couche="organisation",
            label="RSSI",
        )
    )
    db_session.add(
        Deliverable(
            project_id=project.id,
            title="Plan test",
            deliverable_type="project_management_plan",
            user_need="Test",
        )
    )
    await db_session.commit()
    await db_session.refresh(project)

    async def override_get_db():
        yield db_session

    fastapi_app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=fastapi_app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.delete(f"/api/projects/{project.id}")
        assert response.status_code == 409
        body = response.json()
        assert "données liées" in body["detail"]
        assert isinstance(body["dependencies"], list)
        names = {d["name"] for d in body["dependencies"]}
        assert "Urbanisme" in names
        assert "Livrables" in names
        assert all(d["count"] > 0 for d in body["dependencies"])

        still = await client.get(f"/api/projects/{project.id}")
        assert still.status_code == 200

    fastapi_app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_delete_conflict_response_lists_dependencies(db_session: AsyncSession):
    project = Project(name="Projet urbanisme")
    db_session.add(project)
    await db_session.flush()
    for i in range(3):
        db_session.add(
            UrbanismEntity(
                project_id=project.id,
                entity_type="processus",
                couche="metier",
                label=f"Processus {i}",
            )
        )
    await db_session.commit()
    await db_session.refresh(project)

    async def override_get_db():
        yield db_session

    fastapi_app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=fastapi_app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.delete(f"/api/projects/{project.id}")
        assert response.status_code == 409
        urbanism = next(d for d in response.json()["dependencies"] if d["name"] == "Urbanisme")
        assert urbanism["count"] == 3

    fastapi_app.dependency_overrides.clear()
