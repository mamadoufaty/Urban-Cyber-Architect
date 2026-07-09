"""Fusion des doublons urbanisme — (project_id, entity_type, normalized_label)."""

from __future__ import annotations

from collections import defaultdict
from typing import Any
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.metamodel.urbanism import validate_relation
from app.models.entities import UrbanismEntity, UrbanismRelation
from app.services.urbanism_engine import _analyze_graph
from app.services.urbanism_entity_utils import entity_dedup_key, pick_canonical_entity


def _relation_tuple(rel: UrbanismRelation) -> tuple[UUID, str, UUID]:
    return (rel.source_id, rel.relation_type, rel.target_id)


def _scope_stmt(model, project_id: UUID, cartography_version_id: UUID | None):
    stmt = select(model).where(model.project_id == project_id)
    if cartography_version_id is not None:
        stmt = stmt.where(model.cartography_version_id == cartography_version_id)
    return stmt


async def _purge_non_official_relations(
    session: AsyncSession,
    project_id: UUID,
    entities: list[UrbanismEntity],
    relations: list[UrbanismRelation],
) -> int:
    """Supprime les relations hors métamodèle R01–R30 (ex. ancienne R31)."""
    emap = {e.id: e for e in entities}
    removed = 0
    for rel in list(relations):
        src = emap.get(rel.source_id)
        tgt = emap.get(rel.target_id)
        if not src or not tgt:
            continue
        if not validate_relation(src.entity_type, rel.relation_type, tgt.entity_type):
            await session.delete(rel)
            relations.remove(rel)
            removed += 1
    if removed:
        await session.commit()
    return removed


async def deduplicate_project(
    session: AsyncSession,
    project_id: UUID,
    cartography_version_id: UUID | None = None,
) -> dict[str, Any]:
    entities = list(
        (await session.execute(
            _scope_stmt(UrbanismEntity, project_id, cartography_version_id)
        )).scalars()
    )
    relations = list(
        (await session.execute(
            _scope_stmt(UrbanismRelation, project_id, cartography_version_id)
        )).scalars()
    )

    await _purge_non_official_relations(session, project_id, entities, relations)
    entities = list(
        (await session.execute(
            _scope_stmt(UrbanismEntity, project_id, cartography_version_id)
        )).scalars()
    )
    relations = list(
        (await session.execute(
            _scope_stmt(UrbanismRelation, project_id, cartography_version_id)
        )).scalars()
    )

    groups: dict[tuple[str, str], list[UrbanismEntity]] = defaultdict(list)
    for entity in entities:
        groups[entity_dedup_key(entity)].append(entity)

    entities_removed = 0
    relations_relocated = 0
    merged_groups = 0
    remove_ids: list[UUID] = []

    for group in groups.values():
        if len(group) < 2:
            continue
        merged_groups += 1
        keeper = pick_canonical_entity(group, relations)
        for duplicate in group:
            if duplicate.id == keeper.id:
                continue
            for rel in relations:
                changed = False
                if rel.source_id == duplicate.id:
                    rel.source_id = keeper.id
                    changed = True
                if rel.target_id == duplicate.id:
                    rel.target_id = keeper.id
                    changed = True
                if changed:
                    relations_relocated += 1
            remove_ids.append(duplicate.id)
            entities_removed += 1

    if not remove_ids:
        return {
            "merged_groups": 0,
            "entities_removed": 0,
            "relations_relocated": 0,
            "analysis": _analyze_graph(entities, relations),
        }

    seen_relations: set[tuple[UUID, str, UUID]] = set()
    duplicate_rel_ids: list[UUID] = []
    for rel in relations:
        key = _relation_tuple(rel)
        if key in seen_relations:
            duplicate_rel_ids.append(rel.id)
        else:
            seen_relations.add(key)

    if duplicate_rel_ids:
        await session.execute(
            delete(UrbanismRelation).where(UrbanismRelation.id.in_(duplicate_rel_ids))
        )

    await session.execute(
        delete(UrbanismEntity).where(UrbanismEntity.id.in_(remove_ids))
    )
    await session.commit()

    entities = list(
        (await session.execute(
            _scope_stmt(UrbanismEntity, project_id, cartography_version_id)
        )).scalars()
    )
    relations = list(
        (await session.execute(
            _scope_stmt(UrbanismRelation, project_id, cartography_version_id)
        )).scalars()
    )

    return {
        "merged_groups": merged_groups,
        "entities_removed": entities_removed,
        "relations_relocated": relations_relocated,
        "analysis": _analyze_graph(entities, relations),
    }
