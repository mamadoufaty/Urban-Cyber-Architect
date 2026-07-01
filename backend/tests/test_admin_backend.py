"""Tests — socle backend Administration V1.0."""

from __future__ import annotations

import asyncio
import json

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.main import app as fastapi_app
import app.models.admin  # noqa: F401
import app.models.entities  # noqa: F401
from app.models.admin import Organization, Permission, Role, User
from app.schemas.admin import OrganizationCreate, UserCreate
from app.services.admin.audit_service import list_audit_logs, log_action
from app.services.admin.role_service import assign_permissions
from app.services.admin.seed_service import run_admin_seed, verify_seed_password
from app.services.admin.user_service import disable_user, enable_user, list_users, reset_password
from app.services.password_service import hash_password, verify_password


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
async def test_seed_idempotent(db_session: AsyncSession):
    await run_admin_seed(db_session)
    await db_session.commit()

    org_count = await db_session.scalar(select(func.count()).select_from(Organization))
    role_count = await db_session.scalar(select(func.count()).select_from(Role))
    perm_count = await db_session.scalar(select(func.count()).select_from(Permission))
    user_count = await db_session.scalar(select(func.count()).select_from(User))

    assert org_count == 1
    assert role_count == 5
    assert perm_count == 17
    assert user_count == 5

    await run_admin_seed(db_session)
    await db_session.commit()

    assert await db_session.scalar(select(func.count()).select_from(Organization)) == 1
    assert await db_session.scalar(select(func.count()).select_from(Role)) == 5
    assert await db_session.scalar(select(func.count()).select_from(User)) == 5


@pytest.mark.asyncio
async def test_system_roles_created(db_session: AsyncSession):
    await run_admin_seed(db_session)
    await db_session.commit()
    result = await db_session.execute(select(Role).where(Role.is_system.is_(True)))
    codes = {r.code for r in result.scalars().all()}
    assert codes == {"admin", "rssi", "consultant", "soc", "metier"}


@pytest.mark.asyncio
async def test_permissions_created(db_session: AsyncSession):
    await run_admin_seed(db_session)
    await db_session.commit()
    result = await db_session.execute(select(Permission))
    codes = {p.code for p in result.scalars().all()}
    assert "dashboard:read" in codes
    assert "administration:write" in codes
    assert "deliverables:generate" in codes


@pytest.mark.asyncio
async def test_initial_users_passwords_hashed(db_session: AsyncSession):
    await run_admin_seed(db_session)
    await db_session.commit()
    result = await db_session.execute(select(User))
    users = list(result.scalars().all())
    assert len(users) == 5
    for user in users:
        assert user.password_hash != "Admin@123"
        assert user.password_hash.startswith("$2")
    assert await verify_seed_password("admin", "Admin@123", db_session)


@pytest.mark.asyncio
async def test_list_users_hides_password_hash(db_session: AsyncSession):
    await run_admin_seed(db_session)
    await db_session.commit()
    items, total = await list_users(db_session)
    assert total == 5
    payload = json.loads(json.dumps([i.model_dump(mode="json") for i in items], default=str))
    for item in payload:
        assert "password_hash" not in item


@pytest.mark.asyncio
async def test_disable_enable_user(db_session: AsyncSession):
    await run_admin_seed(db_session)
    await db_session.commit()
    result = await db_session.execute(select(User).where(User.username == "consultant"))
    user = result.scalar_one()
    disabled = await disable_user(db_session, user.id)
    assert disabled.status == "disabled"
    enabled = await enable_user(db_session, user.id)
    assert enabled.status == "active"


@pytest.mark.asyncio
async def test_reset_password(db_session: AsyncSession):
    await run_admin_seed(db_session)
    await db_session.commit()
    result = await db_session.execute(select(User).where(User.username == "soc"))
    user = result.scalar_one()
    old_hash = user.password_hash
    await reset_password(db_session, user.id, "NewSoc@456")
    await db_session.commit()
    refreshed = await db_session.get(User, user.id)
    assert refreshed.password_hash != old_hash
    assert verify_password("NewSoc@456", refreshed.password_hash)


@pytest.mark.asyncio
async def test_create_organization(db_session: AsyncSession):
    from app.services.admin.organization_service import create_organization

    org = await create_organization(
        db_session,
        OrganizationCreate(name="Acme Corp", code="acme", description="Test"),
    )
    await db_session.commit()
    assert org.code == "acme"
    assert org.status == "active"


@pytest.mark.asyncio
async def test_assign_permissions_to_role(db_session: AsyncSession):
    await run_admin_seed(db_session)
    await db_session.commit()
    role_result = await db_session.execute(select(Role).where(Role.code == "metier"))
    role = role_result.scalar_one()
    perm_result = await db_session.execute(
        select(Permission).where(Permission.code == "urbanism:write")
    )
    perm = perm_result.scalar_one()
    updated = await assign_permissions(db_session, role.id, [perm.id])
    await db_session.commit()
    codes = {p.code for p in updated.permissions}
    assert "urbanism:write" in codes


@pytest.mark.asyncio
async def test_audit_log_action(db_session: AsyncSession):
    await run_admin_seed(db_session)
    await db_session.commit()
    user_result = await db_session.execute(select(User).where(User.username == "admin"))
    admin_user = user_result.scalar_one()
    await log_action(
        db_session,
        user_id=admin_user.id,
        action="test.action",
        object_type="user",
        object_id=str(admin_user.id),
        details={"note": "test"},
    )
    await db_session.commit()
    logs, total = await list_audit_logs(db_session)
    assert total >= 1
    assert logs[0].action == "test.action"
    assert logs[0].username == "admin"


@pytest.mark.asyncio
async def test_admin_api_users(db_session: AsyncSession):
    await run_admin_seed(db_session)
    await db_session.commit()

    async def override_get_db():
        yield db_session

    fastapi_app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=fastapi_app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        listing = await client.get("/api/admin/users")
        assert listing.status_code == 200
        body = listing.json()
        assert body["total"] == 5
        assert "password_hash" not in listing.text

        user_id = body["items"][0]["id"]
        disabled = await client.patch(f"/api/admin/users/{user_id}/disable")
        assert disabled.status_code == 200
        assert disabled.json()["status"] == "disabled"

        enabled = await client.patch(f"/api/admin/users/{user_id}/enable")
        assert enabled.status_code == 200
        assert enabled.json()["status"] == "active"

        reset = await client.patch(
            f"/api/admin/users/{user_id}/reset-password",
            json={"password": "Reset@999"},
        )
        assert reset.status_code == 200

        orgs = await client.get("/api/admin/organizations")
        assert orgs.status_code == 200
        assert orgs.json()["total"] >= 1

        roles = await client.get("/api/admin/roles")
        assert roles.status_code == 200
        assert roles.json()["total"] == 5

        perms = await client.get("/api/admin/permissions")
        assert perms.status_code == 200
        assert perms.json()["total"] == 17

        audit = await client.get("/api/admin/audit-logs")
        assert audit.status_code == 200

        created = await client.post(
            "/api/admin/users",
            json={
                "username": "newuser",
                "password": "NewUser@123",
                "role_id": roles.json()["items"][0]["id"],
            },
        )
        assert created.status_code == 201
        assert created.json()["username"] == "newuser"

    fastapi_app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_password_service_roundtrip():
    hashed = hash_password("Test@123")
    assert verify_password("Test@123", hashed)
    assert not verify_password("wrong", hashed)
