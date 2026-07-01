from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.entities import Project
from app.models.project_core import ProjectActivity, ProjectMember
from app.schemas.api import (
    ProjectActivityResponse,
    ProjectCreate,
    ProjectMemberCreate,
    ProjectMemberResponse,
    ProjectResponse,
    ProjectUpdate,
)
from app.services.project_dependencies import collect_project_dependencies, delete_empty_ebios_assessments
from app.services.project_templates import apply_template, list_templates
from app.services.projects.project_service import (
    add_project_member,
    apply_project_updates,
    archive_project_entity,
    create_project_entity,
    duplicate_project_entity,
    log_project_delete,
    log_project_update,
    remove_project_member,
)

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
        project = await create_project_entity(
            db,
            name=payload["name"],
            description=data.description or payload.get("description"),
            organization=org,
            referentials=payload.get("referentials", []),
            objectives=payload.get("objectives", []),
            urbanism=payload.get("urbanism", {}),
            code=data.code,
            client=data.client,
            organization_id=data.organization_id,
            status=data.status or "draft",
            priority=data.priority or "medium",
            start_date=data.start_date,
            end_date=data.end_date,
            owner_id=data.owner_id,
            tags=data.tags,
            created_by=data.created_by,
            user_id=data.created_by,
        )
    else:
        from app.services.urbanism_schema import _empty_club_urba

        org = data.organization.model_dump() if data.organization else {
            "name": data.name, "sector": "generic", "size": "PME", "country": "France"
        }
        urbanism = data.urbanism if data.urbanism else {"club_urba": _empty_club_urba()}
        if "club_urba" not in urbanism:
            urbanism = {**urbanism, "club_urba": _empty_club_urba()}

        project = await create_project_entity(
            db,
            name=data.name,
            description=data.description,
            organization=org,
            referentials=data.referentials,
            objectives=data.objectives,
            urbanism=urbanism,
            code=data.code,
            client=data.client,
            organization_id=data.organization_id,
            status=data.status or "draft",
            priority=data.priority or "medium",
            start_date=data.start_date,
            end_date=data.end_date,
            owner_id=data.owner_id,
            tags=data.tags,
            created_by=data.created_by,
            user_id=data.created_by,
        )

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

    updates = data.model_dump(exclude_unset=True)
    if "organization" in updates and updates["organization"] is not None:
        updates["organization"] = updates["organization"]
    changed = apply_project_updates(project, updates)
    await log_project_update(db, project, changed)
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

    await log_project_delete(db, project)
    await delete_empty_ebios_assessments(db, project_id)
    await db.delete(project)
    await db.commit()


@router.post("/{project_id}/archive", response_model=ProjectResponse)
async def archive_project(project_id: UUID, db: AsyncSession = Depends(get_db)):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    project = await archive_project_entity(db, project)
    await db.commit()
    await db.refresh(project)
    return project


@router.post("/{project_id}/duplicate", response_model=ProjectResponse, status_code=201)
async def duplicate_project(project_id: UUID, db: AsyncSession = Depends(get_db)):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "Project not found")

    clone = await duplicate_project_entity(db, project)
    await db.commit()
    await db.refresh(clone)
    return clone


@router.get("/{project_id}/members", response_model=list[ProjectMemberResponse])
async def list_project_members(project_id: UUID, db: AsyncSession = Depends(get_db)):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    result = await db.execute(
        select(ProjectMember)
        .where(ProjectMember.project_id == project_id)
        .order_by(ProjectMember.created_at.asc())
    )
    return result.scalars().all()


@router.post("/{project_id}/members", response_model=ProjectMemberResponse, status_code=201)
async def create_project_member(
    project_id: UUID,
    data: ProjectMemberCreate,
    db: AsyncSession = Depends(get_db),
):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    try:
        member = await add_project_member(
            db,
            project,
            user_id=data.user_id,
            project_role=data.project_role,
        )
    except LookupError as e:
        raise HTTPException(404, str(e)) from e
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    await db.commit()
    await db.refresh(member)
    return member


@router.delete("/{project_id}/members/{member_id}", status_code=204)
async def delete_project_member(
    project_id: UUID,
    member_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    member = await db.get(ProjectMember, member_id)
    if not member or member.project_id != project_id:
        raise HTTPException(404, "Member not found")
    await remove_project_member(db, project, member)
    await db.commit()


@router.get("/{project_id}/activity", response_model=list[ProjectActivityResponse])
async def list_project_activity(project_id: UUID, db: AsyncSession = Depends(get_db)):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    result = await db.execute(
        select(ProjectActivity)
        .where(ProjectActivity.project_id == project_id)
        .order_by(ProjectActivity.created_at.desc())
    )
    return result.scalars().all()


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
