"""Cartographies multiples par projet + versionning — service, API et migration."""

import asyncio
import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.main import app as fastapi_app
from app.models.cartography import Cartography, CartographyHistory, CartographyVersion
from app.models.entities import Project, UrbanismEntity, UrbanismRelation
from app.services import cartography_service
from app.services.cartography_service import CartographyError
from app.services.urbanism_assistant import assisted_create
from app.services.urbanism_engine import get_project_cartography


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
    project = Project(name="Métropolis", organization={})
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)
    return project


async def _create_entity(db, project_id, entity_type, label, bindings=None):
    return (await assisted_create(db, project_id, entity_type, label, bindings or {}))["entity"]


# ————————————————————————————————————————————————————————————————
# Migration / compatibilité descendante
# ————————————————————————————————————————————————————————————————


@pytest.mark.asyncio
async def test_ensure_default_cartography_backfills_legacy_graph(
    db_session: AsyncSession, project: Project
):
    """Un projet dont le graphe a été créé avant l'évolution cartographies
    reçoit automatiquement une cartographie par défaut contenant ce graphe."""
    legacy_entity = UrbanismEntity(
        project_id=project.id, entity_type="metier", couche="metier", label="Métier historique"
    )
    db_session.add(legacy_entity)
    await db_session.commit()
    await db_session.refresh(legacy_entity)
    assert legacy_entity.cartography_version_id is None

    cartography = await cartography_service.ensure_default_cartography(db_session, project)
    await db_session.commit()

    assert cartography.project_id == project.id
    assert cartography.is_active is True

    version = await cartography_service.get_current_version(db_session, cartography)
    await db_session.refresh(legacy_entity)
    assert legacy_entity.cartography_version_id == version.id

    # Idempotent : un second appel ne crée pas de deuxième cartographie.
    again = await cartography_service.ensure_default_cartography(db_session, project)
    assert again.id == cartography.id
    count = await db_session.scalar(
        select(cartography_service.Cartography.id).where(
            cartography_service.Cartography.project_id == project.id
        )
    )
    assert count is not None


@pytest.mark.asyncio
async def test_ensure_default_cartography_for_all_projects(db_session: AsyncSession):
    p1 = Project(name="P1", organization={})
    p2 = Project(name="P2", organization={})
    db_session.add_all([p1, p2])
    await db_session.commit()

    created = await cartography_service.ensure_default_cartography_for_all_projects(db_session)
    assert created == 2

    result = await db_session.execute(select(Cartography))
    all_cartographies = result.scalars().all()
    assert len(all_cartographies) == 2

    # Ré-exécution : idempotent, aucune cartographie supplémentaire créée.
    created_again = await cartography_service.ensure_default_cartography_for_all_projects(db_session)
    assert created_again == 0


@pytest.mark.asyncio
async def test_ensure_default_cartography_for_all_projects_with_multiple_existing_cartographies(
    db_session: AsyncSession, project: Project
):
    """Régression : un projet possédant déjà plusieurs cartographies (tests,
    versionning, imports) ne doit jamais faire planter le backfill de
    démarrage avec ``sqlalchemy.exc.MultipleResultsFound``."""
    await cartography_service.create_cartography(
        db_session, project.id, name="Urbanisme Métier", type_="urbanisme_metier",
        description=None, author=None,
    )
    await cartography_service.create_cartography(
        db_session, project.id, name="Cybersécurité", type_="cybersecurite",
        description=None, author=None,
    )
    count_before = (
        await db_session.execute(
            select(Cartography.id).where(Cartography.project_id == project.id)
        )
    ).scalars().all()
    assert len(count_before) >= 2

    # Ne doit lever aucune exception malgré les multiples lignes existantes.
    created = await cartography_service.ensure_default_cartography_for_all_projects(db_session)
    assert created == 0

    count_after = (
        await db_session.execute(
            select(Cartography.id).where(Cartography.project_id == project.id)
        )
    ).scalars().all()
    assert len(count_after) == len(count_before)


