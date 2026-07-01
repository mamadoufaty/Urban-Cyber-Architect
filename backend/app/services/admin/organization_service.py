"""Service CRUD — organisations."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admin import Organization, User
from app.models.entities import Project
from app.schemas.admin import OrganizationCreate, OrganizationUpdate


async def list_organizations(db: AsyncSession) -> tuple[list[Organization], int]:
    total = await db.scalar(select(func.count()).select_from(Organization)) or 0
    result = await db.execute(select(Organization).order_by(Organization.name))
    return list(result.scalars().all()), total


async def get_organization(db: AsyncSession, organization_id: UUID) -> Organization:
    org = await db.get(Organization, organization_id)
    if not org:
        raise ValueError("Organisation introuvable")
    return org


async def create_organization(db: AsyncSession, data: OrganizationCreate) -> Organization:
    existing = await db.execute(select(Organization).where(Organization.code == data.code))
    if existing.scalar_one_or_none():
        raise ValueError("Une organisation avec ce code existe déjà")
    org = Organization(
        name=data.name,
        code=data.code,
        description=data.description,
        status=data.status,
    )
    db.add(org)
    await db.flush()
    return org


async def update_organization(
    db: AsyncSession, organization_id: UUID, data: OrganizationUpdate
) -> Organization:
    org = await get_organization(db, organization_id)
    if data.name is not None:
        org.name = data.name
    if data.description is not None:
        org.description = data.description
    if data.status is not None:
        org.status = data.status
    org.updated_at = datetime.now(timezone.utc)
    await db.flush()
    return org


async def archive_organization(db: AsyncSession, organization_id: UUID) -> Organization:
    org = await get_organization(db, organization_id)
    org.status = "archived"
    org.updated_at = datetime.now(timezone.utc)
    await db.flush()
    return org


async def activate_organization(db: AsyncSession, organization_id: UUID) -> Organization:
    org = await get_organization(db, organization_id)
    org.status = "active"
    org.updated_at = datetime.now(timezone.utc)
    await db.flush()
    return org


async def deactivate_organization(db: AsyncSession, organization_id: UUID) -> Organization:
    return await archive_organization(db, organization_id)


async def delete_organization(db: AsyncSession, organization_id: UUID) -> None:
    org = await get_organization(db, organization_id)
    user_count = await db.scalar(
        select(func.count()).select_from(User).where(User.organization_id == organization_id)
    )
    if user_count and user_count > 0:
        raise ValueError("Impossible de supprimer : des utilisateurs sont rattachés à cette organisation")
    project_count = await db.scalar(
        select(func.count()).select_from(Project).where(Project.organization_id == organization_id)
    )
    if project_count and project_count > 0:
        raise ValueError("Impossible de supprimer : des projets sont rattachés à cette organisation")
    await db.delete(org)
    await db.flush()
