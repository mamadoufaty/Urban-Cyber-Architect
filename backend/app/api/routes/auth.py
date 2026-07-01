"""Routes API — authentification."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.auth import LoginRequest, LoginResponse
from app.services.auth_service import login

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
async def api_login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    try:
        response = await login(db, body.username, body.password)
        await db.commit()
        return response
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
