"""Arêtes dérivées pour l'affichage — hors métamodèle officiel R01–R30."""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from app.models.entities import UrbanismEntity, UrbanismRelation
from app.services.urbanism_edge_layout import get_derived_edge_layout
from app.services.urbanism_entity_utils import ASSISTANT_DERIVED_LINKS_KEY, get_assistant_ilot_fonctionnel_id

logger = logging.getLogger(__name__)
R30_TYPE = "est mise en œuvre par"
DERIVED_FONC_APPLIC_LABEL = "est mis en œuvre par"


def _entity_map(entities: list[UrbanismEntity]) -> dict[UUID, UrbanismEntity]:
    return {e.id: e for e in entities}


def build_derived_edges(
    entities: list[UrbanismEntity],
    relations: list[UrbanismRelation],
) -> list[dict[str, Any]]:
    """Liens calculés pour la cartographie (îlot fonctionnel → îlot applicatif)."""
    emap = _entity_map(entities)
    edges: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()

    def add_edge(source_id: UUID, target_id: UUID) -> None:
        key = (str(source_id), str(target_id))
        if key in seen:
            return
        src = emap.get(source_id)
        tgt = emap.get(target_id)
        if not src or not tgt:
            return
        if src.entity_type != "ilot_fonctionnel" or tgt.entity_type != "ilot_applicatif":
            return
        seen.add(key)
        edges.append({
            "id": f"derived-fonc-applic-{source_id}-{target_id}",
            "source": str(source_id),
            "target": str(target_id),
            "relation_type": DERIVED_FONC_APPLIC_LABEL,
            "category": "derived",
            "criticite": None,
            "commentaire": "Lien dérivé (affichage)",
            "derived": True,
            "layout": get_derived_edge_layout(tgt, f"derived-fonc-applic-{source_id}-{target_id}"),
        })

    for entity in entities:
        if entity.entity_type != "ilot_applicatif":
            continue
        ilot_f_id = get_assistant_ilot_fonctionnel_id(entity)
        if ilot_f_id:
            logger.info(
                "derived_edges.assistant_link ilot_applicatif=%s ilot_fonctionnel=%s props=%s",
                entity.id,
                ilot_f_id,
                (entity.properties or {}).get(ASSISTANT_DERIVED_LINKS_KEY),
            )
        else:
            logger.warning(
                "derived_edges.missing_link ilot_applicatif=%s label=%s properties=%s",
                entity.id,
                entity.label,
                entity.properties,
            )
            raw = (entity.properties or {}).get("ilot_fonctionnel_id")
            if raw:
                try:
                    ilot_f_id = UUID(str(raw))
                except (ValueError, TypeError):
                    ilot_f_id = None
        if ilot_f_id:
            add_edge(ilot_f_id, entity.id)

    ops_to_fonctionnel: dict[UUID, UUID] = {}
    ops_to_applicatif: dict[UUID, UUID] = {}
    for rel in relations:
        if rel.relation_type != R30_TYPE:
            continue
        src = emap.get(rel.source_id)
        tgt = emap.get(rel.target_id)
        if not src or not tgt or src.entity_type != "operation":
            continue
        if tgt.entity_type == "ilot_fonctionnel":
            ops_to_fonctionnel[rel.source_id] = rel.target_id
        elif tgt.entity_type == "ilot_applicatif":
            ops_to_applicatif[rel.source_id] = rel.target_id

    for op_id, ilot_f_id in ops_to_fonctionnel.items():
        ilot_a_id = ops_to_applicatif.get(op_id)
        if ilot_a_id:
            add_edge(ilot_f_id, ilot_a_id)

    ilots_f = [e for e in entities if e.entity_type == "ilot_fonctionnel"]
    ilots_a = [e for e in entities if e.entity_type == "ilot_applicatif"]
    if len(ilots_f) == 1 and len(ilots_a) == 1:
        add_edge(ilots_f[0].id, ilots_a[0].id)

    return edges


def link_applicatif_to_fonctionnel_via_operation(
    entity: UrbanismEntity,
    ilot_fonctionnel_id: UUID,
    entities: list[UrbanismEntity],
    relations: list[UrbanismRelation],
    project_id: UUID,
) -> list[UrbanismRelation]:
    """Crée R29 (operation → ilot_applicatif) si une opération implémente déjà l'îlot fonctionnel (R30)."""
    emap = _entity_map(entities)
    created: list[UrbanismRelation] = []
    operation_ids = [
        r.source_id
        for r in relations
        if r.target_id == ilot_fonctionnel_id
        and r.relation_type == R30_TYPE
        and (op := emap.get(r.source_id)) is not None
        and op.entity_type == "operation"
    ]

    for op_id in operation_ids:
        exists = any(
            r.source_id == op_id and r.target_id == entity.id and r.relation_type == R30_TYPE
            for r in relations
        )
        if exists:
            continue
        created.append(
            UrbanismRelation(
                project_id=project_id,
                source_id=op_id,
                target_id=entity.id,
                relation_type=R30_TYPE,
                category="applicatif",
            )
        )
    return created
