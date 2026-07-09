"""Urbanism engine — graph construction, validation, cartography from persisted relations."""

import logging
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.urbanism_canonical_layout import compute_canonical_positions
from app.services.urbanism_entity_layout import get_entity_layout, resolve_entity_position
from app.services.urbanism_entity_utils import normalize_label, resolve_entity_couche
from app.services.urbanism_derived_edges import build_derived_edges
from app.services.urbanism_edge_layout import get_derived_edge_layout, get_relation_layout
from app.metamodel.urbanism import (
    COUCHE_COLORS,
    COUCHE_LABELS,
    RELATION_CATEGORIES,
    RELATION_RULES,
    get_entity_meta,
    validate_relation,
)
from app.models.entities import Project, UrbanismEntity, UrbanismRelation

COUCHE_ORDER = ["metier", "organisation", "fonctionnel", "applicatif", "technique", "transverse"]

logger = logging.getLogger(__name__)

BAND_HEIGHT = 200
BAND_GAP = 28
NODE_WIDTH = 200
NODE_HEIGHT = 72
NODE_GAP = 14
BAND_LABEL_W = 150
COL_WIDTH = 220


def _category_for_relation(source_type: str, relation_type: str, target_type: str) -> str:
    for rule in RELATION_RULES:
        if rule["source"] == source_type and rule["type"] == relation_type and rule["target"] == target_type:
            return rule["category"]
    return "metier"


R05_RELATION_TYPE = "est pris en compte dans"


def _metier_scope(
    metier_id: UUID,
    relations: list[UrbanismRelation],
) -> tuple[list[UUID], list[UUID]]:
    """Objectifs (R02) et processus (R03) rattachés au même métier."""
    objectif_ids = [
        r.target_id
        for r in relations
        if r.source_id == metier_id and r.relation_type == "définit"
    ]
    processus_ids = [
        r.target_id
        for r in relations
        if r.source_id == metier_id and r.relation_type == "pilote"
    ]
    return objectif_ids, processus_ids


async def sync_missing_r05_relations(
    session: AsyncSession,
    project_id: UUID,
    entities: list[UrbanismEntity],
    relations: list[UrbanismRelation],
    cartography_version_id: UUID | None = None,
) -> list[UrbanismRelation]:
    """Crée R05 manquante pour le triangle canonique Métier → Objectif / Processus (1:1)."""
    entity_map = {e.id: e for e in entities}
    existing_r05 = {
        (r.source_id, r.target_id)
        for r in relations
        if r.relation_type == R05_RELATION_TYPE
    }
    created: list[UrbanismRelation] = []

    for metier in (e for e in entities if e.entity_type == "metier"):
        objectif_ids, processus_ids = _metier_scope(metier.id, relations)
        if len(objectif_ids) != 1 or len(processus_ids) != 1:
            continue

        objectif_id = objectif_ids[0]
        processus_id = processus_ids[0]
        if (objectif_id, processus_id) in existing_r05:
            continue

        objectif = entity_map.get(objectif_id)
        processus = entity_map.get(processus_id)
        if not objectif or not processus:
            continue
        if objectif.entity_type != "objectif" or processus.entity_type != "processus":
            continue
        if not validate_relation("objectif", R05_RELATION_TYPE, "processus"):
            continue

        rel = UrbanismRelation(
            project_id=project_id,
            cartography_version_id=cartography_version_id,
            source_id=objectif_id,
            target_id=processus_id,
            relation_type=R05_RELATION_TYPE,
            category=_category_for_relation("objectif", R05_RELATION_TYPE, "processus"),
        )
        session.add(rel)
        created.append(rel)
        existing_r05.add((objectif_id, processus_id))

    if created:
        await session.commit()
        for rel in created:
            await session.refresh(rel)

    return created