# ————————————————————————————————————————————————————————————————
# CRUD & indépendance des graphes
# ————————————————————————————————————————————————————————————————


@pytest.mark.asyncio
async def test_create_cartography_becomes_active_and_deactivates_others(
    db_session: AsyncSession, project: Project
):
    first = await cartography_service.create_cartography(
        db_session, project.id, name="Urbanisme Métier", type_="urbanisme_metier",
        description=None, author="Mamadou",
    )
    assert first.is_active is True

    second = await cartography_service.create_cartography(
        db_session, project.id, name="Cybersécurité", type_="cybersecurite",
        description="RSSI", author="RSSI",
    )
    await db_session.refresh(first)
    assert second.is_active is True
    assert first.is_active is False
    assert second.version == "1.0"
    assert second.status == "draft"


@pytest.mark.asyncio
async def test_new_project_gets_lazy_default_cartography_via_list(
    db_session: AsyncSession, project: Project
):
    items = await cartography_service.list_cartographies(db_session, project.id)
    assert len(items) == 1
    assert items[0].name == cartography_service.DEFAULT_CARTOGRAPHY_NAME
    assert items[0].is_active is True


@pytest.mark.asyncio
async def test_two_cartographies_have_fully_independent_graphs(
    db_session: AsyncSession, project: Project
):
    """§2 — aucune donnée n'est partagée entre deux cartographies d'un même projet."""
    cart_a = await cartography_service.create_cartography(
        db_session, project.id, name="Urbanisme Technique", type_="urbanisme_technique",
        description=None, author=None,
    )
    entity_a = await _create_entity(db_session, project.id, "metier", "Métier A")

    cart_b = await cartography_service.create_cartography(
        db_session, project.id, name="Cybersécurité", type_="cybersecurite",
        description=None, author=None,
    )
    entity_b = await _create_entity(db_session, project.id, "metier", "Métier B")

    graph_a = await get_project_cartography(db_session, project.id, cartography_id=cart_a.id)
    graph_b = await get_project_cartography(db_session, project.id, cartography_id=cart_b.id)

    labels_a = {n["label"] for n in graph_a["nodes"]}
    labels_b = {n["label"] for n in graph_b["nodes"]}
    assert "Métier A" in labels_a and "Métier B" not in labels_a
    assert "Métier B" in labels_b and "Métier A" not in labels_b


@pytest.mark.asyncio
async def test_delete_cartography_removes_its_graph_only(
    db_session: AsyncSession, project: Project
):
    default_cart = await cartography_service.ensure_default_cartography(db_session, project)
    await _create_entity(db_session, project.id, "metier", "Reste")

    extra = await cartography_service.create_cartography(
        db_session, project.id, name="À supprimer", type_="libre", description=None, author=None
    )
    entity_extra = await _create_entity(db_session, project.id, "metier", "Disparaît")
    entity_extra_id = entity_extra.id
    default_cart_id = default_cart.id
    project_id = project.id

    await cartography_service.delete_cartography(db_session, extra.id)

    remaining_entity = (
        await db_session.execute(select(UrbanismEntity).where(UrbanismEntity.id == entity_extra_id))
    ).scalar_one_or_none()
    assert remaining_entity is None

    # La cartographie par défaut redevient active et son graphe est intact.
    refreshed_default = await db_session.get(Cartography, default_cart_id)
    assert refreshed_default.is_active is True
    graph = await get_project_cartography(db_session, project_id)
    assert any(n["label"] == "Reste" for n in graph["nodes"])


# ————————————————————————————————————————————————————————————————
# Versionning — validation, copie-sur-écriture, historique
# ————————————————————————————————————————————————————————————————


