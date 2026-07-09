"""Écriture des entités urbanisme depuis l'import."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.metamodel.urbanism import get_entity_meta
from app.models.entities import UrbanismEntity, UrbanismRelation
from app.services.urbanism_entity_utils import find_entity_by_normalized_label, normalize_label, set_assistant_derived_link
from app.services.urbanism_import.types import ImportMode, ImportRow


IMPORT_ID_KEY = "_import_id"


async def clear_project_cartography(
    db: AsyncSession, project_id: UUID, cartography_version_id: UUID | None = None
) -> None:
    """Vide le graphe — scope à une version de cartographie si fournie (§12),
    sinon (compat. historique) l'ensemble du projet."""
    rel_stmt = delete(UrbanismRelation).where(UrbanismRelation.project_id == project_id)
    entity_stmt = delete(UrbanismEntity).where(UrbanismEntity.project_id == project_id)
    if cartography_version_id is not None:
        rel_stmt = rel_stmt.where(UrbanismRelation.cartography_version_id == cartography_version_id)
        entity_stmt = entity_stmt.where(
            UrbanismEntity.cartography_version_id == cartography_version_id
        )
    await db.execute(rel_stmt)
    await db.execute(entity_stmt)


async def load_existing_entities(
    db: AsyncSession, project_id: UUID, cartography_version_id: UUID | None = None
) -> list[UrbanismEntity]:
    stmt = select(UrbanismEntity).where(UrbanismEntity.project_id == project_id)
    if cartography_version_id is not None:
        stmt = stmt.where(UrbanismEntity.cartography_version_id == cartography_version_id)
    result = await db.execute(stmt)
    return list(result.scalars().all())


def build_lookup(entities: list[UrbanismEntity]) -> dict[tuple[str, str], UUID]:
    lookup: dict[tuple[str, str], UUID] = {}
    for entity in entities:
        props = entity.properties or {}
        import_id = props.get(IMPORT_ID_KEY)
        if import_id:
            lookup[(entity.entity_type, str(import_id).lower())] = entity.id
        lookup[(entity.entity_type, normalize_label(entity.label))] = entity.id
        lookup[(entity.entity_type, entity.label.strip().lower())] = entity.id
    return lookup


async def upsert_entities(
    db: AsyncSession,
    project_id: UUID,
    rows: list[ImportRow],
    mode: ImportMode,
    existing: list[UrbanismEntity],
    cartography_version_id: UUID | None = None,
) -> tuple[list[UrbanismEntity], dict[str, int], dict[str, int]]:
    created: dict[str, int] = {}
    updated: dict[str, int] = {}
    entities = list(existing)
    lookup = build_lookup(entities)
    access_posts: list[tuple[str, str]] = []

    for row in rows:
        if row.entity_type == "_technique_link":
            app_ref = row.parent_refs.get("ilot_applicatif")
            if app_ref:
                access_posts.append((f"__access__{app_ref}", app_ref))
            continue

        meta = get_entity_meta(row.entity_type)
        if not meta:
            continue

        props = dict(row.properties)
        props[IMPORT_ID_KEY] = row.external_id
        props["_import_sheet"] = row.sheet

        existing_entity = lookup.get((row.entity_type, row.external_id.lower()))
        if not existing_entity:
            match = find_entity_by_normalized_label(entities, row.entity_type, row.label)
            if match:
                existing_entity = match.id

        if existing_entity:
            entity = await db.get(UrbanismEntity, existing_entity)
            if entity:
                entity.label = row.label.strip()
                entity.description = row.description
                merged = dict(entity.properties or {})
                merged.update(props)
                entity.properties = merged
                updated[row.entity_type] = updated.get(row.entity_type, 0) + 1
                lookup[(row.entity_type, row.external_id.lower())] = entity.id
                lookup[(row.entity_type, normalize_label(row.label))] = entity.id
                if row.entity_type == "ilot_applicatif":
                    parent = row.parent_refs.get("ilot_fonctionnel")
                    if parent:
                        parent_id = lookup.get(("ilot_fonctionnel", parent.lower()))
                        if parent_id:
                            set_assistant_derived_link(entity, ilot_fonctionnel_id=parent_id)
                continue

        entity = UrbanismEntity(
            project_id=project_id,
            cartography_version_id=cartography_version_id,
            entity_type=row.entity_type,
            couche=meta["couche"],
            label=row.label.strip(),
            description=row.description,
            properties=props,
        )
        db.add(entity)
        await db.flush()
        entities.append(entity)
        created[row.entity_type] = created.get(row.entity_type, 0) + 1
        lookup[(row.entity_type, row.external_id.lower())] = entity.id
        lookup[(row.entity_type, normalize_label(row.label))] = entity.id
        if row.entity_type == "ilot_applicatif":
            parent = row.parent_refs.get("ilot_fonctionnel")
            if parent:
                parent_id = lookup.get(("ilot_fonctionnel", parent.lower()))
                if parent_id:
                    set_assistant_derived_link(entity, ilot_fonctionnel_id=parent_id)

    for access_id, app_ref in access_posts:
        if ( "poste_travail", access_id.lower()) in lookup:
            continue
        meta = get_entity_meta("poste_travail")
        if not meta:
            continue
        label = f"Accès {app_ref}"
        entity = UrbanismEntity(
            project_id=project_id,
            cartography_version_id=cartography_version_id,
            entity_type="poste_travail",
            couche=meta["couche"],
            label=label,
            description="Poste d'accès généré automatiquement à l'import",
            properties={IMPORT_ID_KEY: access_id, "_import_generated": True},
        )
        db.add(entity)
        await db.flush()
        entities.append(entity)
        created["poste_travail"] = created.get("poste_travail", 0) + 1
        lookup[("poste_travail", access_id.lower())] = entity.id

    return entities, created, updated
