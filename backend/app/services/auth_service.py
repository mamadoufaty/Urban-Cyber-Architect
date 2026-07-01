"""Service d'authentification — connexion utilisateur."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.admin import User
from app.schemas.auth import AuthUserResponse, LoginResponse
from app.services.password_service import verify_password

INVALID_CREDENTIALS_MSG = "Identifiants invalides."


def _display_name(user: User) -> str:
    parts = [user.first_name, user.last_name]
    label = " ".join(p.strip() for p in parts if p and str(p).strip())
    return label or user.username


async def login(db: AsyncSession, username: str, password: str) -> LoginResponse:
    normalized = username.strip()
    result = await db.execute(
        select(User)
        .where(User.username == normalized)
        .options(selectinload(User.role))
    )
    user = result.scalar_one_or_none()

    if not user or not verify_password(password, user.password_hash):
        raise ValueError(INVALID_CREDENTIALS_MSG)

    if user.status != "active":
        raise ValueError(INVALID_CREDENTIALS_MSG)

    user.last_login_at = datetime.now(timezone.utc)
    user.failed_login_count = 0
    user.locked_until = None
    await db.flush()

    role_code = user.role.code if user.role else "metier"
    return LoginResponse(
        user=AuthUserResponse(
            id=str(user.id),
            username=user.username,
            displayName=_display_name(user),
            role=role_code,
        )
    )
