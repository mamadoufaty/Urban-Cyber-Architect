"""Atelier 1 EBIOS RM — progression et déverrouillage de l'atelier 2."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.ebios.assessment_service import get_workshop, list_records

WORKSHOP1_SECTIONS = (
    "security_scope",
    "stakeholder",
    "security_baseline",
    "reference_document",
)
SECTION_WEIGHT = 25


def _scope_is_complete(records) -> bool:
    for record in records:
        if record.record_type == "security_scope" and record.label.strip():
            return True
    return False


def _has_record_type(records, record_type: str) -> bool:
    return any(r.record_type == record_type for r in records)


def compute_workshop1_progress(records) -> int:
    progress = 0
    if _scope_is_complete(records):
        progress += SECTION_WEIGHT
    for record_type in WORKSHOP1_SECTIONS[1:]:
        if _has_record_type(records, record_type):
            progress += SECTION_WEIGHT
    return progress


async def recalculate_workshop1_progress(db: AsyncSession, assessment_id: UUID) -> int:
    records = await list_records(db, assessment_id, workshop_number=1)
    progress = compute_workshop1_progress(records)

    workshop1 = await get_workshop(db, assessment_id, 1)
    workshop1.progress_percent = progress

    if progress == 100:
        workshop1.status = "completed"
    elif progress > 0:
        workshop1.status = "in_progress"
    else:
        workshop1.status = "available"

    workshop2 = await get_workshop(db, assessment_id, 2)
    if progress == 100:
        if workshop2.status == "locked":
            workshop2.status = "available"
    elif workshop2.progress_percent == 0 and workshop2.status == "available":
        workshop2.status = "locked"

    await db.commit()
    return progress
