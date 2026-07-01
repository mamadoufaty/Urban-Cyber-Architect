"""Tests — générateur de livrables documentaires."""

import asyncio
import json
import uuid
from datetime import datetime, timezone

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.main import app
from app.models.entities import Project, UrbanismEntity
from app.services.deliverables.deliverable_export import export_deliverable_pdf
from app.services.deliverables.deliverable_generator import collect_project_context, generate_deliverable
from app.services.deliverables.serialize_json import serialize_json
from app.services.deliverables.templates import build_project_management_plan


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


def test_serialize_json_converts_uuid_datetime_and_nested_structures():
    uid = uuid.uuid4()
    payload = {
        "id": uid,
        "items": [{"ref": uid}, (uid,)],
        "meta": {"created_at": datetime(2026, 6, 24, 12, 0, tzinfo=timezone.utc)},
    }
    serialized = serialize_json(payload)
    json.dumps(serialized)
    assert serialized["id"] == str(uid)
    assert serialized["items"][0]["ref"] == str(uid)
    assert serialized["items"][1][0] == str(uid)
    assert serialized["meta"]["created_at"].startswith("2026-06-24")


def test_serialize_json_on_generated_content_with_grc_uuids():
    uid = uuid.uuid4()
    content = serialize_json(
        {
            "title": "Plan",
            "metadata": {"project_id": uid},
            "context_snapshot": {
                "grc": {
                    "risk_register_sample": [{"assessment_id": uid, "owner_id": uid}],
                }
            },
            "sections": [],
        }
    )
    json.dumps(content)
    assert content["metadata"]["project_id"] == str(uid)
    assert content["context_snapshot"]["grc"]["risk_register_sample"][0]["assessment_id"] == str(uid)


def test_project_management_plan_has_eleven_sections():
    context = {
        "project": {
            "name": "Métropolis",
            "description": "Smart city",
            "organization": {"name": "Métropolis", "sector": "smart_city"},
            "objectives": ["Services numériques sécurisés"],
            "referentials": ["NIS2"],
        },
        "urbanism": {
            "acteurs": ["RSSI", "Architecte SI"],
            "organisations": ["Direction du numérique"],
            "processus": ["Mobilité"],
            "applications": ["Portail citoyen"],
            "biens_supports": ["Datacenter"],
        },
        "grc": {"risk_register_total": 3, "ptr_total": 2, "top_risks": []},
        "data_sources_used": ["urbanism", "grc"],
    }
    doc = build_project_management_plan(
        title="Plan Métropolis",
        user_need="Organisation multiculturelle et gouvernance projet",
        context=context,
        type_label="Plan de management de projet",
    )
    assert len(doc["sections"]) == 11
    assert doc["sections"][0]["title"].startswith("1.")
    assert "Métropolis" in doc["sections"][0]["content"]


def test_export_deliverable_pdf_bytes():
    content = {
        "title": "Test PDF",
        "sections": [{"title": "Section", "content": "Corps", "bullets": ["Point 1"]}],
    }
    assert export_deliverable_pdf(content)[:4] == b"%PDF"


@pytest.mark.asyncio
async def test_generate_deliverable_preview(db_session: AsyncSession):
    project = Project(
        name="Métropolis",
        organization={"name": "Métropolis", "sector": "smart_city"},
        objectives=["Résilience urbaine"],
    )
    db_session.add(project)
    await db_session.flush()
    db_session.add(
        UrbanismEntity(
            project_id=project.id,
            entity_type="acteur",
            couche="organisation",
            label="Chef de projet",
        )
    )
    await db_session.commit()

    result = await generate_deliverable(
        db_session,
        project.id,
        title="Plan de management",
        deliverable_type="project_management_plan",
        user_need="Équipe multiculturelle et parties prenantes",
        data_sources=["urbanism"],
        export_format="pdf",
        preview=True,
    )
    assert result["preview"] is True
    assert result["deliverable"] is None
    assert len(result["generated_content"]["sections"]) == 11


@pytest.mark.asyncio
async def test_deliverables_api(db_session: AsyncSession):
    project = Project(name="Métropolis", organization={"name": "Métropolis"})
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    base = f"/api/projects/{project.id}/deliverables"

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        listing = await client.get(base)
        assert listing.status_code == 200
        assert listing.json()["total"] == 0

        generated = await client.post(
            f"{base}/generate",
            json={
                "title": "Plan projet Métropolis",
                "deliverable_type": "project_management_plan",
                "user_need": "Management multiculturel",
                "data_sources": ["urbanism", "ebios", "grc"],
                "export_format": "markdown",
                "preview": False,
            },
        )
        assert generated.status_code == 200
        body = generated.json()
        assert body["deliverable"]["title"] == "Plan projet Métropolis"
        deliverable_id = body["deliverable"]["id"]

        detail = await client.get(f"{base}/{deliverable_id}")
        assert detail.status_code == 200
        assert len(detail.json()["generated_content"]["sections"]) == 11

        export_pdf = await client.get(f"{base}/{deliverable_id}/export?format=pdf")
        assert export_pdf.status_code == 200
        assert export_pdf.content[:4] == b"%PDF"

    ctx = await collect_project_context(db_session, project.id, ["urbanism"])
    assert ctx["project"]["name"] == "Métropolis"
    assert "urbanism" in ctx

    app.dependency_overrides.clear()
