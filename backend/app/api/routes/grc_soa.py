"""Routes API — Déclaration d'Applicabilité (SoA)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.entities import Project
from app.schemas.grc_soa import SoaResponse
from app.services.ebios.assessment_service import get_or_create_assessment
from app.services.grc.soa_export import export_soa_csv, export_soa_pdf, export_soa_xlsx
from app.services.grc.soa_service import get_soa_for_export, get_statement_of_applicability

router = APIRouter(tags=["grc-soa"])


def _export_filters(
    search: str,
    iso_reference: str | None,
    applicable: str | None,
    implemented: str | None,
    responsible: str | None,
    status: str | None,
) -> dict:
    return {
        "search": search,
        "iso_reference": iso_reference,
        "applicable": applicable,
        "implemented": implemented,
        "responsible": responsible,
        "status": status,
    }


@router.get(
    "/projects/{project_id}/grc/soa",
    response_model=SoaResponse,
)
async def list_statement_of_applicability(
    project_id: UUID,
    search: str = Query("", max_length=200),
    iso_reference: str | None = None,
    applicable: str | None = None,
    implemented: str | None = None,
    responsible: str | None = None,
    status: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    try:
        assessment = await get_or_create_assessment(db, project_id)
        project = await db.get(Project, project_id)
        return await get_statement_of_applicability(
            db,
            project_id,
            assessment.id,
            project_name=project.name if project else "",
            search=search,
            iso_reference=iso_reference,
            applicable=applicable,
            implemented=implemented,
            responsible=responsible,
            status=status,
            page=page,
            page_size=page_size,
        )
    except ValueError as e:
        raise HTTPException(404, str(e)) from e


@router.get("/projects/{project_id}/grc/soa/export")
async def export_statement_of_applicability(
    project_id: UUID,
    format: str = Query("csv", pattern="^(csv|xlsx|pdf)$"),
    search: str = Query("", max_length=200),
    iso_reference: str | None = None,
    applicable: str | None = None,
    implemented: str | None = None,
    responsible: str | None = None,
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    try:
        assessment = await get_or_create_assessment(db, project_id)
        project = await db.get(Project, project_id)
        summary, rows = await get_soa_for_export(
            db,
            project_id,
            assessment.id,
            project_name=project.name if project else "",
            **_export_filters(
                search,
                iso_reference,
                applicable,
                implemented,
                responsible,
                status,
            ),
        )

        if format == "csv":
            content = export_soa_csv(rows)
            media_type = "text/csv; charset=utf-8"
            filename = "declaration-applicabilite.csv"
        elif format == "xlsx":
            content = export_soa_xlsx(rows, summary=summary)
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            filename = "declaration-applicabilite.xlsx"
        else:
            content = export_soa_pdf(
                rows,
                summary=summary,
                project_name=project.name if project else "",
            )
            media_type = "application/pdf"
            filename = "declaration-applicabilite.pdf"

        return Response(
            content=content,
            media_type=media_type,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except ValueError as e:
        raise HTTPException(404, str(e)) from e
