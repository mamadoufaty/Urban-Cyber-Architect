"""Routes API — corrélation SOC (lecture seule)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.entities import Project
from app.schemas.soc_correlation import SocCorrelationsResponse
from app.services.soc.correlation_service import get_soc_correlations

router = APIRouter(tags=["soc"])


@router.get("/soc/correlations", response_model=SocCorrelationsResponse)
async def list_soc_correlations(
    project_id: UUID = Query(..., description="Identifiant du projet"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "Projet introuvable")
    return await get_soc_correlations(
        db,
        project_id,
        limit=limit,
        offset=offset,
        project_name=project.name,
    )