@pytest.mark.asyncio
async def test_validated_version_is_frozen_then_edit_creates_new_draft_version(
    db_session: AsyncSession, project: Project
):
    """§5 — Brouillon → Validation → Version figée → modification → v1.1 brouillon."""
    cartography = await cartography_service.ensure_default_cartography(db_session, project)
    metier = await _create_entity(db_session, project.id, "metier", "Métier v1")

    validated = await cartography_service.validate_cartography(
        db_session, cartography.id, validated_by="RSSI"
    )
    assert validated.status == "validated"
    assert validated.version == "1.0"
    v1 = await cartography_service.get_current_version(db_session, validated)
    assert v1.status == "validated"

    # Toute tentative de modification via le moteur déclenche une v1.1 brouillon.
    cartography2, version2, id_map = await cartography_service.resolve_editable_version(
        db_session, project.id, cartography.id
    )
    assert version2.id != v1.id
    assert version2.status == "draft"
    assert version2.version == "1.1"
    assert cartography2.version == "1.1"
    assert cartography2.status == "draft"
    assert metier.id in id_map

    # La version validée n'a pas été modifiée : son contenu reste intact.
    old_entities = list(
        (
            await db_session.execute(
                select(UrbanismEntity).where(UrbanismEntity.cartography_version_id == v1.id)
            )
        )
        .scalars()
        .all()
    )
    assert len(old_entities) == 1
    assert old_entities[0].id == metier.id

    new_entities = list(
        (
            await db_session.execute(
                select(UrbanismEntity).where(UrbanismEntity.cartography_version_id == version2.id)
            )
        )
        .scalars()
        .all()
    )
    assert len(new_entities) == 1
    assert new_entities[0].id != metier.id
    assert new_entities[0].label == "Métier v1"

    history = await cartography_service.get_cartography_history(db_session, cartography.id)
    actions = [h.action for h in history]
    assert "new_version" in actions
    assert "validated" in actions


@pytest.mark.asyncio
async def test_archived_cartography_cannot_be_edited(db_session: AsyncSession, project: Project):
    cartography = await cartography_service.ensure_default_cartography(db_session, project)
    await cartography_service.archive_cartography(db_session, cartography.id, author="Admin")

    with pytest.raises(CartographyError):
        await cartography_service.resolve_editable_version(db_session, project.id, cartography.id)


@pytest.mark.asyncio
async def test_create_new_version_manual_action(db_session: AsyncSession, project: Project):
    cartography = await cartography_service.ensure_default_cartography(db_session, project)
    updated = await cartography_service.create_new_version(
        db_session, cartography.id, author="Mamadou", comment="Ajout applications"
    )
    assert updated.version == "1.1"
    versions = await cartography_service.list_versions(db_session, cartography.id)
    assert {v.version for v in versions} == {"1.0", "1.1"}


@pytest.mark.asyncio
async def test_restore_version_creates_new_draft_from_history(
    db_session: AsyncSession, project: Project
):
    cartography = await cartography_service.ensure_default_cartography(db_session, project)
    entity_v1 = await _create_entity(db_session, project.id, "metier", "Contenu v1")
    v1 = await cartography_service.get_current_version(db_session, cartography)

    # v1.0 est validée (figée) — son contenu ne sera plus jamais modifié.
    await cartography_service.validate_cartography(db_session, cartography.id, validated_by="RSSI")

    # Toute édition ultérieure bascule automatiquement sur une v1.1 brouillon
    # (copie de v1.0) : on y supprime le contenu pour simuler une divergence.
    cartography, v1_1, id_map = await cartography_service.resolve_editable_version(
        db_session, project.id, cartography.id
    )
    copied_entity = await db_session.get(UrbanismEntity, id_map[entity_v1.id])
    await db_session.delete(copied_entity)
    await db_session.commit()

    graph_before_restore = await get_project_cartography(db_session, project.id, cartography_id=cartography.id)
    assert graph_before_restore["nodes"] == []

    restored = await cartography_service.restore_version(
        db_session, cartography.id, v1.id, author="Mamadou"
    )
    assert restored.version == "1.2"
    assert restored.status == "draft"
    graph_after_restore = await get_project_cartography(db_session, project.id, cartography_id=cartography.id)
    assert any(n["label"] == "Contenu v1" for n in graph_after_restore["nodes"])

    history = await cartography_service.get_cartography_history(db_session, cartography.id)
    assert any(h.action == "restored" for h in history)


