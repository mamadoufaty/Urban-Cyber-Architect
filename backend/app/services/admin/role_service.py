"""Service CRUD — rôles et permissions associées."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.admin import Permission, Role, RolePermission
from app.schemas.admin import PermissionRead, RoleCreate, RoleRead, RoleUpdate


def _role_to_read(role: Role) -> RoleRead:
    perms = [
        PermissionRead.model_validate(rp.permission)
        for rp in sorted(role.role_permissions, key=lambda x: x.permission.code)
    ]
    return RoleRead(
        id=role.id,
        name=role.name,
        code=role.code,
        description=role.description,
        is_system=role.is_system,
        created_at=role.created_at,
        updated_at=role.updated_at,
        permissions=perms,
    )


async def list_roles(db: AsyncSession) -> tuple[list[RoleRead], int]:
    total = await db.scalar(select(func.count()).select_from(Role)) or 0
    result = await db.execute(
        select(Role)
        .options(selectinload(Role.role_permissions).selectinload(RolePermission.permission))
        .order_by(Role.name)
    )
    items = [_role_to_read(r) for r in result.scalars().all()]
    return items, total


async def get_role(db: AsyncSession, role_id: UUID) -> RoleRead:
    result = await db.execute(
        select(Role)
        .where(Role.id == role_id)
        .options(selectinload(Role.role_permissions).selectinload(RolePermission.permission))
    )
    role = result.scalar_one_or_none()
    if not role:
        raise ValueError("Rôle introuvable")
    return _role_to_read(role)


async def create_role(db: AsyncSession, data: RoleCreate) -> RoleRead:
    existing = await db.execute(select(Role).where(Role.code == data.code))
    if existing.scalar_one_or_none():
        raise ValueError("Un rôle avec ce code existe déjà")
    role = Role(
        name=data.name,
        code=data.code,
        description=data.description,
        is_system=False,
    )
    db.add(role)
    await db.flush()
    return await get_role(db, role.id)


async def update_role(db: AsyncSession, role_id: UUID, data: RoleUpdate) -> RoleRead:
    role = await db.get(Role, role_id)
    if not role:
        raise ValueError("Rôle introuvable")
    if data.name is not None:
        role.name = data.name
    if data.description is not None:
        role.description = data.description
    role.updated_at = datetime.now(timezone.utc)
    await db.flush()
    return await get_role(db, role_id)


async def assign_permissions(db: AsyncSession, role_id: UUID, permission_ids: list[UUID]) -> RoleRead:
    role = await db.get(Role, role_id)
    if not role:
        raise ValueError("Rôle introuvable")

    if permission_ids:
        result = await db.execute(select(Permission).where(Permission.id.in_(permission_ids)))
        found = {p.id for p in result.scalars().all()}
        missing = set(permission_ids) - found
        if missing:
            raise ValueError("Une ou plusieurs permissions sont introuvables")

    existing = await db.execute(select(RolePermission).where(RolePermission.role_id == role_id))
    for rp in existing.scalars().all():
        await db.delete(rp)
    await db.flush()

    for perm_id in permission_ids:
        db.add(RolePermission(role_id=role_id, permission_id=perm_id))
    role.updated_at = datetime.now(timezone.utc)
    await db.flush()
    return await get_role(db, role_id)
