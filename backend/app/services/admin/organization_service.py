"""Service CRUD — organisations."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admin import Organization
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
