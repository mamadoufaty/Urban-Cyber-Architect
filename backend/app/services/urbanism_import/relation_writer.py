"""Écriture des relations urbanisme depuis l'import."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import UrbanismEntity, UrbanismRelation
from app.services.urbanism_engine import _category_for_relation
from app.services.urbanism_import.relation_builder import PlannedRelation, is_valid_metamodel_relation, resolve_entity_id
from app.services.urbanism_import.types import ImportIssue, ImportErrorCode


async def create_relations(
    db: AsyncSession,
    project_id: UUID,
    planned: list[PlannedRelation],
    lookup: dict[tuple[str, str], UUID],
    existing_relations: list[UrbanismRelation],
    cartography_version_id: UUID | None = None,
) -> tuple[int, list[ImportIssue]]:
    issues: list[ImportIssue] = []
    created = 0
    existing_keys = {
        (r.source_id, r.relation_type, r.target_id) for r in existing_relations
    }

    for rel in planned:
        if rel.relation_type.startswith("__"):
            continue
        if not is_valid_metamodel_relation(rel):
            issues.append(
                ImportIssue(
                    code=ImportErrorCode.INVALID_RELATION,
                    message=(
                        f"Relation impossible : {rel.source_type} —{rel.relation_type}→ "
                        f"{rel.target_type} ({rel.source_ref} → {rel.target_ref})"
                    ),
                )
            )
            continue

        source_id = resolve_entity_id(lookup, rel.source_type, rel.source_ref)
        target_id = resolve_entity_id(lookup, rel.target_type, rel.target_ref)
        if not source_id or not target_id:
            issues.append(
                ImportIssue(
                    code=ImportErrorCode.UNKNOWN_REFERENCE,
                    message=f"Référence introuvable pour relation {rel.source_ref} → {rel.target_ref}",
                )
            )
            continue

        key = (source_id, rel.relation_type, target_id)
        if key in existing_keys:
            continue

        relation = UrbanismRelation(
            project_id=project_id,
            cartography_version_id=cartography_version_id,
            source_id=source_id,
            target_id=target_id,
            relation_type=rel.relation_type,
            category=_category_for_relation(rel.source_type, rel.relation_type, rel.target_type),
            commentaire=rel.commentaire,
            criticite=rel.criticite,
            properties={"_import": True},
        )
        db.add(relation)
        existing_keys.add(key)
        created += 1

    return created, issues


async def store_flux_on_applications(
    db: AsyncSession,
    flux_rows: list[dict],
    lookup: dict[tuple[str, str], UUID],
) -> int:
    stored = 0
    for flux in flux_rows:
        source_id = resolve_entity_id(lookup, "ilot_applicatif", flux["source"])
        if not source_id:
            continue
        entity = await db.get(UrbanismEntity, source_id)
        if not entity:
            continue
        props = dict(entity.properties or {})
        flux_list = list(props.get("import_flux") or [])
        flux_list.append(
            {
                "destination": flux["destination"],
                "type": flux.get("type"),
                "protocol": flux.get("protocol"),
                "description": flux.get("description"),
            }
        )
        props["import_flux"] = flux_list
        entity.properties = props
        stored += 1
    return stored


async def load_existing_relations(
    db: AsyncSession, project_id: UUID, cartography_version_id: UUID | None = None
) -> list[UrbanismRelation]:
    stmt = select(UrbanismRelation).where(UrbanismRelation.project_id == project_id)
    if cartography_version_id is not None:
        stmt = stmt.where(UrbanismRelation.cartography_version_id == cartography_version_id)
    result = await db.execute(stmt)
    return list(result.scalars().all())
