import copy
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.entities import Project
from app.schemas.api import ProjectCreate, ProjectResponse, ProjectUpdate
from app.services.project_dependencies import collect_project_dependencies, delete_empty_ebios_assessments
from app.services.project_templates import apply_template, list_templates

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("/templates/list")
async def get_project_templates():
    return list_templates()


@router.post("", response_model=ProjectResponse, status_code=201)
async def create_project(data: ProjectCreate, db: AsyncSession = Depends(get_db)):
    if data.template:
        try:
            payload = apply_template(data.template, data.name or None)
        except ValueError as e:
            raise HTTPException(400, str(e)) from e
        org = data.organization.model_dump() if data.organization else payload["organization"]
        project = Project(
            name=payload["name"],
            description=data.description or payload.get("description"),
            organization=org,
            referentials=payload.get("referentials", []),
            objectives=payload.get("objectives", []),
            urbanism=payload.get("urbanism", {}),
        )
    else:
        from app.services.urbanism_schema import _empty_club_urba

        org = data.organization.model_dump() if data.organization else {
            "name": data.name, "sector": "generic", "size": "PME", "country": "France"
        }
        urbanism = data.urbanism if data.urbanism else {"club_urba": _empty_club_urba()}
        if "club_urba" not in urbanism:
            urbanism = {**urbanism, "club_urba": _empty_club_urba()}

        project = Project(
            name=data.name,
            description=data.description,
            organization=org,
            referentials=data.referentials,
            objectives=data.objectives,
            urbanism=urbanism,
        )

    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project


@router.get("", response_model=list[ProjectResponse])
async def list_projects(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Project).order_by(Project.created_at.desc()))
    return result.scalars().all()


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: UUID, db: AsyncSession = Depends(get_db)):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    return project


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(project_id: UUID, data: ProjectUpdate, db: AsyncSession = Depends(get_db)):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "Project not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        if field == "organization" and value is not None:
            setattr(project, field, value)
        elif value is not None:
            setattr(project, field, value)

    await db.commit()
    await db.refresh(project)
    return project


@router.delete("/{project_id}", status_code=204)
async def delete_project(project_id: UUID, db: AsyncSession = Depends(get_db)):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "Project not found")

    dependencies = await collect_project_dependencies(db, project_id)
    if dependencies.has_blocking:
        return JSONResponse(
            status_code=409,
            content={
                "detail": "Impossible de supprimer ce projet car il contient des données liées.",
                "dependencies": dependencies.to_response_list(),
            },
        )

    await delete_empty_ebios_assessments(db, project_id)
    await db.delete(project)
    await db.commit()


@router.post("/{project_id}/duplicate", response_model=ProjectResponse, status_code=201)
async def duplicate_project(project_id: UUID, db: AsyncSession = Depends(get_db)):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "Project not found")

    clone = Project(
        name=f"{project.name} (copie)",
        description=project.description,
        organization=copy.deepcopy(project.organization),
        referentials=copy.deepcopy(project.referentials),
        objectives=copy.deepcopy(project.objectives),
        urbanism=copy.deepcopy(project.urbanism),
        status="draft",
    )
    db.add(clone)
    await db.commit()
    await db.refresh(clone)
    return clone


@router.get("/{project_id}/context")
async def get_project_context(project_id: UUID, db: AsyncSession = Depends(get_db)):
    from app.context.builder import ContextBuilder

    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "Project not found")

    builder = ContextBuilder()
    context = builder.build(
        {
            "id": str(project.id),
            "organization": project.organization,
            "referentials": project.referentials,
            "urbanism": project.urbanism,
            "objectives": project.objectives,
        }
    )
    from dataclasses import asdict
    return asdict(context)


@router.get("/{project_id}/urbanism-schema")
async def get_urbanism_schema(
    project_id: UUID,
    categories: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    from app.services.urbanism_engine import get_project_cartography

    cats = [c.strip() for c in categories.split(",") if c.strip()] if categories else None
    schema = await get_project_cartography(db, project_id, cats)
    if not schema:
        raise HTTPException(404, "Project not found")
    return schema
