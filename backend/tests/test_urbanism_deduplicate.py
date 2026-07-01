"""Tests déduplication et réutilisation entités."""

import uuid

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base
from app.models.entities import Project, UrbanismEntity, UrbanismRelation
from app.services.urbanism_assistant import assisted_create, get_form_schema
from app.services.urbanism_deduplicate import deduplicate_project
from app.services.urbanism_engine import build_cartography


@pytest.fixture(scope="session")
def event_loop():
    import asyncio
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
    project = Project(name="Dedup test", organization={})
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)
    return project


@pytest.mark.asyncio
async def test_assisted_create_reuses_existing_entity(db_session: AsyncSession, project: Project):
    first = await assisted_create(db_session, project.id, "ilot_applicatif", "Microsoft Sentinel", {})
    assert first["reused"] is False

    second = await assisted_create(db_session, project.id, "ilot_applicatif", "microsoft sentinel", {})
    assert second["reused"] is True
    assert second["entity"].id == first["entity"].id

    entities = list(
        (await db_session.execute(
            select(UrbanismEntity).where(
                UrbanismEntity.project_id == project.id,
                UrbanismEntity.entity_type == "ilot_applicatif",
            )
        )).scalars()
    )
    assert len(entities) == 1


@pytest.mark.asyncio
async def test_deduplicate_merges_labels_with_type_suffix(db_session: AsyncSession, project: Project):
    a = UrbanismEntity(
        project_id=project.id, entity_type="ilot_applicatif", couche="applicatif",
        label="Microsoft Sentinel",
    )
    b = UrbanismEntity(
        project_id=project.id, entity_type="ilot_applicatif", couche="applicatif",
        label="Microsoft Sentinel (ilot_applicatif)",
    )
    db_session.add_all([a, b])
    await db_session.commit()

    result = await deduplicate_project(db_session, project.id)
    assert result["merged_groups"] == 1
    assert result["entities_removed"] == 1

    remaining = list(
        (await db_session.execute(select(UrbanismEntity).where(UrbanismEntity.project_id == project.id))).scalars()
    )
    assert len(remaining) == 1


@pytest.mark.asyncio
async def test_ilot_applicatif_form_offers_virtual_ilot_fonctionnel(db_session: AsyncSession, project: Project):
    classe = UrbanismEntity(
        project_id=project.id, entity_type="classe", couche="metier", label="Événements",
    )
    ilot = UrbanismEntity(
        project_id=project.id, entity_type="ilot_fonctionnel", couche="fonctionnel", label="Supervision",
    )
    db_session.add_all([classe, ilot])
    await db_session.flush()
    db_session.add(
        UrbanismRelation(
            project_id=project.id,
            source_id=classe.id,
            target_id=ilot.id,
            relation_type="donne lieu à",
            category="fonctionnel",
        )
    )
    await db_session.commit()

    schema = await get_form_schema(db_session, project.id, "ilot_applicatif")
    virtual = next((f for f in schema["fields"] if f["field_id"] == "virtual_linked_ilot_fonctionnel"), None)
    assert virtual is not None
    assert virtual["required"] is True
    assert virtual["label"] == "Sélectionnez l'Îlot fonctionnel"
    assert len(virtual["options"]) == 1


@pytest.mark.asyncio
async def test_orphan_applicatif_visible_in_graph(db_session: AsyncSession, project: Project):
    ilot = UrbanismEntity(
        project_id=project.id, entity_type="ilot_applicatif", couche="applicatif", label="Microsoft Sentinel",
    )
    db_session.add(ilot)
    await db_session.commit()

    graph = await build_cartography(db_session, project)
    applicatif_nodes = [n for n in graph["nodes"] if n["entity_type"] == "ilot_applicatif"]
    assert len(applicatif_nodes) == 1
    assert applicatif_nodes[0]["couche"] == "applicatif"