async def build_cartography(
    session: AsyncSession,
    project: Project,
    relation_categories: list[str] | None = None,
    cartography_version_id: UUID | None = None,
) -> dict[str, Any]:
    entity_stmt = select(UrbanismEntity).where(UrbanismEntity.project_id == project.id)
    relation_stmt = select(UrbanismRelation).where(UrbanismRelation.project_id == project.id)
    if cartography_version_id is not None:
        entity_stmt = entity_stmt.where(
            UrbanismEntity.cartography_version_id == cartography_version_id
        )
        relation_stmt = relation_stmt.where(
            UrbanismRelation.cartography_version_id == cartography_version_id
        )

    entities_result = await session.execute(entity_stmt)
    entities = list(entities_result.scalars().all())

    relations_result = await session.execute(relation_stmt)
    all_relations = list(relations_result.scalars().all())

    synced = await sync_missing_r05_relations(
        session, project.id, entities, all_relations, cartography_version_id
    )
    if synced:
        all_relations = all_relations + synced

    if relation_categories:
        relations = [r for r in all_relations if r.category in relation_categories]
    else:
        relations = all_relations

    entity_ids_in_view = {e.id for e in entities}
    for r in relations:
        entity_ids_in_view.add(r.source_id)
        entity_ids_in_view.add(r.target_id)

    visible_entities = list(entities)

    raw_nodes = [
        {
            "id": str(entity.id),
            "entity_type": entity.entity_type,
            "couche": entity.couche,
            "label": entity.label,
        }
        for entity in visible_entities
        if not get_entity_layout(entity.properties)
    ]
    positions, _band_heights = compute_canonical_positions(raw_nodes)

    nodes = []
    for entity in visible_entities:
        meta = get_entity_meta(entity.entity_type) or {}
        canonical_couche = resolve_entity_couche(entity.entity_type, entity.couche)
        canonical = positions.get(str(entity.id), {"x": 0, "y": 0})
        pos, layout = resolve_entity_position(entity, canonical)
        nodes.append(
            {
                "id": str(entity.id),
                "type": "urbanism",
                "entity_type": entity.entity_type,
                "entity_type_label": meta.get("label", entity.entity_type),
                "couche": canonical_couche,
                "couche_label": COUCHE_LABELS.get(canonical_couche, canonical_couche),
                "couche_color": COUCHE_COLORS.get(canonical_couche, "#64748b"),
                "label": entity.label,
                "position": pos,
                "layout": layout,
            }
        )
        logger.info(
            "cartography.node id=%s type=%s couche=%s position=%s,%s label=%s",
            str(entity.id),
            entity.entity_type,
            canonical_couche,
            pos["x"],
            pos["y"],
            entity.label,
        )

    persisted_edges = [
        {
            "id": str(rel.id),
            "source": str(rel.source_id),
            "target": str(rel.target_id),
            "relation_type": rel.relation_type,
            "category": rel.category,
            "criticite": rel.criticite,
            "commentaire": rel.commentaire,
            "derived": False,
            "layout": get_relation_layout(rel.properties),
        }
        for rel in relations
    ]
    derived_edges = build_derived_edges(entities, all_relations)
    edges = persisted_edges + derived_edges

    for edge in edges:
        logger.info(
            "cartography.edge id=%s source=%s target=%s derived=%s type=%s",
            edge["id"],
            edge["source"],
            edge["target"],
            edge.get("derived", False),
            edge.get("relation_type"),
        )

    analysis = _analyze_graph(entities, all_relations, derived_edges)
    org = project.organization or {}

    by_couche = {
        c: sum(1 for e in entities if resolve_entity_couche(e.entity_type, e.couche) == c)
        for c in COUCHE_ORDER
    }
    by_relation_type: dict[str, int] = {}
    for r in all_relations:
        by_relation_type[r.relation_type] = by_relation_type.get(r.relation_type, 0) + 1

    meta_layers = [
        {
            "id": c,
            "label": COUCHE_LABELS[c],
            "color": COUCHE_COLORS[c],
            "object_count": by_couche.get(c, 0),
        }
        for c in COUCHE_ORDER
    ]

    return {
        "project_id": str(project.id),
        "project_name": project.name,
        "cartography_version_id": str(cartography_version_id) if cartography_version_id else None,
        "organization": org,
        "author": org.get("author") or org.get("name") or "Urban Cyber Architect",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "model": "club_urba_metamodel",
        "nodes": nodes,
        "edges": edges,
        "meta_layers": meta_layers,
        "stats": {
            "total_objects": len(entities),
            "total_relations": len(all_relations),
            "visible_objects": len(visible_entities),
            "visible_relations": len(relations) + len(derived_edges),
            "by_couche": by_couche,
            "by_relation_type": by_relation_type,
        },
        "analysis": analysis,
        "relation_categories": RELATION_CATEGORIES,
        "relation_type_legend": sorted(by_relation_type.keys()),
    }


def _compute_positions(
    entities: list[UrbanismEntity], relations: list[UrbanismRelation]
) -> dict[str, dict[str, float]]:
    """Layout par couche avec répartition horizontale selon le degré entrant."""
    positions: dict[str, dict[str, float]] = {}
    by_couche: dict[str, list[UrbanismEntity]] = {c: [] for c in COUCHE_ORDER}

    for e in entities:
        couche = resolve_entity_couche(e.entity_type, e.couche)
        if couche in by_couche:
            by_couche[couche].append(e)

    in_degree: dict[str, int] = {str(e.id): 0 for e in entities}
    for r in relations:
        tid = str(r.target_id)
        in_degree[tid] = in_degree.get(tid, 0) + 1

    for band_idx, couche in enumerate(COUCHE_ORDER):
        band_entities = sorted(
            by_couche[couche],
            key=lambda e: (in_degree.get(str(e.id), 0), e.label.lower()),
        )
        band_y = band_idx * (BAND_HEIGHT + BAND_GAP)
        count = max(len(band_entities), 1)
        for i, entity in enumerate(band_entities):
            col = i % 4
            row = i // 4
            positions[str(entity.id)] = {
                "x": BAND_LABEL_W + col * COL_WIDTH,
                "y": band_y + 40 + row * (NODE_HEIGHT + NODE_GAP),
            }

    return positions


