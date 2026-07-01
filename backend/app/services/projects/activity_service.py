"""Journalisation des actions projet."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project_core import ProjectActivity


async def log_project_activity(
    db: AsyncSession,
    *,
    project_id: UUID,
    action: str,
    details: dict | None = None,
    user_id: UUID | None = None,
) -> ProjectActivity:
    entry = ProjectActivity(
        project_id=project_id,
        user_id=user_id,
        action=action,
        details=details or {},
    )
    db.add(entry)
    return entry
