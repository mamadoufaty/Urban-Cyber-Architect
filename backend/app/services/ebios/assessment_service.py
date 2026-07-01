"""Services EBIOS RM — orchestration des ateliers (squelette)."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.metamodel.ebios import WORKSHOPS, default_workshop_content
from app.models.ebios import EbiosAssessment, EbiosLink, EbiosRecord, EbiosWorkshop
from app.models.entities import Project


async def _get_project(db: AsyncSession, project_id: UUID) -> Project:
    project = await db.get(Project, project_id)
    if not project:
        raise ValueError("Projet introuvable")
    return project


def _seed_workshops(assessment_id: UUID) -> list[EbiosWorkshop]:
    workshops: list[EbiosWorkshop] = []
    for index, spec in enumerate(WORKSHOPS):
        workshops.append(
            EbiosWorkshop(
                assessment_id=assessment_id,
                workshop_number=spec["number"],
                code=spec["code"],
                status="available" if index == 0 else "locked",
                progress_percent=0,
                summary={"label": spec["label"]},
                content=default_workshop_content(spec["code"]),
            )
        )
    return workshops


async def get_or_create_assessment(db: AsyncSession, project_id: UUID) -> EbiosAssessment:
    await _get_project(db, project_id)
    result = await db.execute(
        select(EbiosAssessment)
        .where(EbiosAssessment.project_id == project_id)
        .order_by(EbiosAssessment.created_at.desc())
        .limit(1)
    )
    existing = result.scalar_one_or_none()
    if existing:
        return existing

    assessment = EbiosAssessment(project_id=project_id)
    db.add(assessment)
    await db.flush()
    db.add_all(_seed_workshops(assessment.id))
    await db.commit()
    await db.refresh(assessment)
    return assessment


async def create_assessment(
    db: AsyncSession, project_id: UUID, title: str, description: str | None = None
) -> EbiosAssessment:
    await _get_project(db, project_id)
    assessment = EbiosAssessment(project_id=project_id, title=title, description=description)
    db.add(assessment)
    await db.flush()
    db.add_all(_seed_workshops(assessment.id))
    await db.commit()
    await db.refresh(assessment)
    return assessment


async def get_assessment(db: AsyncSession, project_id: UUID, assessment_id: UUID) -> EbiosAssessment:
    assessment = await db.get(EbiosAssessment, assessment_id)
    if not assessment or assessment.project_id != project_id:
        raise ValueError("Analyse EBIOS introuvable")
    return assessment


async def list_workshops(db: AsyncSession, assessment_id: UUID) -> list[EbiosWorkshop]:
    result = await db.execute(
        select(EbiosWorkshop)
        .where(EbiosWorkshop.assessment_id == assessment_id)
        .order_by(EbiosWorkshop.workshop_number)
    )
    return list(result.scalars().all())


async def get_workshop(db: AsyncSession, assessment_id: UUID, workshop_number: int) -> EbiosWorkshop:
    result = await db.execute(
        select(EbiosWorkshop).where(
            EbiosWorkshop.assessment_id == assessment_id,
            EbiosWorkshop.workshop_number == workshop_number,
        )
    )
    workshop = result.scalar_one_or_none()
    if not workshop:
        raise ValueError("Atelier introuvable")
    return workshop


async def list_records(
    db: AsyncSession,
    assessment_id: UUID,
    workshop_number: int | None = None,
) -> list[EbiosRecord]:
    query = select(EbiosRecord).where(EbiosRecord.assessment_id == assessment_id)
    if workshop_number is not None:
        query = query.where(EbiosRecord.workshop_number == workshop_number)
    query = query.order_by(EbiosRecord.workshop_number, EbiosRecord.sort_order, EbiosRecord.label)
    result = await db.execute(query)
    return list(result.scalars().all())


async def create_record(
    db: AsyncSession,
    assessment_id: UUID,
    workshop_number: int,
    record_type: str,
    label: str,
    description: str | None = None,
    properties: dict | None = None,
    status: str = "draft",
    sort_order: int = 0,
) -> EbiosRecord:
    record = EbiosRecord(
        assessment_id=assessment_id,
        workshop_number=workshop_number,
        record_type=record_type,
        label=label,
        description=description,
        properties=properties or {},
        status=status,
        sort_order=sort_order,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


async def build_overview(db: AsyncSession, assessment: EbiosAssessment) -> dict:
    workshops = await list_workshops(db, assessment.id)
    counts_result = await db.execute(
        select(EbiosRecord.workshop_number, func.count())
        .where(EbiosRecord.assessment_id == assessment.id)
        .group_by(EbiosRecord.workshop_number)
    )
    record_counts = {str(row[0]): row[1] for row in counts_result.all()}
    link_count_result = await db.execute(
        select(func.count()).select_from(EbiosLink).where(EbiosLink.assessment_id == assessment.id)
    )
    link_count = link_count_result.scalar_one()
    overall = int(sum(w.progress_percent for w in workshops) / max(len(workshops), 1))
    return {
        "assessment": assessment,
        "workshops": workshops,
        "record_counts_by_workshop": record_counts,
        "link_count": link_count,
        "overall_progress_percent": overall,
    }
