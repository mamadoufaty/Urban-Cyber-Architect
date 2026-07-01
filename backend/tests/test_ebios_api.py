"""Tests API squelette — module EBIOS RM."""

import asyncio
import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.main import app
from app.models.entities import Project


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
async def test_ebios_metamodel_and_assessment(db_session: AsyncSession):
    project = Project(name="EBIOS test", organization={})
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        meta = await client.get("/api/metamodel/ebios")
        assert meta.status_code == 200
        assert len(meta.json()["workshops"]) == 5

        assessment = await client.get(f"/api/projects/{project.id}/ebios/assessment")
        assert assessment.status_code == 200
        body = assessment.json()
        assert body["current_workshop"] == 1

        workshops = await client.get(
            f"/api/projects/{project.id}/ebios/assessments/{body['id']}/workshops"
        )
        assert workshops.status_code == 200
        assert len(workshops.json()) == 5
        assert workshops.json()[0]["code"] == "framing"

    app.dependency_overrides.clear()
