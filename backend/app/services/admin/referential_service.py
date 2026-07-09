"""Service CRUD + seed — référentiels de conformité."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.referentials import ReferentialFramework
from app.schemas.admin import ReferentialCreate, ReferentialUpdate

# (code, label, category) — jeu initial repris de l'ancienne liste frontend.
REFERENTIAL_SEED: list[tuple[str, str, str]] = [
    ("rgpd", "RGPD", "Protection des données"),
    ("nis2", "NIS2", "Réglementation UE"),
    ("ebios-rm", "EBIOS RM", "Gestion des risques"),
    ("iso-27001", "ISO 27001", "Système de management"),
    ("iso-27002", "ISO 27002", "Mesures de sécurité"),
    ("iso-27005", "ISO 27005", "Gestion des risques"),
    ("iec-62443", "IEC 62443", "Sécurité industrielle"),
    ("anssi", "ANSSI", "Recommandations nationales"),
    ("dora", "DORA", "Réglementation UE"),
    ("hds", "HDS", "Santé"),
    ("pci-dss", "PCI DSS", "Paiement"),
    ("soc-2", "SOC 2", "Contrôle des services"),
]


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or "referentiel"


async def run_referential_seed(db: AsyncSession) -> None:
    """Seed idempotent — insère les référentiels manquants (par code)."""
    for index, (code, label, category) in enumerate(REFERENTIAL_SEED):
        existing = await db.execute(
            select(ReferentialFramework).where(ReferentialFramework.code == code)
        )
        if existing.scalar_one_or_none():
            continue
        db.add(
            ReferentialFramework(
                code=code,
                label=label,
                category=category,
                status="active",
                sort_order=index,
            )
        )
    await db.flush()


async def list_referentials(
    db: AsyncSession, *, active_only: bool = False
) -> tuple[list[ReferentialFramework], int]:
    stmt = select(ReferentialFramework)
    if active_only:
        stmt = stmt.where(ReferentialFramework.status == "active")
    stmt = stmt.order_by(ReferentialFramework.sort_order, ReferentialFramework.label)
    result = await db.execute(stmt)
    items = list(result.scalars().all())
    total = await db.scalar(select(func.count()).select_from(ReferentialFramework)) or 0
    return items, total


async def get_referential(db: AsyncSession, referential_id: UUID) -> ReferentialFramework:
    ref = await db.get(ReferentialFramework, referential_id)
    if not ref:
        raise ValueError("Référentiel introuvable")
    return ref


async def create_referential(db: AsyncSession, data: ReferentialCreate) -> ReferentialFramework:
    code = (data.code or slugify(data.label)).strip().lower()
    existing = await db.execute(
        select(ReferentialFramework).where(ReferentialFramework.code == code)
    )
    if existing.scalar_one_or_none():
        raise ValueError("Un référentiel avec ce code existe déjà")
    max_order = await db.scalar(select(func.max(ReferentialFramework.sort_order)))
    ref = ReferentialFramework(
        code=code,
        label=data.label.strip(),
        category=(data.category or None),
        description=(data.description or None),
        status=data.status or "active",
        sort_order=data.sort_order if data.sort_order is not None else (max_order or 0) + 1,
    )
    db.add(ref)
    await db.flush()
    return ref


async def update_referential(
    db: AsyncSession, referential_id: UUID, data: ReferentialUpdate
) -> ReferentialFramework:
    ref = await get_referential(db, referential_id)
    if data.label is not None:
        ref.label = data.label.strip()
    if data.category is not None:
        ref.category = data.category or None
    if data.description is not None:
        ref.description = data.description or None
    if data.status is not None:
        ref.status = data.status
    if data.sort_order is not None:
        ref.sort_order = data.sort_order
    ref.updated_at = datetime.now(timezone.utc)
    await db.flush()
    return ref


async def set_status(
    db: AsyncSession, referential_id: UUID, status: str
) -> ReferentialFramework:
    ref = await get_referential(db, referential_id)
    ref.status = status
    ref.updated_at = datetime.now(timezone.utc)
    await db.flush()
    return ref


async def delete_referential(db: AsyncSession, referential_id: UUID) -> None:
    ref = await get_referential(db, referential_id)
    await db.delete(ref)
    await db.flush()
