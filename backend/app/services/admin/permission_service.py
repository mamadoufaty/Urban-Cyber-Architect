"""Service lecture — permissions."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admin import Permission


async def list_permissions(db: AsyncSession) -> tuple[list[Permission], int]:
    total = await db.scalar(select(func.count()).select_from(Permission)) or 0
    result = await db.execute(select(Permission).order_by(Permission.code))
    return list(result.scalars().all()), total


async def get_permission(db: AsyncSession, permission_id: UUID) -> Permission:
    perm = await db.get(Permission, permission_id)
    if not perm:
        raise ValueError("Permission introuvable")
    return perm
