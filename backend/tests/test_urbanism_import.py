"""Tests — import cartographie urbanisme V1.4."""

from __future__ import annotations

import asyncio

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.main import app as fastapi_app
from app.models.cartography import CartographyVersion
from app.models.entities import Project, UrbanismEntity, UrbanismRelation
import app.models.admin  # noqa: F401
import app.models.entities  # noqa: F401
from app.services import cartography_service
from app.services.urbanism_import import ImportMode, execute_import, generate_official_template, preview_from_bytes


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


@pytest_asyncio.fixture
async def project(db_session: AsyncSession) -> Project:
    project = Project(name="Import test", organization={"name": "Test"})
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)
    return project


@pytest.fixture
def template_bytes() -> bytes:
    return generate_official_template()


@pytest.mark.asyncio
async def test_template_generation(template_bytes: bytes):
    assert template_bytes[:2] == b"PK"
    assert len(template_bytes) > 5000


@pytest.mark.asyncio
async def test_preview_official_template(template_bytes: bytes):
    preview = preview_from_bytes(template_bytes, "modele.xlsx", ImportMode.MERGE)
    assert preview["counts"]["metiers"] >= 1
    assert preview["counts"]["applications"] >= 2
    assert preview["counts"]["relations"] >= 1
    assert preview["can_import"] is True


@pytest.mark.asyncio
async def test_execute_import_merge(
    db_session: AsyncSession, project: Project, template_bytes: bytes
):
    report = await execute_import(
        db_session,
        project.id,
        template_bytes,
        "modele.xlsx",
        ImportMode.MERGE,
    )
    assert sum(report.created.values()) > 0
    assert report.relations_created > 0

    entity_count = await db_session.scalar(
        select(func.count()).select_from(UrbanismEntity).where(UrbanismEntity.project_id == project.id)
    )
    relation_count = await db_session.scalar(
        select(func.count()).select_from(UrbanismRelation).where(UrbanismRelation.project_id == project.id)
    )
    assert entity_count and entity_count > 5
    assert relation_count and relation_count > 0


@pytest.mark.asyncio
async def test_execute_import_idempotent_merge(
    db_session: AsyncSession, project: Project, template_bytes: bytes
):
    await execute_import(db_session, project.id, template_bytes, "modele.xlsx", ImportMode.MERGE)
    before = await db_session.scalar(
        select(func.count()).select_from(UrbanismEntity).where(UrbanismEntity.project_id == project.id)
    )
    report = await execute_import(
        db_session, project.id, template_bytes, "modele.xlsx", ImportMode.MERGE
    )
    after = await db_session.scalar(
        select(func.count()).select_from(UrbanismEntity).where(UrbanismEntity.project_id == project.id)
    )
    assert before == after
    assert sum(report.updated.values()) > 0


@pytest.mark.asyncio
async def test_import_api_preview_and_execute(
    db_session: AsyncSession, project: Project, template_bytes: bytes
):
    async def override_get_db():
        yield db_session

    fastapi_app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=fastapi_app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        template_res = await client.get("/api/urbanism/import/template")
        assert template_res.status_code == 200
        assert template_res.content[:2] == b"PK"

        files = {"file": ("modele.xlsx", template_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        preview_res = await client.post(
            f"/api/projects/{project.id}/urbanism/import/preview",
            files=files,
            data={"mode": "merge"},
        )
        assert preview_res.status_code == 200
        body = preview_res.json()
        assert body["counts"]["metiers"] >= 1

        import_res = await client.post(
            f"/api/projects/{project.id}/urbanism/import",
            files=files,
            data={"mode": "merge", "force": "false"},
        )
        assert import_res.status_code == 200
        report = import_res.json()
        assert report["relations_created"] > 0

    fastapi_app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_import_execute_route_does_not_duplicate_import_segment(
    db_session: AsyncSession, project: Project, template_bytes: bytes
):
    """Regression test: the frontend must call POST .../urbanism/import, NOT
    .../urbanism/import/import — the latter must not be a registered route."""

    async def override_get_db():
        yield db_session

    fastapi_app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=fastapi_app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        files = {
            "file": (
                "modele.xlsx",
                template_bytes,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        }

        wrong_url_res = await client.post(
            f"/api/projects/{project.id}/urbanism/import/import",
            files=files,
            data={"mode": "merge", "force": "false"},
        )
        assert wrong_url_res.status_code == 404

        correct_url_res = await client.post(
            f"/api/projects/{project.id}/urbanism/import",
            files=files,
            data={"mode": "merge", "force": "false"},
        )
        assert correct_url_res.status_code == 200

    fastapi_app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_import_execute_targets_selected_cartography_id(
    db_session: AsyncSession, project: Project, template_bytes: bytes
):
    """The `cartography_id` query param must scope the import to that exact
    cartography's current version, without touching the active/default one."""

    default_cartography = await cartography_service.ensure_default_cartography(db_session, project)

    target_cartography = await cartography_service.create_cartography(
        db_session,
        project.id,
        name="Urbanisme Technique",
        type_="urbanisme_technique",
        description=None,
        author="Testeur",
    )
    assert target_cartography.id != default_cartography.id

    async def override_get_db():
        yield db_session

    fastapi_app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=fastapi_app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        files = {
            "file": (
                "modele.xlsx",
                template_bytes,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        }
        import_res = await client.post(
            f"/api/projects/{project.id}/urbanism/import",
            params={"cartography_id": str(target_cartography.id)},
            files=files,
            data={"mode": "merge", "force": "false"},
        )
        assert import_res.status_code == 200
        report = import_res.json()
        assert sum(report["created"].values()) > 0

    fastapi_app.dependency_overrides.clear()

    target_version = await db_session.scalar(
        select(CartographyVersion).where(
            CartographyVersion.cartography_id == target_cartography.id,
            CartographyVersion.is_current.is_(True),
        )
    )
    default_version = await db_session.scalar(
        select(CartographyVersion).where(
            CartographyVersion.cartography_id == default_cartography.id,
            CartographyVersion.is_current.is_(True),
        )
    )

    imported_count = await db_session.scalar(
        select(func.count())
        .select_from(UrbanismEntity)
        .where(UrbanismEntity.cartography_version_id == target_version.id)
    )
    default_count = await db_session.scalar(
        select(func.count())
        .select_from(UrbanismEntity)
        .where(UrbanismEntity.cartography_version_id == default_version.id)
    )
    assert imported_count and imported_count > 0
    assert default_count == 0
