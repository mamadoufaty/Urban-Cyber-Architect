import asyncio
import uuid

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base
from app.models.entities import Project
from app.services.urbanism_assistant import AssistantError, assisted_create, assisted_link, get_form_schema


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
    project = Project(name="Test Métropolis", organization={"sector": "smart_city"})
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)
    return project


async def _create(db: AsyncSession, project_id: uuid.UUID, entity_type: str, label: str, bindings: dict | None = None):
    return await assisted_create(db, project_id, entity_type, label, bindings or {})


@pytest.mark.asyncio
async def test_create_metier_no_relations(db_session: AsyncSession, project: Project):
    """Exemple 1 — Métier sans dépendance."""
    schema = await get_form_schema(db_session, project.id, "metier")
    assert schema["entity_type"] == "metier"
    assert schema["fields"] == []

    result = await _create(db_session, project.id, "metier", "Gestion des services urbains")
    assert result["entity"].entity_type == "metier"
    assert result["entity"].label == "Gestion des services urbains"
    assert result["relations_created"] == []
    assert result["bindings_applied"] == 0


@pytest.mark.asyncio
async def test_create_objectif_with_metier(db_session: AsyncSession, project: Project):
    """Exemple 2 — Objectif lié automatiquement au Métier (R02)."""
    metier = (await _create(db_session, project.id, "metier", "Gestion des services urbains"))["entity"]

    schema = await get_form_schema(db_session, project.id, "objectif")
    assert len(schema["fields"]) >= 1
    metier_field = next(f for f in schema["fields"] if f["rule_id"] == "R02")
    assert metier_field["required"] is True
    assert metier_field["selected"] == [str(metier.id)]

    result = await _create(
        db_session,
        project.id,
        "objectif",
        "Assurer la continuité des services",
        {metier_field["field_id"]: [str(metier.id)]},
    )
    assert result["entity"].entity_type == "objectif"
    assert len(result["relations_created"]) == 1
    rel = result["relations_created"][0]
    assert rel.relation_type == "définit"
    assert rel.source_id == metier.id
    assert rel.target_id == result["entity"].id


@pytest.mark.asyncio
async def test_create_objectif_fails_without_required_metier(db_session: AsyncSession, project: Project):
    await _create(db_session, project.id, "metier", "Gestion des services urbains")

    with pytest.raises(AssistantError, match="obligatoire"):
        await _create(db_session, project.id, "objectif", "Objectif orphelin", {})


@pytest.mark.asyncio
async def test_create_processus_with_dependencies(db_session: AsyncSession, project: Project):
    """Exemple 3 — Processus avec Métier, Objectifs et Procédures."""
    metier = (await _create(db_session, project.id, "metier", "Gestion des services urbains"))["entity"]
    org = (await _create(
        db_session, project.id, "organisation", "Direction du numérique",
        {"R04_incoming_metier": [str(metier.id)]},
    ))["entity"]
    procedure = (await _create(
        db_session, project.id, "procedure", "Procédure incident",
        {"R12_incoming_organisation": [str(org.id)]},
    ))["entity"]
    objectif = (await _create(
        db_session, project.id, "objectif", "Continuité de service",
        {"R02_incoming_metier": [str(metier.id)]},
    ))["entity"]

    schema = await get_form_schema(db_session, project.id, "processus")
    field_ids = {f["rule_id"] for f in schema["fields"]}
    assert "R03" in field_ids
    assert "R05" in field_ids
    assert "R13" in field_ids
    r05_field = next(f for f in schema["fields"] if f["rule_id"] == "R05")
    assert r05_field["required"] is True
    assert "R05_incoming_objectif" in schema["required_field_ids"]

    bindings = {
        "R03_incoming_metier": [str(metier.id)],
        "R05_incoming_objectif": [str(objectif.id)],
        "R13_incoming_procedure": [str(procedure.id)],
    }
    result = await _create(
        db_session, project.id, "processus", "Gestion des incidents citoyens", bindings
    )
    assert result["entity"].entity_type == "processus"
    assert len(result["relations_created"]) == 3
    types = {r.relation_type for r in result["relations_created"]}
    assert types == {"pilote", "est pris en compte dans", "s'organise en"}


