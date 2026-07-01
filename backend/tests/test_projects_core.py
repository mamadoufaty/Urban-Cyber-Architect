"""Tests — API projet V1.3 (core project)."""

from __future__ import annotations

import asyncio
from datetime import date

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.main import app as fastapi_app
from app.models.admin import User
from app.services.password_service import hash_password
import app.models.admin  # noqa: F401
import app.models.deliverables  # noqa: F401
import app.models.ebios  # noqa: F401
import app.models.project_core  # noqa: F401


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
        user = User(
            username="chef_projet_test",
            password_hash=hash_password("secret"),
            first_name="Chef",
            last_name="Projet",
            email="chef@test.local",
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        session.info["test_user_id"] = str(user.id)
        yield session
    await engine.dispose()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession):
    async def override_get_db():
        yield db_session

    fastapi_app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://test") as http_client:
        yield http_client, db_session
    fastapi_app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_project(client):
    http, db = client
    user_id = db.info["test_user_id"]
    response = await http.post(
        "/api/projects",
        json={
            "name": "Transformation SI",
            "description": "Projet pilote",
            "code": "transfo-si",
            "client": "Acme Corp",
            "priority": "high",
            "start_date": "2025-01-15",
            "end_date": "2025-12-31",
            "tags": ["cyber", "urbanisme"],
            "created_by": user_id,
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Transformation SI"
    assert body["code"] == "transfo-si"
    assert body["client"] == "Acme Corp"
    assert body["priority"] == "high"
    assert body["tags"] == ["cyber", "urbanisme"]
    assert body["status"] == "draft"
    assert body["organization"]  # rétrocompatibilité frontend

    activity = await http.get(f"/api/projects/{body['id']}/activity")
    assert activity.status_code == 200
    actions = [a["action"] for a in activity.json()]
    assert "project.created" in actions


@pytest.mark.asyncio
async def test_list_projects(client):
    http, _ = client
    await http.post("/api/projects", json={"name": "Projet A"})
    await http.post("/api/projects", json={"name": "Projet B"})
    response = await http.get("/api/projects")
    assert response.status_code == 200
    names = {p["name"] for p in response.json()}
    assert "Projet A" in names
    assert "Projet B" in names


@pytest.mark.asyncio
async def test_update_project(client):
    http, _ = client
    created = await http.post("/api/projects", json={"name": "Avant"})
    project_id = created.json()["id"]
    response = await http.put(
        f"/api/projects/{project_id}",
        json={"name": "Après", "client": "Client X", "priority": "low"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Après"
    assert body["client"] == "Client X"
    assert body["priority"] == "low"

    activity = await http.get(f"/api/projects/{project_id}/activity")
    assert any(a["action"] == "project.updated" for a in activity.json())


@pytest.mark.asyncio
async def test_duplicate_project(client):
    http, db = client
    user_id = db.info["test_user_id"]
    created = await http.post(
        "/api/projects",
        json={"name": "Original", "client": "Dup Co", "created_by": user_id},
    )
    source_id = created.json()["id"]
    response = await http.post(f"/api/projects/{source_id}/duplicate")
    assert response.status_code == 201
    clone = response.json()
    assert clone["name"] == "Original (copie)"
    assert clone["client"] == "Dup Co"
    assert clone["id"] != source_id
    assert clone["status"] == "draft"

    source_activity = await http.get(f"/api/projects/{source_id}/activity")
    assert any(a["action"] == "project.duplicated" for a in source_activity.json())


@pytest.mark.asyncio
async def test_archive_project(client):
    http, _ = client
    created = await http.post("/api/projects", json={"name": "À archiver"})
    project_id = created.json()["id"]
    response = await http.post(f"/api/projects/{project_id}/archive")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "archived"
    assert body["archived_at"] is not None

    activity = await http.get(f"/api/projects/{project_id}/activity")
    assert any(a["action"] == "project.archived" for a in activity.json())

    again = await http.post(f"/api/projects/{project_id}/archive")
    assert again.status_code == 200
    assert again.json()["archived_at"] == body["archived_at"]


@pytest.mark.asyncio
async def test_project_members(client):
    http, db = client
    user_id = db.info["test_user_id"]
    created = await http.post("/api/projects", json={"name": "Équipe"})
    project_id = created.json()["id"]

    bad_role = await http.post(
        f"/api/projects/{project_id}/members",
        json={"user_id": user_id, "project_role": "inconnu"},
    )
    assert bad_role.status_code == 400

    added = await http.post(
        f"/api/projects/{project_id}/members",
        json={"user_id": user_id, "project_role": "chef_projet"},
    )
    assert added.status_code == 201
    member = added.json()
    assert member["project_role"] == "chef_projet"

    listed = await http.get(f"/api/projects/{project_id}/members")
    assert len(listed.json()) == 1

    duplicate = await http.post(
        f"/api/projects/{project_id}/members",
        json={"user_id": user_id, "project_role": "rssi"},
    )
    assert duplicate.status_code == 400

    deleted = await http.delete(f"/api/projects/{project_id}/members/{member['id']}")
    assert deleted.status_code == 204
    empty = await http.get(f"/api/projects/{project_id}/members")
    assert empty.json() == []

    activity = await http.get(f"/api/projects/{project_id}/activity")
    actions = [a["action"] for a in activity.json()]
    assert "member.added" in actions
    assert "member.removed" in actions


@pytest.mark.asyncio
async def test_project_activity_history(client):
    http, db = client
    user_id = db.info["test_user_id"]
    created = await http.post(
        "/api/projects",
        json={"name": "Historique", "created_by": user_id},
    )
    project_id = created.json()["id"]
    await http.put(f"/api/projects/{project_id}", json={"description": "Mise à jour"})
    await http.post(
        f"/api/projects/{project_id}/members",
        json={"user_id": user_id, "project_role": "rssi"},
    )

    response = await http.get(f"/api/projects/{project_id}/activity")
    assert response.status_code == 200
    actions = {a["action"] for a in response.json()}
    assert "project.created" in actions
    assert "project.updated" in actions
    assert "member.added" in actions
