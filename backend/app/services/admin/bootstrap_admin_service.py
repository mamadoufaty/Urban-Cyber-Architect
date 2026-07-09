"""Bootstrap / récupération d'un compte administrateur."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.models.admin import Role, User
from app.schemas.admin import UserCreate
from app.services.admin.admin_guard import ADMIN_ROLE_CODES, count_active_admins
from app.services.admin.audit_service import log_action
from app.services.admin.seed_service import run_admin_seed
from app.services.admin.user_service import create_user, reset_password
from app.services.password_service import hash_password

DEFAULT_ADMIN_USERNAME = "admin"
PREFERRED_ADMIN_ROLE_CODE = "superadmin"
FALLBACK_ADMIN_ROLE_CODE = "admin"


def bootstrap_enabled() -> bool:
    return settings.debug or settings.enable_bootstrap_admin


async def needs_bootstrap(db: AsyncSession) -> bool:
    return await count_active_admins(db) == 0


async def _resolve_admin_role(db: AsyncSession) -> Role:
    for code in (PREFERRED_ADMIN_ROLE_CODE, FALLBACK_ADMIN_ROLE_CODE):
        result = await db.execute(select(Role).where(Role.code == code))
        role = result.scalar_one_or_none()
        if role:
            return role
    raise ValueError("Aucun rôle administrateur disponible — exécutez le seed initial.")


async def _audit_bootstrap(
    db: AsyncSession,
    *,
    username: str,
    result: str,
    user_id: UUID | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    details: dict | None = None,
) -> None:
    payload = {"username": username, **(details or {})}
    await log_action(
        db,
        user_id=user_id,
        action="admin.bootstrap",
        object_type="user",
        object_id=str(user_id) if user_id else None,
        result=result,
        ip_address=ip_address,
        user_agent=user_agent,
        details=payload,
    )


async def bootstrap_admin_cli(
    db: AsyncSession,
    *,
    username: str = DEFAULT_ADMIN_USERNAME,
    password: str,
    first_name: str | None = None,
    last_name: str | None = None,
    email: str | None = None,
    reset: bool = False,
) -> dict[str, str]:
    """Commande CLI — crée ou réinitialise un administrateur."""
    await run_admin_seed(db)
    admin_role = await _resolve_admin_role(db)

    result = await db.execute(
        select(User).where(User.username == username).options(selectinload(User.role))
    )
    existing = result.scalar_one_or_none()

    if existing:
        existing.password_hash = hash_password(password)
        if first_name is not None:
            existing.first_name = first_name
        if last_name is not None:
            existing.last_name = last_name
        if email is not None:
            existing.email = email
        existing.role_id = admin_role.id
        existing.status = "active"
        existing.failed_login_count = 0
        existing.locked_until = None
        await db.flush()
        await _audit_bootstrap(
            db,
            username=username,
            user_id=existing.id,
            result="password_reset",
            details={"mode": "cli", "reset": reset},
        )
        await db.commit()
        return {"action": "password_reset", "username": username, "role": admin_role.code}

    user = await create_user(
        db,
        UserCreate(
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name,
            email=email,
            role_id=admin_role.id,
            status="active",
        ),
    )
    await _audit_bootstrap(
        db,
        username=username,
        user_id=user.id,
        result="created",
        details={"mode": "cli"},
    )
    await db.commit()
    return {"action": "created", "username": username, "role": admin_role.code}


async def bootstrap_admin_recovery(
    db: AsyncSession,
    *,
    username: str,
    password: str,
    first_name: str | None = None,
    last_name: str | None = None,
    email: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> dict[str, str]:
    """Récupération via interface — uniquement si aucun admin actif."""
    if not bootstrap_enabled():
        raise ValueError("La récupération administrateur n'est pas activée sur cette instance.")
    if not await needs_bootstrap(db):
        raise ValueError("Au moins un administrateur actif existe déjà.")

    await run_admin_seed(db)
    admin_role = await _resolve_admin_role(db)

    result = await db.execute(select(User).where(User.username == username))
    existing = result.scalar_one_or_none()
    if existing:
        existing.password_hash = hash_password(password)
        existing.first_name = first_name or existing.first_name
        existing.last_name = last_name or existing.last_name
        existing.email = email or existing.email
        existing.role_id = admin_role.id
        existing.status = "active"
        existing.failed_login_count = 0
        existing.locked_until = None
        await db.flush()
        await _audit_bootstrap(
            db,
            username=username,
            user_id=existing.id,
            result="password_reset",
            ip_address=ip_address,
            user_agent=user_agent,
            details={"mode": "recovery"},
        )
        await db.commit()
        return {"action": "password_reset", "username": username, "role": admin_role.code}

    user = await create_user(
        db,
        UserCreate(
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name,
            email=email,
            role_id=admin_role.id,
            status="active",
        ),
    )
    await _audit_bootstrap(
        db,
        username=username,
        user_id=user.id,
        result="created",
        ip_address=ip_address,
        user_agent=user_agent,
        details={"mode": "recovery"},
    )
    await db.commit()
    return {"action": "created", "username": username, "role": admin_role.code}
