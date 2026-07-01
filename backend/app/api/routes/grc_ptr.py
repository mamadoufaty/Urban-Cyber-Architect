"""Routes API — Plan de Traitement des Risques (PTR)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.entities import Project
from app.schemas.ebios import EbiosRecordResponse
from app.schemas.grc_ptr import PtrActionPatch, PtrResponse
from app.services.ebios.assessment_service import get_or_create_assessment
from app.services.grc.ptr_export import export_ptr_csv, export_ptr_pdf, export_ptr_xlsx
from app.services.grc.ptr_service import get_ptr_for_export, get_risk_treatment_plan, patch_ptr_action

router = APIRouter(tags=["grc-ptr"])


def _export_filters(
    search: str,
    responsible: str | None,
    organization: str | None,
    priority: str | None,
    status: str | None,
    treatment_decision: str | None,
    due_filter: str | None,
) -> dict:
    return {
        "search": search,
        "responsible": responsible,
        "organization": organization,
        "priority": priority,
        "status": status,
        "treatment_decision": treatment_decision,
        "due_filter": due_filter,
    }


@router.get(
    "/projects/{project_id}/grc/ptr",
    response_model=PtrResponse,
)
async def list_risk_treatment_plan(
    project_id: UUID,
    search: str = Query("", max_length=200),
    responsible: str | None = None,
    organization: str | None = None,
    priority: str | None = None,
    status: str | None = None,
    treatment_decision: str | None = None,
    due_filter: str | None = Query(
        None, pattern="^(overdue|due_soon|this_week|this_month)$"
    ),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    try:
        assessment = await get_or_create_assessment(db, project_id)
        project = await db.get(Project, project_id)
        return await get_risk_treatment_plan(
            db,
            project_id,
            assessment.id,
            project_name=project.name if project else "",
            search=search,
            responsible=responsible,
            organization=organization,
            priority=priority,
            status=status,
            treatment_decision=treatment_decision,
            due_filter=due_filter,
            page=page,
            page_size=page_size,
        )
    except ValueError as e:
        raise HTTPException(404, str(e)) from e


@router.patch(
    "/projects/{project_id}/grc/ptr/actions/{action_id}",
    response_model=EbiosRecordResponse,
)
async def update_ptr_action(
    project_id: UUID,
    action_id: UUID,
    data: PtrActionPatch,
    db: AsyncSession = Depends(get_db),
):
    try:
        assessment = await get_or_create_assessment(db, project_id)
        return await patch_ptr_action(
            db,
            assessment.id,
            action_id,
            data.model_dump(exclude_unset=True),
        )
    except ValueError as e:
        raise HTTPException(404, str(e)) from e


@router.get("/projects/{project_id}/grc/ptr/export")
async def export_risk_treatment_plan(
    project_id: UUID,
    format: str = Query("csv", pattern="^(csv|xlsx|pdf)$"),
    search: str = Query("", max_length=200),
    responsible: str | None = None,
    organization: str | None = None,
    priority: str | None = None,
    status: str | None = None,
    treatment_decision: str | None = None,
    due_filter: str | None = Query(
        None, pattern="^(overdue|due_soon|this_week|this_month)$"
    ),
    db: AsyncSession = Depends(get_db),
):
    try:
        assessment = await get_or_create_assessment(db, project_id)
        project = await db.get(Project, project_id)
        summary, rows = await get_ptr_for_export(
            db,
            project_id,
            assessment.id,
            project_name=project.name if project else "",
            **_export_filters(
                search,
                responsible,
                organization,
                priority,
                status,
                treatment_decision,
                due_filter,
            ),
        )

        if format == "csv":
            content = export_ptr_csv(rows)
            media_type = "text/csv; charset=utf-8"
            filename = "plan-traitement-risques.csv"
        elif format == "xlsx":
            content = export_ptr_xlsx(rows, summary=summary)
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            filename = "plan-traitement-risques.xlsx"
        else:
            content = export_ptr_pdf(
                rows,
                summary=summary,
                project_name=project.name if project else "",
            )
            media_type = "application/pdf"
            filename = "plan-traitement-risques.pdf"

        return Response(
            content=content,
            media_type=media_type,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except ValueError as e:
        raise HTTPException(404, str(e)) from e