@pytest.mark.asyncio
async def test_assisted_create_ilot_applicatif_with_virtual_field(db_session: AsyncSession, project: Project):
  classe = UrbanismEntity(
      project_id=project.id, entity_type="classe", couche="metier", label="Événements",
  )
  ilot_f = UrbanismEntity(
      project_id=project.id, entity_type="ilot_fonctionnel", couche="fonctionnel", label="Supervision",
  )
  db_session.add_all([classe, ilot_f])
  await db_session.flush()
  db_session.add(
      UrbanismRelation(
          project_id=project.id,
          source_id=classe.id,
          target_id=ilot_f.id,
          relation_type="donne lieu à",
          category="fonctionnel",
      )
  )
  await db_session.commit()

  result = await assisted_create(
      db_session,
      project.id,
      "ilot_applicatif",
      "QRadar",
      {"virtual_linked_ilot_fonctionnel": [str(ilot_f.id)]},
  )
  assert result["entity"].label == "QRadar"
  assert result["entity"].entity_type == "ilot_applicatif"
  assert result["entity"].couche == "applicatif"
  assert not (result["entity"].properties or {}).get("ilot_fonctionnel_id")

  from app.services.urbanism_entity_utils import get_assistant_ilot_fonctionnel_id

  assert get_assistant_ilot_fonctionnel_id(result["entity"]) == ilot_f.id

  graph = await build_cartography(db_session, project)
  derived = [e for e in graph["edges"] if e.get("derived")]
  assert len(derived) >= 1
  assert any(e["source"] == str(ilot_f.id) and e["target"] == str(result["entity"].id) for e in derived)
  orphan_ids = {o["id"] for o in graph["analysis"]["orphans"]}
  assert str(result["entity"].id) not in orphan_ids


@pytest.mark.asyncio
async def test_ilot_applicatif_with_derived_link_not_orphan(db_session: AsyncSession, project: Project):
    ilot_f = UrbanismEntity(
        project_id=project.id, entity_type="ilot_fonctionnel", couche="fonctionnel", label="Supervision",
    )
    db_session.add(ilot_f)
    await db_session.flush()

    result = await assisted_create(
        db_session,
        project.id,
        "ilot_applicatif",
        "QRadar",
        {"virtual_linked_ilot_fonctionnel": [str(ilot_f.id)]},
    )

    graph = await build_cartography(db_session, project)
    orphan_labels = [o["label"] for o in graph["analysis"]["orphans"]]
    assert "QRadar" not in orphan_labels
    assert graph["analysis"]["orphan_count"] == len(graph["analysis"]["orphans"])


@pytest.mark.asyncio
async def test_derived_edge_virtual_binding_with_multiple_ilots(db_session: AsyncSession, project: Project):
    ilot_f1 = UrbanismEntity(
        project_id=project.id, entity_type="ilot_fonctionnel", couche="fonctionnel", label="Supervision",
    )
    ilot_f2 = UrbanismEntity(
        project_id=project.id, entity_type="ilot_fonctionnel", couche="fonctionnel", label="Exploitation",
    )
    sentinel = UrbanismEntity(
        project_id=project.id, entity_type="ilot_applicatif", couche="applicatif", label="Microsoft Sentinel",
    )
    db_session.add_all([ilot_f1, ilot_f2, sentinel])
    await db_session.commit()

    result = await assisted_create(
        db_session,
        project.id,
        "ilot_applicatif",
        "QRadar",
        {"virtual_linked_ilot_fonctionnel": [str(ilot_f1.id)]},
    )

    graph = await build_cartography(db_session, project)
    derived = [e for e in graph["edges"] if e.get("derived")]
    matching = [
        e for e in derived
        if e["source"] == str(ilot_f1.id) and e["target"] == str(result["entity"].id)
    ]
    assert len(matching) == 1
    assert matching[0]["relation_type"] == "est mis en œuvre par"

    applicatif_nodes = [
        n for n in graph["nodes"]
        if n["entity_type"] == "ilot_applicatif"
    ]
    assert all(n["couche"] == "applicatif" for n in applicatif_nodes)


@pytest.mark.asyncio
async def test_wrong_stored_couche_resolved_to_applicatif(db_session: AsyncSession, project: Project):
    qradar = UrbanismEntity(
        project_id=project.id,
        entity_type="ilot_applicatif",
        couche="technique",
        label="QRadar",
    )
    db_session.add(qradar)
    await db_session.commit()

    graph = await build_cartography(db_session, project)
    node = next(n for n in graph["nodes"] if n["label"] == "QRadar")
    assert node["couche"] == "applicatif"
    assert node["couche_color"] == "#f59e0b"


@pytest.mark.asyncio
async def test_derived_edge_one_to_one_inference(db_session: AsyncSession, project: Project):
    ilot_f = UrbanismEntity(
        project_id=project.id, entity_type="ilot_fonctionnel", couche="fonctionnel", label="Supervision",
    )
    ilot_a = UrbanismEntity(
        project_id=project.id,
        entity_type="ilot_applicatif",
        couche="applicatif",
        label="QRadar",
    )
    db_session.add_all([ilot_f, ilot_a])
    await db_session.commit()

    graph = await build_cartography(db_session, project)
    derived = [e for e in graph["edges"] if e.get("derived")]
    assert len(derived) == 1
    assert derived[0]["relation_type"] == "est mis en œuvre par"
