"""Routes API — livrables automatiques EBIOS RM (lecture seule)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.entities import Project
from app.schemas.ebios import EbiosDeliverableResponse
from app.services.deliverables.ebios_report_generator import (
    build_executive_summary,
    build_full_report,
    build_risk_register_deliverable,
    build_treatment_plan_deliverable,
)
from app.services.ebios.assessment_service import get_assessment

router = APIRouter(tags=["ebios-deliverables"])


async def _load_context(db: AsyncSession, project_id: UUID, assessment_id: UUID):
    try:
        assessment = await get_assessment(db, project_id, assessment_id)
    except ValueError as e:
        raise HTTPException(404, str(e)) from e
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "Projet introuvable")
    return project, assessment


@router.get(
    "/projects/{project_id}/ebios/assessments/{assessment_id}/deliverables/report",
    response_model=EbiosDeliverableResponse,
)
async def get_ebios_deliverable_report(
    project_id: UUID, assessment_id: UUID, db: AsyncSession = Depends(get_db)
):
    project, assessment = await _load_context(db, project_id, assessment_id)
    return await build_full_report(db, project, assessment)


@router.get(
    "/projects/{project_id}/ebios/assessments/{assessment_id}/deliverables/risk-register",
    response_model=EbiosDeliverableResponse,
)
async def get_ebios_deliverable_risk_register(
    project_id: UUID, assessment_id: UUID, db: AsyncSession = Depends(get_db)
):
    project, assessment = await _load_context(db, project_id, assessment_id)
    return await build_risk_register_deliverable(db, project, assessment)


@router.get(
    "/projects/{project_id}/ebios/assessments/{assessment_id}/deliverables/treatment-plan",
    response_model=EbiosDeliverableResponse,
)
async def get_ebios_deliverable_treatment_plan(
    project_id: UUID, assessment_id: UUID, db: AsyncSession = Depends(get_db)
):
    project, assessment = await _load_context(db, project_id, assessment_id)
    return await build_treatment_plan_deliverable(db, project, assessment)


@router.get(
    "/projects/{project_id}/ebios/assessments/{assessment_id}/deliverables/executive-summary",
    response_model=EbiosDeliverableResponse,
)
async def get_ebios_deliverable_executive_summary(
    project_id: UUID, assessment_id: UUID, db: AsyncSession = Depends(get_db)
):
    project, assessment = await _load_context(db, project_id, assessment_id)
    return await build_executive_summary(db, project, assessment)
