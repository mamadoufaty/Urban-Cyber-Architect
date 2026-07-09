"""Persistance du tracé manuel des relations (waypoints verrouillés)."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from app.models.entities import UrbanismEntity, UrbanismRelation

EDGE_LAYOUTS_KEY = "_edge_layouts"
DERIVED_EDGE_PREFIX = "derived-fonc-applic-"


def get_relation_layout(properties: dict | None) -> dict[str, Any] | None:
    if not properties or not isinstance(properties, dict):
        return None
    layout = properties.get("layout")
    if not isinstance(layout, dict):
        return None
    if layout.get("mode") == "manual" or layout.get("locked"):
        return layout
    return None


def get_derived_edge_layout(entity: UrbanismEntity, edge_id: str) -> dict[str, Any] | None:
    props = entity.properties or {}
    layouts = props.get(EDGE_LAYOUTS_KEY)
    if not isinstance(layouts, dict):
        return None
    layout = layouts.get(edge_id)
    if not isinstance(layout, dict):
        return None
    if layout.get("mode") == "manual" or layout.get("locked"):
        return layout
    return None


def parse_derived_fonc_applic_edge(edge_id: str) -> tuple[UUID, UUID] | None:
    if not edge_id.startswith(DERIVED_EDGE_PREFIX):
        return None
    rest = edge_id[len(DERIVED_EDGE_PREFIX) :]
    if len(rest) < 73 or rest[36] != "-":
        return None
    try:
        source = UUID(rest[:36])
        target = UUID(rest[37:73])
        return source, target
    except (ValueError, TypeError):
        return None


def _relation_owned(
    rel: UrbanismRelation | None, project_id: UUID, cartography_version_id: UUID | None
) -> bool:
    if not rel or rel.project_id != project_id:
        return False
    if cartography_version_id is not None and rel.cartography_version_id != cartography_version_id:
        return False
    return True


def _entity_owned(
    entity: UrbanismEntity | None, project_id: UUID, cartography_version_id: UUID | None
) -> bool:
    if not entity or entity.project_id != project_id:
        return False
    if cartography_version_id is not None and entity.cartography_version_id != cartography_version_id:
        return False
    return True


async def save_edge_layout(
    db: AsyncSession,
    project_id: UUID,
    edge_id: str,
    layout: dict[str, Any],
    cartography_version_id: UUID | None = None,
) -> dict[str, Any]:
    """Enregistre un tracé verrouillé pour une relation persistée ou dérivée."""
    layout = {**layout, "mode": "manual", "locked": True, "pathType": layout.get("pathType") or "custom"}

    try:
        relation_id = UUID(edge_id)
    except (ValueError, TypeError):
        relation_id = None

    if relation_id is not None:
        rel = await db.get(UrbanismRelation, relation_id)
        if not _relation_owned(rel, project_id, cartography_version_id):
            raise ValueError("Relation introuvable")
        props = dict(rel.properties or {})
        props["layout"] = layout
        rel.properties = props
        flag_modified(rel, "properties")
        await db.commit()
        await db.refresh(rel)
        return layout

    parsed = parse_derived_fonc_applic_edge(edge_id)
    if not parsed:
        raise ValueError("Identifiant de lien invalide")
    _source_id, target_id = parsed
    entity = await db.get(UrbanismEntity, target_id)
    if not _entity_owned(entity, project_id, cartography_version_id):
        raise ValueError("Entité cible du lien dérivé introuvable")
    props = dict(entity.properties or {})
    layouts = dict(props.get(EDGE_LAYOUTS_KEY) or {})
    layouts[edge_id] = layout
    props[EDGE_LAYOUTS_KEY] = layouts
    entity.properties = props
    flag_modified(entity, "properties")
    await db.commit()
    await db.refresh(entity)
    return layout


async def clear_edge_layout(
    db: AsyncSession,
    project_id: UUID,
    edge_id: str,
    cartography_version_id: UUID | None = None,
) -> None:
    """Supprime le verrouillage — le moteur recalculera le tracé."""
    try:
        relation_id = UUID(edge_id)
    except (ValueError, TypeError):
        relation_id = None

    if relation_id is not None:
        rel = await db.get(UrbanismRelation, relation_id)
        if not _relation_owned(rel, project_id, cartography_version_id):
            raise ValueError("Relation introuvable")
        props = dict(rel.properties or {})
        props.pop("layout", None)
        rel.properties = props
        flag_modified(rel, "properties")
        await db.commit()
        return

    parsed = parse_derived_fonc_applic_edge(edge_id)
    if not parsed:
        raise ValueError("Identifiant de lien invalide")
    _source_id, target_id = parsed
    entity = await db.get(UrbanismEntity, target_id)
    if not _entity_owned(entity, project_id, cartography_version_id):
        raise ValueError("Entité cible du lien dérivé introuvable")
    props = dict(entity.properties or {})
    layouts = dict(props.get(EDGE_LAYOUTS_KEY) or {})
    layouts.pop(edge_id, None)
    if layouts:
        props[EDGE_LAYOUTS_KEY] = layouts
    else:
        props.pop(EDGE_LAYOUTS_KEY, None)
    entity.properties = props
    flag_modified(entity, "properties")
    await db.commit()
