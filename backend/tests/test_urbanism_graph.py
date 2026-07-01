"""Pipeline graphe — R05 persistée, API et cohérence métamodèle."""

import asyncio
import uuid

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base
from app.models.entities import Project, UrbanismRelation
from app.services.urbanism_assistant import assisted_create
from app.services.urbanism_engine import build_cartography, sync_missing_r05_relations


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
    project = Project(name="Graph R05", organization={})
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)
    return project


async def _create(db: AsyncSession, project_id: uuid.UUID, entity_type: str, label: str, bindings: dict | None = None):
    return await assisted_create(db, project_id, entity_type, label, bindings or {})


@pytest.mark.asyncio
async def test_sync_r05_creates_missing_relation(db_session: AsyncSession, project: Project):
    """Triangle Métier/Objectif/Processus sans R05 → synchronisation automatique."""
    metier = (await _create(db_session, project.id, "metier", "Métier test"))["entity"]
    processus = (await _create(
        db_session, project.id, "processus", "Processus test",
        {"R03_incoming_metier": [str(metier.id)]},
    ))["entity"]
    objectif = (await _create(
        db_session, project.id, "objectif", "Objectif test",
        {"R02_incoming_metier": [str(metier.id)]},
    ))["entity"]

    relations = list(
        (await db_session.execute(
            select(UrbanismRelation).where(UrbanismRelation.project_id == project.id)
        )).scalars()
    )
    r05_before = [r for r in relations if r.relation_type == "est pris en compte dans"]
    assert r05_before == []

    entities = [metier, objectif, processus]
    created = await sync_missing_r05_relations(db_session, project.id, entities, relations)
    assert len(created) == 1
    assert created[0].relation_type == "est pris en compte dans"
    assert str(created[0].source_id) == str(objectif.id)
    assert str(created[0].target_id) == str(processus.id)


@pytest.mark.asyncio
async def test_graph_api_returns_r05_edge(db_session: AsyncSession, project: Project):
    """GET graph inclut R05 après sync (Métier→Objectif, Métier→Processus, Objectif→Processus)."""
    metier = (await _create(db_session, project.id, "metier", "Métier test"))["entity"]
    await _create(
        db_session, project.id, "processus", "Processus test",
        {"R03_incoming_metier": [str(metier.id)]},
    )
    await _create(
        db_session, project.id, "objectif", "Objectif test",
        {"R02_incoming_metier": [str(metier.id)]},
    )

    graph = await build_cartography(db_session, project)
    relation_types = {e["relation_type"] for e in graph["edges"]}
    assert relation_types == {"définit", "pilote", "est pris en compte dans"}

    r05_edges = [e for e in graph["edges"] if e["relation_type"] == "est pris en compte dans"]
    assert len(r05_edges) == 1
    assert r05_edges[0]["category"] == "metier"

    objectif_nodes = [n for n in graph["nodes"] if n["entity_type"] == "objectif"]
    processus_nodes = [n for n in graph["nodes"] if n["entity_type"] == "processus"]
    assert r05_edges[0]["source"] == objectif_nodes[0]["id"]
    assert r05_edges[0]["target"] == processus_nodes[0]["id"]


@pytest.mark.asyncio
async def test_graph_edges_not_deduplicated_by_endpoints(db_session: AsyncSession, project: Project):
    """R02, R03 et R05 partagent des nœuds mais restent trois arêtes distinctes."""
    metier = (await _create(db_session, project.id, "metier", "Métier test"))["entity"]
    await _create(
        db_session, project.id, "processus", "Processus test",
        {"R03_incoming_metier": [str(metier.id)]},
    )
    await _create(
        db_session, project.id, "objectif", "Objectif test",
        {"R02_incoming_metier": [str(metier.id)]},
    )

    graph = await build_cartography(db_session, project)
    assert len(graph["edges"]) == 3
    assert len({e["id"] for e in graph["edges"]}) == 3


@pytest.mark.asyncio
async def test_graph_includes_derived_fonc_applic_edge_with_layout_key(
    db_session: AsyncSession, project: Project,
):
    """Régression : build_derived_edges doit exposer layout (sans NameError)."""
    from app.services.urbanism_assistant import assisted_create

    ilot_f = (
        await assisted_create(db_session, project.id, "ilot_fonctionnel", "Supervision", {})
    )["entity"]
    await assisted_create(
        db_session,
        project.id,
        "ilot_applicatif",
        "QRadar",
        {"virtual_linked_ilot_fonctionnel": [str(ilot_f.id)]},
    )

    graph = await build_cartography(db_session, project)
    derived = [e for e in graph["edges"] if e.get("derived")]
    assert len(derived) == 1
    assert "layout" in derived[0]
    assert derived[0]["layout"] is None
