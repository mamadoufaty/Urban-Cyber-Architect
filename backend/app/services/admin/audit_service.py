"""Service — journal d'audit."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.admin import AuditLog, User
from app.schemas.admin import AuditLogRead


async def log_action(
    db: AsyncSession,
    *,
    action: str,
    user_id: UUID | None = None,
    object_type: str | None = None,
    object_id: str | None = None,
    result: str = "success",
    ip_address: str | None = None,
    user_agent: str | None = None,
    details: dict | None = None,
) -> AuditLog:
    entry = AuditLog(
        user_id=user_id,
        action=action,
        object_type=object_type,
        object_id=object_id,
        result=result,
        ip_address=ip_address,
        user_agent=user_agent,
        details=details or {},
    )
    db.add(entry)
    await db.flush()
    return entry


def _audit_to_read(entry: AuditLog) -> AuditLogRead:
    return AuditLogRead(
        id=entry.id,
        user_id=entry.user_id,
        action=entry.action,
        object_type=entry.object_type,
        object_id=entry.object_id,
        result=entry.result,
        ip_address=entry.ip_address,
        user_agent=entry.user_agent,
        details=entry.details,
        created_at=entry.created_at,
        username=entry.user.username if entry.user else None,
    )


async def list_audit_logs(db: AsyncSession, *, limit: int = 100) -> tuple[list[AuditLogRead], int]:
    total = await db.scalar(select(func.count()).select_from(AuditLog)) or 0
    result = await db.execute(
        select(AuditLog)
        .options(selectinload(AuditLog.user))
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
    )
    items = [_audit_to_read(e) for e in result.scalars().all()]
    return items, total
