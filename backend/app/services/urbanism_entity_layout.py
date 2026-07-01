"""Persistance du placement manuel des entités (urbanisme)."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from app.models.entities import UrbanismEntity

LAYOUT_KEY = "layout"


def get_entity_layout(properties: dict | None) -> dict[str, Any] | None:
    if not properties or not isinstance(properties, dict):
        return None
    layout = properties.get(LAYOUT_KEY)
    if not isinstance(layout, dict):
        return None
    if layout.get("mode") == "manual" or layout.get("locked"):
        return layout
    return None


def is_manual_layout(layout: dict[str, Any] | None) -> bool:
    return get_entity_layout({"layout": layout} if layout else None) is not None


def resolve_entity_position(
    entity: UrbanismEntity,
    canonical: dict[str, float],
) -> tuple[dict[str, float], dict[str, Any]]:
    manual = get_entity_layout(entity.properties)
    if manual and "x" in manual and "y" in manual:
        pos = {"x": float(manual["x"]), "y": float(manual["y"])}
        return pos, manual
    pos = dict(canonical)
    return pos, {"mode": "auto", "locked": False, "x": pos["x"], "y": pos["y"]}


async def save_entity_layout(
    db: AsyncSession,
    project_id: UUID,
    entity_id: UUID,
    layout: dict[str, Any],
) -> dict[str, Any]:
    entity = await db.get(UrbanismEntity, entity_id)
    if not entity or entity.project_id != project_id:
        raise ValueError("Entité introuvable")
    stored = {
        "mode": "manual",
        "locked": True,
        "x": float(layout["x"]),
        "y": float(layout["y"]),
    }
    props = dict(entity.properties or {})
    props[LAYOUT_KEY] = stored
    entity.properties = props
    flag_modified(entity, "properties")
    await db.commit()
    await db.refresh(entity)
    return stored


async def save_entity_layouts_bulk(
    db: AsyncSession,
    project_id: UUID,
    layouts: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    saved: list[dict[str, Any]] = []
    for item in layouts:
        entity_id = UUID(str(item["entity_id"]))
        entity = await db.get(UrbanismEntity, entity_id)
        if not entity or entity.project_id != project_id:
            raise ValueError(f"Entité introuvable: {entity_id}")
        stored = {
            "mode": "manual",
            "locked": True,
            "x": float(item["layout"]["x"]),
            "y": float(item["layout"]["y"]),
        }
        props = dict(entity.properties or {})
        props[LAYOUT_KEY] = stored
        entity.properties = props
        flag_modified(entity, "properties")
        saved.append({"entity_id": str(entity_id), "layout": stored})
    await db.commit()
    return saved


async def clear_entity_layout(
    db: AsyncSession,
    project_id: UUID,
    entity_id: UUID,
) -> None:
    entity = await db.get(UrbanismEntity, entity_id)
    if not entity or entity.project_id != project_id:
        raise ValueError("Entité introuvable")
    props = dict(entity.properties or {})
    props.pop(LAYOUT_KEY, None)
    entity.properties = props
    flag_modified(entity, "properties")
    await db.commit()
