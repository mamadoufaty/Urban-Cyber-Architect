"""Protection du dernier administrateur actif de la plateforme."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.admin import Role, User

ADMIN_ROLE_CODES = frozenset({"admin", "superadmin"})
LAST_ADMIN_MESSAGE = "Impossible de supprimer le dernier administrateur de la plateforme."


class LastAdministratorError(ValueError):
    """Levée lorsqu'une action supprimerait le dernier administrateur actif."""

    def __init__(self) -> None:
        super().__init__(LAST_ADMIN_MESSAGE)


async def count_active_admins(
    db: AsyncSession,
    *,
    exclude_user_id: UUID | None = None,
) -> int:
    query = (
        select(func.count())
        .select_from(User)
        .join(Role, User.role_id == Role.id)
        .where(User.status == "active", Role.code.in_(ADMIN_ROLE_CODES))
    )
    if exclude_user_id is not None:
        query = query.where(User.id != exclude_user_id)
    return int(await db.scalar(query) or 0)


async def user_has_admin_role(db: AsyncSession, user_id: UUID) -> bool:
    result = await db.execute(
        select(User).where(User.id == user_id).options(selectinload(User.role))
    )
    user = result.scalar_one_or_none()
    if not user or user.status != "active" or not user.role:
        return False
    return user.role.code in ADMIN_ROLE_CODES


async def ensure_admin_remains(db: AsyncSession, user_id: UUID) -> None:
    """Refuse si l'utilisateur est le dernier administrateur actif."""
    if not await user_has_admin_role(db, user_id):
        return
    if await count_active_admins(db, exclude_user_id=user_id) == 0:
        raise LastAdministratorError()


async def ensure_role_change_keeps_admin(
    db: AsyncSession,
    user_id: UUID,
    new_role_id: UUID | None,
) -> None:
    """Refuse la rétrogradation du dernier administrateur actif."""
    if not await user_has_admin_role(db, user_id):
        return
    if new_role_id is None:
        raise LastAdministratorError()
    role = await db.get(Role, new_role_id)
    if role and role.code in ADMIN_ROLE_CODES:
        return
    if await count_active_admins(db, exclude_user_id=user_id) == 0:
        raise LastAdministratorError()