@pytest.mark.asyncio
async def test_duplicate_cartography_is_fully_independent(
    db_session: AsyncSession, project: Project
):
    source = await cartography_service.create_cartography(
        db_session, project.id, name="Urbanisme Technique", type_="urbanisme_technique",
        description=None, author=None,
    )
    await _create_entity(db_session, project.id, "metier", "Objet original")

    clone = await cartography_service.duplicate_cartography(
        db_session, source.id, name="Architecture Technique 2028", author="Mamadou"
    )
    assert clone.id != source.id
    assert clone.name == "Architecture Technique 2028"
    assert clone.status == "draft"
    assert clone.version == "1.0"

    clone_graph = await get_project_cartography(db_session, project.id, cartography_id=clone.id)
    assert any(n["label"] == "Objet original" for n in clone_graph["nodes"])

    # Modifier le clone ne doit pas affecter la source.
    clone_version = await cartography_service.get_current_version(db_session, clone)
    clone_entity = (
        await db_session.execute(
            select(UrbanismEntity).where(UrbanismEntity.cartography_version_id == clone_version.id)
        )
    ).scalars().first()
    clone_entity.label = "Objet modifié dans le clone"
    await db_session.commit()

    source_graph = await get_project_cartography(db_session, project.id, cartography_id=source.id)
    assert any(n["label"] == "Objet original" for n in source_graph["nodes"])
    assert not any(n["label"] == "Objet modifié dans le clone" for n in source_graph["nodes"])


@pytest.mark.asyncio
async def test_archive_and_unarchive_cartography(db_session: AsyncSession, project: Project):
    cartography = await cartography_service.create_cartography(
        db_session, project.id, name="Cloud", type_="cloud", description=None, author=None
    )
    archived = await cartography_service.archive_cartography(db_session, cartography.id, author="Admin")
    assert archived.is_archived is True
    assert archived.status == "archived"
    assert archived.is_active is False

    unarchived = await cartography_service.unarchive_cartography(
        db_session, cartography.id, author="Admin"
    )
    assert unarchived.is_archived is False
    assert unarchived.status == "draft"


@pytest.mark.asyncio
async def test_submit_for_validation_then_validate(db_session: AsyncSession, project: Project):
    cartography = await cartography_service.ensure_default_cartography(db_session, project)
    submitted = await cartography_service.submit_for_validation(db_session, cartography.id, author="Mamadou")
    assert submitted.status == "in_validation"

    validated = await cartography_service.validate_cartography(
        db_session, cartography.id, validated_by="RSSI", comment="OK"
    )
    assert validated.status == "validated"
    assert validated.validated_by == "RSSI"
    assert validated.validated_at is not None


@pytest.mark.asyncio
async def test_history_records_action_author_comment_version(
    db_session: AsyncSession, project: Project
):
    cartography = await cartography_service.ensure_default_cartography(db_session, project)
    await cartography_service.update_cartography(
        db_session, cartography.id, name="Renommée", author="Mamadou"
    )
    history = await cartography_service.get_cartography_history(db_session, cartography.id)
    entry = next(h for h in history if h.action == "updated")
    assert entry.version == "1.0"
    assert entry.author == "Mamadou"
    assert isinstance(entry, CartographyHistory)


# ————————————————————————————————————————————————————————————————
# API REST
# ————————————————————————————————————————————————————————————————


