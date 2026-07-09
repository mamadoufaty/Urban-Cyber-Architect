"""Journalisation de l'import cartographie."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.admin.audit_service import log_action
from app.services.urbanism_import.types import ImportMode, ImportReport


async def log_import(
    db: AsyncSession,
    *,
    project_id: UUID,
    mode: ImportMode,
    filename: str,
    report: ImportReport,
    user_id: UUID | None = None,
) -> None:
    await log_action(
        db,
        user_id=user_id,
        action="urbanism.import",
        object_type="project",
        object_id=str(project_id),
        details={
            "mode": mode.value,
            "filename": filename,
            "created": report.created,
            "updated": report.updated,
            "relations_created": report.relations_created,
            "orphans": report.orphans,
            "inconsistencies": report.inconsistencies,
            "completeness_rate": report.completeness_rate,
            "flux_stored": report.flux_stored,
        },
    )
