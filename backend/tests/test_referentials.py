"""Tests — référentiels administrables + organisation dans la réponse de login."""

from __future__ import annotations

import asyncio

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import app.models  # noqa: F401 — enregistre tous les modèles
from app.database import get_db
from app.main import app as fastapi_app
from app.models import Base
from app.models.admin import User
from app.models.referentials import ReferentialFramework
from app.services.admin import referential_service
from app.services.admin.seed_service import run_admin_seed
from app.services.auth_service import login


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
async def test_seed_creates_active_referentials(db_session: AsyncSession):
    items, total = await referential_service.list_referentials(db_session, active_only=True)
    labels = {r.label for r in items}
    assert total >= 12
    assert "ISO 27001" in labels
    assert "EBIOS RM" in labels
    assert all(r.status == "active" for r in items)


@pytest.mark.asyncio
async def test_seed_is_idempotent(db_session: AsyncSession):
    await run_admin_seed(db_session)
    await db_session.commit()
    count = await db_session.scalar(select(ReferentialFramework.id))
    _, total = await referential_service.list_referentials(db_session)
    assert count is not None
    assert total == 12


@pytest.mark.asyncio
async def test_create_referential_appears_in_list(db_session: AsyncSession):
    async def override_get_db():
        yield db_session

    fastapi_app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=fastapi_app)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            created = await client.post(
                "/api/admin/referentials",
                json={"label": "Doctrine Cloud", "category": "Cloud"},
            )
            assert created.status_code == 201
            body = created.json()
            assert body["code"] == "doctrine-cloud"

            listing = await client.get("/api/admin/referentials")
            assert listing.status_code == 200
            labels = [item["label"] for item in listing.json()["items"]]
            assert "Doctrine Cloud" in labels
    finally:
        fastapi_app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_quick_add_referential_from_project_form_appears_in_active_list(
    db_session: AsyncSession,
):
    """Simule l'ajout rapide d'un référentiel depuis le formulaire projet."""

    async def override_get_db():
        yield db_session

    fastapi_app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=fastapi_app)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            created = await client.post(
                "/api/admin/referentials",
                json={
                    "label": "ISO 42001",
                    "code": "iso-42001",
                    "description": "Gouvernance de l'IA",
                    "status": "active",
                },
            )
            assert created.status_code == 201
            body = created.json()
            assert body["code"] == "iso-42001"
            assert body["status"] == "active"

            # Le formulaire projet ne charge que les référentiels actifs.
            listing = await client.get("/api/admin/referentials?active_only=true")
            assert listing.status_code == 200
            labels = [item["label"] for item in listing.json()["items"]]
            assert "ISO 42001" in labels
    finally:
        fastapi_app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_referential_rejects_duplicate_code_with_clear_message(
    db_session: AsyncSession,
):
    async def override_get_db():
        yield db_session

    fastapi_app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=fastapi_app)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            first = await client.post(
                "/api/admin/referentials",
                json={"label": "SecNumCloud", "code": "secnumcloud"},
            )
            assert first.status_code == 201

            duplicate = await client.post(
                "/api/admin/referentials",
                json={"label": "SecNumCloud (bis)", "code": "secnumcloud"},
            )
            assert duplicate.status_code == 400
            assert "existe déjà" in duplicate.json()["detail"]
    finally:
        fastapi_app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_deactivated_referential_excluded_from_active_list(db_session: AsyncSession):
    ref = await referential_service.create_referential(
        db_session,
        referential_service.ReferentialCreate(label="Temporaire"),
    )
    await db_session.commit()
    await referential_service.set_status(db_session, ref.id, "archived")
    await db_session.commit()

    active, _ = await referential_service.list_referentials(db_session, active_only=True)
    assert "Temporaire" not in {r.label for r in active}
    all_items, _ = await referential_service.list_referentials(db_session)
    assert "Temporaire" in {r.label for r in all_items}


@pytest.mark.asyncio
async def test_login_returns_organization_id(db_session: AsyncSession):
    result = await db_session.execute(select(User).where(User.username == "admin"))
    admin = result.scalar_one()
    assert admin.organization_id is not None

    response = await login(db_session, "admin", "Admin@123")
    assert response.user.organizationId == str(admin.organization_id)
