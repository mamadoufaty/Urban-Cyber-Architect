"""Routes API — livrables documentaires."""

from __future__ import annotations

import re
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.deliverables import (
    DeliverableDetail,
    DeliverableGenerateRequest,
    DeliverableGenerateResponse,
    DeliverableListResponse,
)
from app.services.deliverables.deliverable_export import (
    export_deliverable_docx,
    export_deliverable_markdown,
    export_deliverable_pdf,
)
from app.services.deliverables.deliverable_generator import (
    generate_deliverable,
    get_project_deliverable,
    list_project_deliverables,
)

router = APIRouter(tags=["deliverables"])


def _safe_filename(title: str) -> str:
    slug = re.sub(r"[^\w\-]+", "_", title.strip(), flags=re.UNICODE).strip("_")
    return slug[:80] or "livrable"


@router.get(
    "/projects/{project_id}/deliverables",
    response_model=DeliverableListResponse,
)
async def list_deliverables(project_id: UUID, db: AsyncSession = Depends(get_db)):
    try:
        return await list_project_deliverables(db, project_id)
    except ValueError as e:
        raise HTTPException(404, str(e)) from e


@router.post(
    "/projects/{project_id}/deliverables/generate",
    response_model=DeliverableGenerateResponse,
)
async def create_deliverable(
    project_id: UUID,
    body: DeliverableGenerateRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        result = await generate_deliverable(
            db,
            project_id,
            title=body.title,
            deliverable_type=body.deliverable_type,
            user_need=body.user_need,
            data_sources=body.data_sources,
            export_format=body.export_format,
            preview=body.preview,
        )
        return DeliverableGenerateResponse(
            preview=result["preview"],
            deliverable=DeliverableDetail(**result["deliverable"]) if result.get("deliverable") else None,
            generated_content=result["generated_content"],
        )
    except ValueError as e:
        raise HTTPException(404, str(e)) from e


@router.get(
    "/projects/{project_id}/deliverables/{deliverable_id}",
    response_model=DeliverableDetail,
)
async def read_deliverable(
    project_id: UUID,
    deliverable_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    try:
        return await get_project_deliverable(db, project_id, deliverable_id)
    except ValueError as e:
        raise HTTPException(404, str(e)) from e


@router.get("/projects/{project_id}/deliverables/{deliverable_id}/export")
async def export_deliverable(
    project_id: UUID,
    deliverable_id: UUID,
    format: str = Query("pdf", pattern="^(pdf|markdown|docx)$"),
    db: AsyncSession = Depends(get_db),
):
    try:
        record = await get_project_deliverable(db, project_id, deliverable_id)
    except ValueError as e:
        raise HTTPException(404, str(e)) from e

    content = record.get("generated_content") or {}
    filename_base = _safe_filename(str(record.get("title") or "livrable"))

    if format == "pdf":
        data = export_deliverable_pdf(content)
        return Response(
            content=data,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename_base}.pdf"'},
        )
    if format == "docx":
        data = export_deliverable_docx(content)
        return Response(
            content=data,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f'attachment; filename="{filename_base}.docx"'},
        )
    data = export_deliverable_markdown(content)
    return Response(
        content=data,
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename_base}.md"'},
    )
