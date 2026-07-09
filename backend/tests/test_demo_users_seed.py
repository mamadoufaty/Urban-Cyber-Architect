"""Tests — seed des utilisateurs de démonstration."""

from __future__ import annotations

import asyncio

import pytest
import pytest_asyncio
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base
import app.models.admin  # noqa: F401
import app.models.entities  # noqa: F401
from app.models.admin import Role, User
from app.services.admin.seed_service import DEMO_USERS, run_admin_seed, verify_seed_password
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
        yield session
    await engine.dispose()


@pytest.mark.asyncio
async def test_demo_users_created_once(db_session: AsyncSession):
    await run_admin_seed(db_session)
    await db_session.commit()

    usernames = {u[0] for u in DEMO_USERS}
    result = await db_session.execute(select(User.username))
    assert set(result.scalars().all()) == usernames
    assert await db_session.scalar(select(func.count()).select_from(User)) == len(DEMO_USERS)


@pytest.mark.asyncio
async def test_demo_users_seed_idempotent_by_username(db_session: AsyncSession):
    await run_admin_seed(db_session)
    await db_session.commit()
    await run_admin_seed(db_session)
    await db_session.commit()

    assert await db_session.scalar(select(func.count()).select_from(User)) == len(DEMO_USERS)


@pytest.mark.asyncio
async def test_demo_users_do_not_overwrite_existing_login(db_session: AsyncSession):
    await run_admin_seed(db_session)
    await db_session.commit()

    result = await db_session.execute(select(User).where(User.username == "admin"))
    admin_user = result.scalar_one()
    admin_user.password_hash = "custom-hash"
    await db_session.commit()

    await run_admin_seed(db_session)
    await db_session.commit()

    refreshed = await db_session.get(User, admin_user.id)
    assert refreshed.password_hash == "custom-hash"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "username,password,role_code",
    [
        ("admin", "Admin@123", "superadmin"),
        ("admin1", "Admin1@123", "admin"),
        ("admin2", "Admin2@123", "admin"),
        ("admin3", "Admin3@123", "admin"),
        ("demo", "Demo@123", "consultant"),
    ],
)
async def test_demo_users_passwords_and_roles(
    db_session: AsyncSession, username: str, password: str, role_code: str
):
    await run_admin_seed(db_session)
    await db_session.commit()

    result = await db_session.execute(select(User).where(User.username == username))
    user = result.scalar_one()
    role = await db_session.get(Role, user.role_id)
    assert role is not None
    assert role.code == role_code
    assert user.password_hash.startswith("$2")
    assert verify_password(password, user.password_hash)
    assert await verify_seed_password(username, password, db_session)
