"""Tests — organisations Administration."""

from __future__ import annotations

import asyncio
import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.main import app as fastapi_app
from app.models.admin import Organization
from app.schemas.admin import OrganizationCreate
import app.models.admin  # noqa: F401
import app.models.entities  # noqa: F401
from app.services.admin.organization_service import create_organization
from app.services.admin.seed_service import run_admin_seed


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
        await run_admin_seed(session)
        await session.commit()
        yield session
    await engine.dispose()


@pytest.mark.asyncio
async def test_delete_organization_without_dependencies(db_session: AsyncSession):
    org = await create_organization(
        db_session,
        OrganizationCreate(name="Acme", code=f"acme-{uuid.uuid4().hex[:8]}", description="Test"),
    )
    await db_session.commit()

    async def override_get_db():
        yield db_session

    fastapi_app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=fastapi_app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.delete(f"/api/admin/organizations/{org.id}")
        assert response.status_code == 204

    fastapi_app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_activate_and_deactivate_organization(db_session: AsyncSession):
    org = await create_organization(
        db_session,
        OrganizationCreate(name="Beta Corp", code=f"beta-{uuid.uuid4().hex[:8]}"),
    )
    await db_session.commit()

    async def override_get_db():
        yield db_session

    fastapi_app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=fastapi_app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        deactivated = await client.patch(f"/api/admin/organizations/{org.id}/deactivate")
        assert deactivated.status_code == 200
        assert deactivated.json()["status"] == "archived"

        activated = await client.patch(f"/api/admin/organizations/{org.id}/activate")
        assert activated.status_code == 200
        assert activated.json()["status"] == "active"

    fastapi_app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_delete_organization_with_users_returns_400(db_session: AsyncSession):
    from sqlalchemy import func, select

    from app.models.admin import User

    result = await db_session.execute(select(Organization).where(Organization.code == "metropolis-test"))
    org = result.scalar_one()
    assert (
        await db_session.scalar(
            select(func.count()).select_from(User).where(User.organization_id == org.id)
        )
    ) > 0

    async def override_get_db():
        yield db_session

    fastapi_app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=fastapi_app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.delete(f"/api/admin/organizations/{org.id}")
        assert response.status_code == 400
        assert "utilisateurs" in response.json()["detail"].lower()

    fastapi_app.dependency_overrides.clear()