@pytest.mark.asyncio
async def test_create_activite_with_processus(db_session: AsyncSession, project: Project):
    """Exemple 4 — Activité rattachée au Processus parent (R06)."""
    metier = (await _create(db_session, project.id, "metier", "Gestion des services urbains"))["entity"]
    processus = (await _create(
        db_session, project.id, "processus", "Supervision",
        {"R03_incoming_metier": [str(metier.id)]},
    ))["entity"]

    schema = await get_form_schema(db_session, project.id, "activite")
    proc_field = next(f for f in schema["fields"] if f["rule_id"] == "R06")
    assert proc_field["required"] is True

    result = await _create(
        db_session, project.id, "activite", "Analyser les alertes",
        {proc_field["field_id"]: [str(processus.id)]},
    )
    assert len(result["relations_created"]) == 1
    rel = result["relations_created"][0]
    assert rel.relation_type == "se décompose en"
    assert rel.source_id == processus.id
    assert rel.target_id == result["entity"].id


@pytest.mark.asyncio
async def test_assistant_link_add_and_remove(db_session: AsyncSession, project: Project):
    metier = (await _create(db_session, project.id, "metier", "Métier test"))["entity"]
    processus = (await _create(
        db_session, project.id, "processus", "Processus test",
        {"R03_incoming_metier": [str(metier.id)]},
    ))["entity"]
    objectif = (await _create(
        db_session, project.id, "objectif", "Objectif test",
        {"R02_incoming_metier": [str(metier.id)]},
    ))["entity"]

    add_result = await assisted_link(
        db_session, project.id, "add", "R05", objectif.id, processus.id,
    )
    assert add_result["relation"] is not None
    assert add_result["relation"].relation_type == "est pris en compte dans"

    remove_result = await assisted_link(
        db_session, project.id, "remove", "R05", objectif.id, processus.id,
    )
    assert remove_result["action"] == "remove"


@pytest.mark.asyncio
async def test_form_schema_hides_orphan_duplicate_peers(db_session: AsyncSession, project: Project):
    """Doublon orphelin (même libellé) masqué si une entité reliée existe — aligné avec le graphe."""
    from app.models.entities import UrbanismEntity, UrbanismRelation
    from app.services.urbanism_assistant.form_schema_generator import generate_form_schema

    metier = UrbanismEntity(
        project_id=project.id, entity_type="metier", couche="metier", label="Métier test",
    )
    classe = UrbanismEntity(
        project_id=project.id, entity_type="classe", couche="metier", label="Classe test",
    )
    ilot_connected = UrbanismEntity(
        project_id=project.id, entity_type="ilot_fonctionnel", couche="fonctionnel", label="Supervision",
    )
    ilot_orphan = UrbanismEntity(
        project_id=project.id, entity_type="ilot_fonctionnel", couche="fonctionnel", label="Supervision",
    )
    db_session.add_all([metier, classe, ilot_connected, ilot_orphan])
    await db_session.flush()

    relations = [
        UrbanismRelation(
            project_id=project.id,
            source_id=classe.id,
            target_id=ilot_connected.id,
            relation_type="donne lieu à",
            category="fonctionnel",
        ),
    ]
    db_session.add_all(relations)
    await db_session.commit()

    entities = [metier, classe, ilot_connected, ilot_orphan]
    schema = generate_form_schema("quartier_fonctionnel", entities, relations)
    ilot_field = next(f for f in schema["fields"] if f["peer_type"] == "ilot_fonctionnel")
    assert len(ilot_field["options"]) == 1
    assert ilot_field["options"][0]["entity_id"] == str(ilot_connected.id)


@pytest.mark.asyncio
async def test_duplicate_relation_rejected(db_session: AsyncSession, project: Project):
    metier = (await _create(db_session, project.id, "metier", "Métier"))["entity"]
    objectif = (await _create(
        db_session, project.id, "objectif", "Obj1",
        {"R02_incoming_metier": [str(metier.id)]},
    ))["entity"]

    with pytest.raises(AssistantError, match="existe déjà"):
        await assisted_link(db_session, project.id, "add", "R02", metier.id, objectif.id)
