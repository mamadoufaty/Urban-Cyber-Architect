"""Journalisation des actions projet."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project_core import ProjectActivity


def serialize_activity_details(value: Any) -> Any:
    """Convertit récursivement les valeurs non JSON-serialisables pour project_activity.details."""
    if isinstance(value, dict):
        return {key: serialize_activity_details(item) for key, item in value.items()}
    if isinstance(value, list):
        return [serialize_activity_details(item) for item in value]
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return value


async def log_project_activity(
    db: AsyncSession,
    *,
    project_id: UUID,
    action: str,
    details: dict | None = None,
    user_id: UUID | None = None,
) -> ProjectActivity:
    raw_details = details or {}
    serialized_details = serialize_activity_details(raw_details)
    if not isinstance(serialized_details, dict):
        serialized_details = {}

    entry = ProjectActivity(
        project_id=project_id,
        user_id=user_id,
        action=action,
        details=serialized_details,
    )
    db.add(entry)
    return entry