def _analyze_graph(
    entities: list[UrbanismEntity],
    relations: list[UrbanismRelation],
    derived_edges: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    if derived_edges is None:
        derived_edges = build_derived_edges(entities, relations)

    connected: set[UUID] = set()
    for r in relations:
        connected.add(r.source_id)
        connected.add(r.target_id)
    for edge in derived_edges:
        connected.add(UUID(edge["source"]))
        connected.add(UUID(edge["target"]))

    orphans = [
        {"id": str(e.id), "label": e.label, "entity_type": e.entity_type, "couche": e.couche}
        for e in entities
        if e.id not in connected
    ]

    seen_orphan_keys: set[tuple[str, str]] = set()
    deduped_orphans: list[dict[str, str]] = []
    for orphan in orphans:
        key = (orphan["entity_type"], normalize_label(orphan["label"]))
        if key in seen_orphan_keys:
            continue
        seen_orphan_keys.add(key)
        deduped_orphans.append(orphan)

    critical_relations = [
        {
            "id": str(r.id),
            "relation_type": r.relation_type,
            "source_id": str(r.source_id),
            "target_id": str(r.target_id),
            "criticite": r.criticite,
        }
        for r in relations
        if r.criticite in ("élevée", "critique")
    ]

    entity_map = {e.id: e for e in entities}
    inconsistencies: list[dict[str, str]] = []

    for r in relations:
        src = entity_map.get(r.source_id)
        tgt = entity_map.get(r.target_id)
        if not src or not tgt:
            inconsistencies.append({"issue": "relation_orpheline", "relation_id": str(r.id)})
            continue
        if not validate_relation(src.entity_type, r.relation_type, tgt.entity_type):
            inconsistencies.append(
                {
                    "issue": "relation_invalide",
                    "relation_id": str(r.id),
                    "detail": f"{src.entity_type} —{r.relation_type}→ {tgt.entity_type}",
                }
            )

    isolated_couches = []
    for c in COUCHE_ORDER:
        couche_entities = [
            e for e in entities if resolve_entity_couche(e.entity_type, e.couche) == c
        ]
        if not couche_entities:
            continue
        couche_entity_ids = {e.id for e in couche_entities}
        has_couche_relation = any(
            r.source_id in couche_entity_ids or r.target_id in couche_entity_ids
            for r in relations
        )
        has_derived_couche_relation = any(
            UUID(edge["source"]) in couche_entity_ids or UUID(edge["target"]) in couche_entity_ids
            for edge in derived_edges
        )
        if not has_couche_relation and not has_derived_couche_relation:
            isolated_couches.append(c)

    return {
        "orphans": deduped_orphans,
        "orphan_count": len(deduped_orphans),
        "critical_relations": critical_relations,
        "critical_count": len(critical_relations),
        "inconsistencies": inconsistencies,
        "inconsistency_count": len(inconsistencies),
        "isolated_couches": isolated_couches,
    }


async def get_project_cartography(
    session: AsyncSession,
    project_id: UUID,
    categories: list[str] | None = None,
    cartography_id: UUID | None = None,
    version_id: UUID | None = None,
) -> dict[str, Any] | None:
    from app.services import cartography_service

    project = await session.get(Project, project_id)
    if not project:
        return None
    if version_id is not None:
        cartography, version = await cartography_service.get_version_or_404(session, version_id)
        if cartography.project_id != project_id:
            raise cartography_service.CartographyError(
                "Cette version n'appartient pas au projet"
            )
    else:
        cartography, version = await cartography_service.resolve_read_version(
            session, project_id, cartography_id
        )
    graph = await build_cartography(session, project, categories, version.id)
    graph["cartography"] = {
        "id": str(cartography.id),
        "name": cartography.name,
        "type": cartography.type,
        "status": cartography.status,
        "is_active": cartography.is_active,
        "is_archived": cartography.is_archived,
    }
    graph["cartography_version"] = {
        "id": str(version.id),
        "version": version.version,
        "status": version.status,
        "is_current": version.is_current,
    }
    return graph
