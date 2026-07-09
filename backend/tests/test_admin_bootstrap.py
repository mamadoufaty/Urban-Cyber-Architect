"""Tests — protection dernier administrateur et bootstrap."""

from __future__ import annotations

import asyncio

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.main import app as fastapi_app
import app.models.admin  # noqa: F401
import app.models.entities  # noqa: F401
from app.models.admin import AuditLog, Role, User
from app.services.admin.admin_guard import LAST_ADMIN_MESSAGE, LastAdministratorError
from app.services.admin.bootstrap_admin_service import bootstrap_admin_cli, bootstrap_admin_recovery
from app.services.admin.seed_service import run_admin_seed
from app.services.admin.user_service import delete_user
from app.services.password_service import verify_password


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


async def _admin_users(session: AsyncSession) -> list[User]:
    result = await session.execute(
        select(User).join(Role, User.role_id == Role.id).where(Role.code.in_(("admin", "superadmin")))
    )
    return list(result.scalars().all())


@pytest.mark.asyncio
async def test_delete_last_administrator_refused(db_session: AsyncSession):
    for user in await _admin_users(db_session):
        if user.username != "admin":
            await delete_user(db_session, user.id)
    await db_session.commit()

    admin_result = await db_session.execute(select(User).where(User.username == "admin"))
    admin_user = admin_result.scalar_one()

    with pytest.raises(LastAdministratorError, match=LAST_ADMIN_MESSAGE):
        await delete_user(db_session, admin_user.id)


@pytest.mark.asyncio
async def test_delete_admin_allowed_when_another_exists(db_session: AsyncSession):
    admin1 = await db_session.execute(select(User).where(User.username == "admin1"))
    user = admin1.scalar_one()
    await delete_user(db_session, user.id)
    await db_session.commit()

    remaining = await _admin_users(db_session)
    assert any(u.username == "admin" for u in remaining)
    assert not any(u.username == "admin1" for u in remaining)


@pytest.mark.asyncio
async def test_bootstrap_recovery_creates_first_admin(db_session: AsyncSession, monkeypatch):
    result = await db_session.execute(select(User))
    for user in result.scalars().all():
        await db_session.delete(user)
    await db_session.commit()

    monkeypatch.setattr("app.services.admin.bootstrap_admin_service.settings.enable_bootstrap_admin", True)
    monkeypatch.setattr("app.services.admin.bootstrap_admin_service.bootstrap_enabled", lambda: True)

    outcome = await bootstrap_admin_recovery(
        db_session,
        username="recovery_admin",
        password="Recovery@123",
        first_name="Recovery",
        last_name="Admin",
        email="recovery@example.com",
        ip_address="127.0.0.1",
        user_agent="pytest",
    )
    assert outcome["action"] == "created"
    assert outcome["username"] == "recovery_admin"

    user_result = await db_session.execute(select(User).where(User.username == "recovery_admin"))
    user = user_result.scalar_one()
    assert verify_password("Recovery@123", user.password_hash)

    audit = await db_session.execute(
        select(AuditLog).where(AuditLog.action == "admin.bootstrap")
    )
    entry = audit.scalars().first()
    assert entry is not None
    assert entry.result == "created"
    assert entry.ip_address == "127.0.0.1"


@pytest.mark.asyncio
async def test_bootstrap_cli_resets_password(db_session: AsyncSession):
    outcome = await bootstrap_admin_cli(
        db_session,
        username="admin",
        password="NewAdmin@456",
        reset=True,
    )
    assert outcome["action"] == "password_reset"

    user_result = await db_session.execute(select(User).where(User.username == "admin"))
    user = user_result.scalar_one()
    assert verify_password("NewAdmin@456", user.password_hash)

    audit = await db_session.execute(select(AuditLog).where(AuditLog.action == "admin.bootstrap"))
    assert audit.scalars().first() is not None


@pytest.mark.asyncio
async def test_api_delete_last_admin_returns_409(db_session: AsyncSession):
    for user in await _admin_users(db_session):
        if user.username != "admin":
            await delete_user(db_session, user.id)
    await db_session.commit()

    admin_result = await db_session.execute(select(User).where(User.username == "admin"))
    admin_user = admin_result.scalar_one()

    async def override_get_db():
        yield db_session

    fastapi_app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=fastapi_app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.delete(f"/api/admin/users/{admin_user.id}")
        assert response.status_code == 409
        assert response.json()["detail"] == LAST_ADMIN_MESSAGE

    fastapi_app.dependency_overrides.clear()
