"""Logique métier projet V1.3."""

from __future__ import annotations

import copy
import re
from datetime import date, datetime
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admin import User
from app.models.entities import Project
from app.models.project_core import ProjectMember
from app.services.projects.activity_service import log_project_activity
from app.services.projects.constants import (
    PROJECT_ACTIVITY_ARCHIVED,
    PROJECT_ACTIVITY_CREATED,
    PROJECT_ACTIVITY_DELETED,
    PROJECT_ACTIVITY_DUPLICATED,
    PROJECT_ACTIVITY_MEMBER_ADDED,
    PROJECT_ACTIVITY_MEMBER_REMOVED,
    PROJECT_ACTIVITY_UPDATED,
    PROJECT_ROLES,
)


def _slugify_code(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return (slug or "project")[:80]


async def ensure_unique_code(db: AsyncSession, base_code: str) -> str:
    code = base_code[:100]
    existing = await db.execute(select(Project.id).where(Project.code == code))
    if existing.scalar_one_or_none() is None:
        return code
    suffix = str(uuid4())[:8]
    return f"{code[:91]}-{suffix}"


async def create_project_entity(
    db: AsyncSession,
    *,
    name: str,
    description: str | None = None,
    organization: dict | None = None,
    referentials: list | None = None,
    objectives: list | None = None,
    urbanism: dict | None = None,
    code: str | None = None,
    client: str | None = None,
    organization_id: UUID | None = None,
    status: str = "draft",
    priority: str = "medium",
    start_date: date | None = None,
    end_date: date | None = None,
    owner_id: UUID | None = None,
    tags: list | None = None,
    created_by: UUID | None = None,
    user_id: UUID | None = None,
) -> Project:
    project_code = await ensure_unique_code(db, code or _slugify_code(name))

    project = Project(
        name=name,
        code=project_code,
        description=description,
        organization=organization or {},
        referentials=referentials or [],
        objectives=objectives or [],
        urbanism=urbanism or {},
        client=client,
        organization_id=organization_id,
        status=status,
        priority=priority,
        start_date=start_date,
        end_date=end_date,
        owner_id=owner_id,
        tags=tags or [],
        created_by=created_by,
    )
    db.add(project)
    await db.flush()
    await log_project_activity(
        db,
        project_id=project.id,
        action=PROJECT_ACTIVITY_CREATED,
        user_id=user_id or created_by,
        details={"name": project.name, "code": project.code},
    )
    return project


def apply_project_updates(project: Project, updates: dict) -> dict:
    changed: dict = {}
    for field, value in updates.items():
        if value is None:
            continue
        if field == "organization" and isinstance(value, dict):
            setattr(project, field, value)
            changed[field] = value
        elif getattr(project, field, None) != value:
            setattr(project, field, value)
            changed[field] = value
    return changed


async def duplicate_project_entity(
    db: AsyncSession,
    project: Project,
    *,
    user_id: UUID | None = None,
) -> Project:
    base_code = await ensure_unique_code(db, f"{project.code or _slugify_code(project.name)}-copy")
    clone = Project(
        name=f"{project.name} (copie)",
        code=base_code,
        description=project.description,
        client=project.client,
        organization=copy.deepcopy(project.organization),
        referentials=copy.deepcopy(project.referentials),
        objectives=copy.deepcopy(project.objectives),
        urbanism=copy.deepcopy(project.urbanism),
        organization_id=project.organization_id,
        status="draft",
        priority=project.priority,
        start_date=project.start_date,
        end_date=project.end_date,
        owner_id=project.owner_id,
        tags=copy.deepcopy(project.tags),
        created_by=user_id or project.created_by,
    )
    db.add(clone)
    await db.flush()
    await log_project_activity(
        db,
        project_id=clone.id,
        action=PROJECT_ACTIVITY_CREATED,
        user_id=user_id,
        details={"name": clone.name, "source_project_id": str(project.id)},
    )
    await log_project_activity(
        db,
        project_id=project.id,
        action=PROJECT_ACTIVITY_DUPLICATED,
        user_id=user_id,
        details={"new_project_id": str(clone.id), "new_name": clone.name},
    )
    return clone


async def archive_project_entity(
    db: AsyncSession,
    project: Project,
    *,
    user_id: UUID | None = None,
) -> Project:
    if project.archived_at is not None:
        return project
    project.archived_at = datetime.utcnow()
    project.status = "archived"
    await log_project_activity(
        db,
        project_id=project.id,
        action=PROJECT_ACTIVITY_ARCHIVED,
        user_id=user_id,
        details={"name": project.name},
    )
    return project


async def log_project_update(
    db: AsyncSession,
    project: Project,
    changed: dict,
    *,
    user_id: UUID | None = None,
) -> None:
    if not changed:
        return
    await log_project_activity(
        db,
        project_id=project.id,
        action=PROJECT_ACTIVITY_UPDATED,
        user_id=user_id,
        details={"fields": list(changed.keys()), "changes": changed},
    )


async def log_project_delete(
    db: AsyncSession,
    project: Project,
    *,
    user_id: UUID | None = None,
) -> None:
    await log_project_activity(
        db,
        project_id=project.id,
        action=PROJECT_ACTIVITY_DELETED,
        user_id=user_id,
        details={"name": project.name, "code": project.code},
    )


def validate_project_role(role: str) -> None:
    if role not in PROJECT_ROLES:
        allowed = ", ".join(sorted(PROJECT_ROLES))
        raise ValueError(f"Rôle projet invalide. Valeurs autorisées : {allowed}")


async def add_project_member(
    db: AsyncSession,
    project: Project,
    *,
    user_id: UUID,
    project_role: str,
    actor_id: UUID | None = None,
) -> ProjectMember:
    validate_project_role(project_role)
    user = await db.get(User, user_id)
    if not user:
        raise LookupError("Utilisateur introuvable")

    existing = await db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == project.id,
            ProjectMember.user_id == user_id,
        )
    )
    if existing.scalar_one_or_none():
        raise ValueError("Cet utilisateur est déjà membre du projet")

    member = ProjectMember(
        project_id=project.id,
        user_id=user_id,
        project_role=project_role,
    )
    db.add(member)
    await db.flush()
    await log_project_activity(
        db,
        project_id=project.id,
        action=PROJECT_ACTIVITY_MEMBER_ADDED,
        user_id=actor_id,
        details={
            "member_id": str(member.id),
            "user_id": str(user_id),
            "project_role": project_role,
            "username": user.username,
        },
    )
    return member


async def remove_project_member(
    db: AsyncSession,
    project: Project,
    member: ProjectMember,
    *,
    actor_id: UUID | None = None,
) -> None:
    await log_project_activity(
        db,
        project_id=project.id,
        action=PROJECT_ACTIVITY_MEMBER_REMOVED,
        user_id=actor_id,
        details={
            "member_id": str(member.id),
            "user_id": str(member.user_id),
            "project_role": member.project_role,
        },
    )
    await db.delete(member)
