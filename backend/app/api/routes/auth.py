"""Routes API — authentification."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.auth import (
    BootstrapAdminRequest,
    BootstrapAdminResponse,
    BootstrapStatusResponse,
    LoginRequest,
    LoginResponse,
)
from app.services.admin.bootstrap_admin_service import (
    bootstrap_admin_recovery,
    bootstrap_enabled,
    needs_bootstrap,
)
from app.services.auth_service import login

router = APIRouter(prefix="/auth", tags=["auth"])


def _client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return None


@router.get("/bootstrap/status", response_model=BootstrapStatusResponse)
async def api_bootstrap_status(db: AsyncSession = Depends(get_db)):
    required = await needs_bootstrap(db)
    enabled = bootstrap_enabled()
    message = "Aucun administrateur détecté." if required else None
    return BootstrapStatusResponse(
        needs_bootstrap=required,
        bootstrap_enabled=enabled,
        message=message,
    )


@router.post("/bootstrap", response_model=BootstrapAdminResponse, status_code=201)
async def api_bootstrap_admin(
    body: BootstrapAdminRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    try:
        result = await bootstrap_admin_recovery(
            db,
            username=body.username.strip(),
            password=body.password,
            first_name=body.first_name,
            last_name=body.last_name,
            email=body.email,
            ip_address=_client_ip(request),
            user_agent=request.headers.get("user-agent"),
        )
        return BootstrapAdminResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.post("/login", response_model=LoginResponse)
async def api_login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    try:
        response = await login(db, body.username, body.password)
        await db.commit()
        return response
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
