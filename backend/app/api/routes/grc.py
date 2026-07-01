"""Routes API — module GRC (Registre des risques)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.entities import Project
from app.schemas.grc import RiskRegisterResponse
from app.schemas.grc_dashboard import RssiDashboardResponse
from app.services.ebios.assessment_service import get_or_create_assessment
from app.services.grc.grc_dashboard_service import get_rssi_dashboard
from app.services.grc.risk_register_export import (
    export_risk_register_csv,
    export_risk_register_pdf,
    export_risk_register_xlsx,
)
from app.services.grc.risk_register_service import get_risk_register, get_risk_register_for_export

router = APIRouter(tags=["grc"])


def _export_filters(
    search: str,
    organization: str | None,
    severity: str | None,
    criticality: str | None,
    treatment_decision: str | None,
    status: str | None,
    sort_by: str,
    sort_dir: str,
) -> dict:
    return {
        "search": search,
        "organization": organization,
        "severity": severity,
        "criticality": criticality,
        "treatment_decision": treatment_decision,
        "status": status,
        "sort_by": sort_by,
        "sort_dir": sort_dir,
    }


@router.get(
    "/projects/{project_id}/grc/risk-register",
    response_model=RiskRegisterResponse,
)
async def list_risk_register(
    project_id: UUID,
    search: str = Query("", max_length=200),
    organization: str | None = None,
    severity: str | None = None,
    criticality: str | None = None,
    treatment_decision: str | None = None,
    status: str | None = None,
    sort_by: str = Query("updated_at"),
    sort_dir: str = Query("desc", pattern="^(asc|desc)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    try:
        assessment = await get_or_create_assessment(db, project_id)
        return await get_risk_register(
            db,
            project_id,
            assessment.id,
            search=search,
            organization=organization,
            severity=severity,
            criticality=criticality,
            treatment_decision=treatment_decision,
            status=status,
            sort_by=sort_by,
            sort_dir=sort_dir,
            page=page,
            page_size=page_size,
        )
    except ValueError as e:
        raise HTTPException(404, str(e)) from e


@router.get(
    "/projects/{project_id}/grc/dashboard-rssi",
    response_model=RssiDashboardResponse,
)
async def get_dashboard_rssi(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    try:
        assessment = await get_or_create_assessment(db, project_id)
        project = await db.get(Project, project_id)
        return await get_rssi_dashboard(
            db,
            project_id,
            assessment.id,
            project_name=project.name if project else "",
        )
    except ValueError as e:
        raise HTTPException(404, str(e)) from e


@router.get("/projects/{project_id}/grc/dashboard-rssi/export")
async def export_dashboard_rssi(
    project_id: UUID,
    format: str = Query(
        "dashboard_pdf",
        pattern="^(dashboard_pdf|comex_summary|rssi_report)$",
    ),
):
    """Endpoint réservé — exports dashboard à implémenter dans un sprint ultérieur."""
    raise HTTPException(
        status_code=501,
        detail={
            "message": "Export dashboard non implémenté dans ce sprint.",
            "format": format,
            "project_id": str(project_id),
            "planned_formats": ["dashboard_pdf", "comex_summary", "rssi_report"],
        },
    )


@router.get("/projects/{project_id}/grc/risk-register/export")
async def export_risk_register(
    project_id: UUID,
    format: str = Query("csv", pattern="^(csv|xlsx|pdf)$"),
    search: str = Query("", max_length=200),
    organization: str | None = None,
    severity: str | None = None,
    criticality: str | None = None,
    treatment_decision: str | None = None,
    status: str | None = None,
    sort_by: str = Query("updated_at"),
    sort_dir: str = Query("desc", pattern="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db),
):
    try:
        assessment = await get_or_create_assessment(db, project_id)
        project = await db.get(Project, project_id)
        rows = await get_risk_register_for_export(
            db,
            project_id,
            assessment.id,
            **_export_filters(
                search,
                organization,
                severity,
                criticality,
                treatment_decision,
                status,
                sort_by,
                sort_dir,
            ),
        )

        if format == "csv":
            content = export_risk_register_csv(rows)
            media_type = "text/csv; charset=utf-8"
            filename = "registre-risques.csv"
        elif format == "xlsx":
            content = export_risk_register_xlsx(rows)
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            filename = "registre-risques.xlsx"
        else:
            content = export_risk_register_pdf(rows, project_name=project.name if project else "")
            media_type = "application/pdf"
            filename = "registre-risques.pdf"

        return Response(
            content=content,
            media_type=media_type,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except ValueError as e:
        raise HTTPException(404, str(e)) from e
