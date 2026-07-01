"""Service CRUD — utilisateurs."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.admin import Organization, Role, User
from app.schemas.admin import UserCreate, UserRead, UserUpdate
from app.services.password_service import hash_password


def _user_to_read(user: User) -> UserRead:
    return UserRead(
        id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        phone=user.phone,
        organization_id=user.organization_id,
        function=user.function,
        role_id=user.role_id,
        status=user.status,
        avatar=user.avatar,
        last_login_at=user.last_login_at,
        failed_login_count=user.failed_login_count,
        locked_until=user.locked_until,
        created_at=user.created_at,
        updated_at=user.updated_at,
        role_code=user.role.code if user.role else None,
        organization_name=user.organization.name if user.organization else None,
    )


async def list_users(db: AsyncSession) -> tuple[list[UserRead], int]:
    total = await db.scalar(select(func.count()).select_from(User)) or 0
    result = await db.execute(
        select(User)
        .options(selectinload(User.role), selectinload(User.organization))
        .order_by(User.username)
    )
    items = [_user_to_read(u) for u in result.scalars().all()]
    return items, total


async def get_user(db: AsyncSession, user_id: UUID) -> UserRead:
    result = await db.execute(
        select(User)
        .where(User.id == user_id)
        .options(selectinload(User.role), selectinload(User.organization))
    )
    user = result.scalar_one_or_none()
    if not user:
        raise ValueError("Utilisateur introuvable")
    return _user_to_read(user)


async def create_user(db: AsyncSession, data: UserCreate) -> UserRead:
    existing = await db.execute(select(User).where(User.username == data.username))
    if existing.scalar_one_or_none():
        raise ValueError("Nom d'utilisateur déjà utilisé")
    if data.organization_id:
        org = await db.get(Organization, data.organization_id)
        if not org:
            raise ValueError("Organisation introuvable")
    if data.role_id:
        role = await db.get(Role, data.role_id)
        if not role:
            raise ValueError("Rôle introuvable")
    user = User(
        username=data.username,
        password_hash=hash_password(data.password),
        first_name=data.first_name,
        last_name=data.last_name,
        email=data.email,
        phone=data.phone,
        organization_id=data.organization_id,
        function=data.function,
        role_id=data.role_id,
        status=data.status,
        avatar=data.avatar,
    )
    db.add(user)
    await db.flush()
    return await get_user(db, user.id)


async def update_user(db: AsyncSession, user_id: UUID, data: UserUpdate) -> UserRead:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise ValueError("Utilisateur introuvable")
    if data.organization_id is not None:
        if data.organization_id:
            org = await db.get(Organization, data.organization_id)
            if not org:
                raise ValueError("Organisation introuvable")
        user.organization_id = data.organization_id
    if data.role_id is not None:
        if data.role_id:
            role = await db.get(Role, data.role_id)
            if not role:
                raise ValueError("Rôle introuvable")
        user.role_id = data.role_id
    for field in ("first_name", "last_name", "email", "phone", "function", "status", "avatar"):
        value = getattr(data, field)
        if value is not None:
            setattr(user, field, value)
    user.updated_at = datetime.now(timezone.utc)
    await db.flush()
    return await get_user(db, user_id)


async def disable_user(db: AsyncSession, user_id: UUID) -> UserRead:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise ValueError("Utilisateur introuvable")
    user.status = "disabled"
    user.updated_at = datetime.now(timezone.utc)
    await db.flush()
    return await get_user(db, user_id)


async def enable_user(db: AsyncSession, user_id: UUID) -> UserRead:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise ValueError("Utilisateur introuvable")
    user.status = "active"
    user.failed_login_count = 0
    user.locked_until = None
    user.updated_at = datetime.now(timezone.utc)
    await db.flush()
    return await get_user(db, user_id)


async def reset_password(db: AsyncSession, user_id: UUID, password: str) -> UserRead:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise ValueError("Utilisateur introuvable")
    user.password_hash = hash_password(password)
    user.updated_at = datetime.now(timezone.utc)
    await db.flush()
    return await get_user(db, user_id)


async def delete_user(db: AsyncSession, user_id: UUID) -> None:
    user = await db.get(User, user_id)
    if not user:
        raise ValueError("Utilisateur introuvable")
    await db.delete(user)
    await db.flush()