@pytest_asyncio.fixture
async def client(db_session: AsyncSession):
    async def override_get_db():
        yield db_session

    fastapi_app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    fastapi_app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_api_crud_cartographies(client: AsyncClient, project: Project):
    res = await client.get(f"/api/projects/{project.id}/cartographies")
    assert res.status_code == 200
    assert res.json()["total"] == 1  # cartographie par défaut auto-provisionnée

    res = await client.post(
        f"/api/projects/{project.id}/cartographies",
        json={"name": "Urbanisme Applicatif", "type": "urbanisme_applicatif", "description": "Test"},
    )
    assert res.status_code == 201
    created = res.json()
    assert created["is_active"] is True
    cartography_id = created["id"]

    res = await client.get(f"/api/cartographies/{cartography_id}")
    assert res.status_code == 200
    assert res.json()["name"] == "Urbanisme Applicatif"

    res = await client.put(f"/api/cartographies/{cartography_id}", json={"name": "Renommé"})
    assert res.status_code == 200
    assert res.json()["name"] == "Renommé"

    res = await client.delete(f"/api/cartographies/{cartography_id}")
    assert res.status_code == 204

    res = await client.get(f"/api/cartographies/{cartography_id}")
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_api_versioning_lifecycle(client: AsyncClient, project: Project):
    res = await client.post(
        f"/api/projects/{project.id}/cartographies",
        json={"name": "Urbanisme Technique", "type": "urbanisme_technique"},
    )
    cartography_id = res.json()["id"]

    res = await client.post(
        f"/api/projects/{project.id}/urbanism/entities",
        params={"cartography_id": cartography_id},
        json={"entity_type": "metier", "label": "Processus métier X"},
    )
    assert res.status_code == 201

    res = await client.post(f"/api/cartographies/{cartography_id}/validate", json={"validated_by": "RSSI"})
    assert res.status_code == 200
    assert res.json()["status"] == "validated"

    res = await client.get(f"/api/cartographies/{cartography_id}/versions")
    assert len(res.json()["items"]) == 1

    # Modifier après validation → nouvelle version brouillon automatique (v1.1).
    res = await client.post(
        f"/api/projects/{project.id}/urbanism/entities",
        params={"cartography_id": cartography_id},
        json={"entity_type": "metier", "label": "Processus métier Y"},
    )
    assert res.status_code == 201

    res = await client.get(f"/api/cartographies/{cartography_id}")
    assert res.json()["version"] == "1.1"
    assert res.json()["status"] == "draft"

    res = await client.get(f"/api/cartographies/{cartography_id}/versions")
    versions = res.json()["items"]
    assert {v["version"] for v in versions} == {"1.0", "1.1"}

    res = await client.get(f"/api/cartographies/{cartography_id}/history")
    actions = {h["action"] for h in res.json()["items"]}
    assert "new_version" in actions
    assert "validated" in actions


@pytest.mark.asyncio
async def test_api_duplicate_and_restore(client: AsyncClient, project: Project):
    res = await client.post(
        f"/api/projects/{project.id}/cartographies",
        json={"name": "Réseau", "type": "reseau"},
    )
    cartography_id = res.json()["id"]

    res = await client.post(
        f"/api/cartographies/{cartography_id}/duplicate",
        json={"name": "Réseau 2028"},
    )
    assert res.status_code == 200
    clone = res.json()
    assert clone["name"] == "Réseau 2028"
    assert clone["id"] != cartography_id

    res = await client.get(f"/api/cartographies/{cartography_id}/versions")
    version_id = res.json()["items"][0]["id"]

    res = await client.post(
        f"/api/cartographies/{cartography_id}/restore",
        json={"version_id": version_id, "author": "Mamadou"},
    )
    assert res.status_code == 200
    assert res.json()["version"] == "1.1"


@pytest.mark.asyncio
async def test_api_new_cartography_starts_with_empty_graph(client: AsyncClient, project: Project):
    res = await client.post(
        f"/api/projects/{project.id}/cartographies",
        json={"name": "Libre", "type": "libre"},
    )
    cartography_id = res.json()["id"]
    res = await client.get(
        f"/api/projects/{project.id}/urbanism/graph", params={"cartography_id": cartography_id}
    )
    assert res.status_code == 200
    body = res.json()
    assert body["nodes"] == []
    assert body["cartography"]["id"] == cartography_id
    assert body["cartography_version"]["version"] == "1.0"


