"""Tests — authentification backend."""

from __future__ import annotations

import asyncio

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.main import app as fastapi_app
from app.models.admin import User
import app.models.admin  # noqa: F401
from app.services.admin.seed_service import run_admin_seed
from app.services.admin.user_service import disable_user


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
async def test_login_success_for_seed_admin(db_session: AsyncSession):
    async def override_get_db():
        yield db_session

    fastapi_app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=fastapi_app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "Admin@123"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["user"]["username"] == "admin"
        assert body["user"]["role"] == "superadmin"
        assert body["user"]["displayName"]
        assert "password_hash" not in response.text

    result = await db_session.execute(select(User).where(User.username == "admin"))
    admin_user = result.scalar_one()
    assert admin_user.last_login_at is not None

    fastapi_app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_login_success_for_demo(db_session: AsyncSession):
    async def override_get_db():
        yield db_session

    fastapi_app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=fastapi_app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/auth/login",
            json={"username": "demo", "password": "Demo@123"},
        )
        assert response.status_code == 200
        assert response.json()["user"]["role"] == "consultant"

    fastapi_app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_login_invalid_credentials(db_session: AsyncSession):
    async def override_get_db():
        yield db_session

    fastapi_app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=fastapi_app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "wrong"},
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Identifiants invalides."

    fastapi_app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_login_rejects_disabled_user(db_session: AsyncSession):
    result = await db_session.execute(select(User).where(User.username == "demo"))
    user = result.scalar_one()
    await disable_user(db_session, user.id)
    await db_session.commit()

    async def override_get_db():
        yield db_session

    fastapi_app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=fastapi_app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/auth/login",
            json={"username": "demo", "password": "Demo@123"},
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Identifiants invalides."

    fastapi_app.dependency_overrides.clear()
