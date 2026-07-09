"""Services EBIOS RM — orchestration des ateliers (squelette).

Isolation des études
---------------------
Une étude EBIOS (:class:`EbiosAssessment`) est rattachée à un ``project_id``
ET à un ``cartography_id`` : la cartographie constitue la source de données
de l'étude (biens supports importés en atelier 2, acteurs en atelier 5…),
mais chaque cartographie possède sa ou ses propres études, jamais partagées.
Le study_id est simplement l'``id`` de l':class:`EbiosAssessment`.

Ainsi, créer une nouvelle cartographie (ou en importer une nouvelle version)
ne fait jamais réapparaître les ateliers, scores ou documents d'une étude
précédente : :func:`get_or_create_assessment` ne résout jamais qu'une étude
existante pour la cartographie demandée, et en crée une nouvelle — totalement
vierge (aucun atelier rempli, 0 % de progression, ateliers 2 à 5 verrouillés)
— si aucune n'existe encore pour cette cartographie.
"""

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


async def _resolve_cartography_id(db: AsyncSession, project_id: UUID) -> UUID | None:
    """Résout la cartographie active du projet — source de données par défaut
    d'une étude EBIOS quand aucune cartographie n'est explicitement précisée."""
    from app.services import cartography_service

    try:
        cartography = await cartography_service.get_active_cartography(db, project_id)
    except cartography_service.CartographyError:
        return None
    return cartography.id


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


def _seed_default_reference_documents(assessment_id: UUID) -> list[EbiosRecord]:
    """Socle documentaire par défaut d'une nouvelle étude (§ Documents de
    référence — Atelier 1) : toujours ``proposed``, jamais validé d'office."""
    from app.services.ebios.workshop1_default_documents import (
        build_default_reference_document_proposals,
    )

    records: list[EbiosRecord] = []
    for proposal in build_default_reference_document_proposals():
        records.append(
            EbiosRecord(
                assessment_id=assessment_id,
                workshop_number=1,
                record_type="reference_document",
                label=proposal["label"],
                description=proposal["description"],
                properties=proposal["properties"],
                status="proposed",
            )
        )
    return records


async def get_or_create_assessment(
    db: AsyncSession, project_id: UUID, cartography_id: UUID | None = None
) -> EbiosAssessment:
    """Résout l'étude EBIOS d'une cartographie (par défaut la cartographie
    active du projet), et en crée une nouvelle — totalement vierge — si aucune
    n'existe encore pour cette cartographie précise (§ isolation des études)."""
    await _get_project(db, project_id)
    if cartography_id is None:
        cartography_id = await _resolve_cartography_id(db, project_id)

    query = select(EbiosAssessment).where(EbiosAssessment.project_id == project_id)
    query = query.where(EbiosAssessment.cartography_id == cartography_id)
    result = await db.execute(query.order_by(EbiosAssessment.created_at.desc()).limit(1))
    existing = result.scalar_one_or_none()
    if existing:
        return existing

    assessment = EbiosAssessment(project_id=project_id, cartography_id=cartography_id)
    db.add(assessment)
    await db.flush()
    db.add_all(_seed_workshops(assessment.id))
    db.add_all(_seed_default_reference_documents(assessment.id))
    await db.commit()
    await db.refresh(assessment)
    return assessment


async def create_assessment(
    db: AsyncSession,
    project_id: UUID,
    title: str,
    description: str | None = None,
    cartography_id: UUID | None = None,
) -> EbiosAssessment:
    await _get_project(db, project_id)
    if cartography_id is None:
        cartography_id = await _resolve_cartography_id(db, project_id)
    assessment = EbiosAssessment(
        project_id=project_id, cartography_id=cartography_id, title=title, description=description
    )
    db.add(assessment)
    await db.flush()
    db.add_all(_seed_workshops(assessment.id))
    db.add_all(_seed_default_reference_documents(assessment.id))
    await db.commit()
    await db.refresh(assessment)
    return assessment


async def get_assessment(db: AsyncSession, project_id: UUID, assessment_id: UUID) -> EbiosAssessment:
    assessment = await db.get(EbiosAssessment, assessment_id)
    if not assessment or assessment.project_id != project_id:
        raise ValueError("Analyse EBIOS introuvable")
    return assessment


async def list_assessments(
    db: AsyncSession, project_id: UUID, cartography_id: UUID | None = None
) -> list[EbiosAssessment]:
    """Liste les études EBIOS d'un projet, éventuellement filtrées par
    cartographie — chaque étude reste indépendante (aucune donnée partagée)."""
    await _get_project(db, project_id)
    query = select(EbiosAssessment).where(EbiosAssessment.project_id == project_id)
    if cartography_id is not None:
        query = query.where(EbiosAssessment.cartography_id == cartography_id)
    query = query.order_by(EbiosAssessment.created_at.desc())
    result = await db.execute(query)
    return list(result.scalars().all())


async def backfill_assessment_cartography_ids(db: AsyncSession) -> int:
    """Backfill de démarrage — rattache les études EBIOS créées avant
    l'introduction du scoping par cartographie à la cartographie active de
    leur projet (idempotent, aucune donnée déplacée entre études)."""
    result = await db.execute(
        select(EbiosAssessment).where(EbiosAssessment.cartography_id.is_(None))
    )
    assessments = list(result.scalars().all())
    updated = 0
    for assessment in assessments:
        cartography_id = await _resolve_cartography_id(db, assessment.project_id)
        if cartography_id is None:
            continue
        assessment.cartography_id = cartography_id
        updated += 1
    if updated:
        await db.commit()
    return updated


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