@pytest.mark.asyncio
async def test_api_activate_cartography_switches_active_flag(
    client: AsyncClient, project: Project
):
    res = await client.get(f"/api/projects/{project.id}/cartographies")
    default_id = res.json()["items"][0]["id"]

    res = await client.post(
        f"/api/projects/{project.id}/cartographies",
        json={"name": "Cybersécurité", "type": "cybersecurite"},
    )
    other_id = res.json()["id"]
    assert res.json()["is_active"] is True  # devient active à la création (§3)

    res = await client.post(f"/api/cartographies/{default_id}/activate")
    assert res.status_code == 200
    assert res.json()["is_active"] is True

    res = await client.get(f"/api/cartographies/{other_id}")
    assert res.json()["is_active"] is False


@pytest.mark.asyncio
async def test_api_graph_by_version_id_is_read_only_snapshot(
    client: AsyncClient, project: Project
):
    """Le sélecteur de version du bandeau doit pouvoir consulter une ancienne
    version figée sans déclencher de copie-sur-écriture (lecture seule)."""
    res = await client.post(
        f"/api/projects/{project.id}/cartographies",
        json={"name": "Urbanisme Technique", "type": "urbanisme_technique"},
    )
    cartography_id = res.json()["id"]

    res = await client.post(
        f"/api/projects/{project.id}/urbanism/entities",
        params={"cartography_id": cartography_id},
        json={"entity_type": "metier", "label": "V1 objet"},
    )
    assert res.status_code == 201

    res = await client.get(f"/api/cartographies/{cartography_id}/versions")
    v1_id = res.json()["items"][0]["id"]

    res = await client.post(f"/api/cartographies/{cartography_id}/validate", json={})
    assert res.status_code == 200

    # Nouvelle modification → v1.1 en brouillon, v1.0 reste figée et consultable.
    res = await client.post(
        f"/api/projects/{project.id}/urbanism/entities",
        params={"cartography_id": cartography_id},
        json={"entity_type": "metier", "label": "V1.1 objet"},
    )
    assert res.status_code == 201

    res = await client.get(
        f"/api/projects/{project.id}/urbanism/graph", params={"version_id": v1_id}
    )
    assert res.status_code == 200
    body = res.json()
    assert body["cartography_version"]["version"] == "1.0"
    labels = {n["label"] for n in body["nodes"]}
    assert labels == {"V1 objet"}

    res = await client.get(f"/api/cartographies/{cartography_id}")
    assert res.json()["version"] == "1.1"


# ————————————————————————————————————————————————————————————————
# Import scoping (§12) — n'écrase jamais les autres cartographies
# ————————————————————————————————————————————————————————————————


@pytest.mark.asyncio
async def test_import_targets_only_selected_cartography(db_session: AsyncSession, project: Project):
    from app.services.urbanism_import import ImportMode, execute_import
    from app.services.urbanism_import.template_generator import generate_official_template

    cart_a = await cartography_service.ensure_default_cartography(db_session, project)
    await _create_entity(db_session, project.id, "metier", "Ne doit pas bouger")

    cart_b = await cartography_service.create_cartography(
        db_session, project.id, name="Cible import", type_="libre", description=None, author=None
    )

    template = generate_official_template()
    await execute_import(
        db_session, project.id, template, "modele.xlsx", ImportMode.MERGE, cartography_id=cart_b.id
    )

    graph_a = await get_project_cartography(db_session, project.id, cartography_id=cart_a.id)
    graph_b = await get_project_cartography(db_session, project.id, cartography_id=cart_b.id)
    assert any(n["label"] == "Ne doit pas bouger" for n in graph_a["nodes"])
    assert len(graph_b["nodes"]) > 0
    assert not any(n["label"] == "Ne doit pas bouger" for n in graph_b["nodes"])
