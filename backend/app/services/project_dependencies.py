"""Comptage des dépendances projet avant suppression."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.deliverables import Deliverable
from app.models.ebios import EbiosAssessment, EbiosLink, EbiosRecord
from app.models.entities import (
    GraphEdge,
    GraphNode,
    HumanDecision,
    OrchestrationRun,
    UrbanismEntity,
    UrbanismRelation,
)


@dataclass
class ProjectDependencyItem:
    name: str
    count: int

    def to_dict(self) -> dict[str, int | str]:
        return {"name": self.name, "count": self.count}


@dataclass
class ProjectDependencies:
    items: list[ProjectDependencyItem]

    @property
    def has_blocking(self) -> bool:
        return any(item.count > 0 for item in self.items)

    def to_response_list(self) -> list[dict[str, int | str]]:
        return [item.to_dict() for item in self.items if item.count > 0]


async def _count(db: AsyncSession, model, project_id: UUID, **filters) -> int:
    stmt = select(func.count()).select_from(model).where(model.project_id == project_id)
    for key, value in filters.items():
        stmt = stmt.where(getattr(model, key) == value)
    return int(await db.scalar(stmt) or 0)


async def _count_ebios_records(db: AsyncSession, project_id: UUID) -> int:
    stmt = (
        select(func.count())
        .select_from(EbiosRecord)
        .join(EbiosAssessment, EbiosRecord.assessment_id == EbiosAssessment.id)
        .where(EbiosAssessment.project_id == project_id)
    )
    return int(await db.scalar(stmt) or 0)


async def _count_ebios_links(db: AsyncSession, project_id: UUID) -> int:
    stmt = (
        select(func.count())
        .select_from(EbiosLink)
        .join(EbiosAssessment, EbiosLink.assessment_id == EbiosAssessment.id)
        .where(EbiosAssessment.project_id == project_id)
    )
    return int(await db.scalar(stmt) or 0)


async def _count_grc_records(db: AsyncSession, project_id: UUID) -> int:
    """Enregistrements EBIOS ateliers 3+ (risques, mesures, traitements → GRC)."""
    stmt = (
        select(func.count())
        .select_from(EbiosRecord)
        .join(EbiosAssessment, EbiosRecord.assessment_id == EbiosAssessment.id)
        .where(
            EbiosAssessment.project_id == project_id,
            EbiosRecord.workshop_number >= 3,
        )
    )
    return int(await db.scalar(stmt) or 0)


async def collect_project_dependencies(db: AsyncSession, project_id: UUID) -> ProjectDependencies:
    urbanism_entities = await _count(db, UrbanismEntity, project_id)
    urbanism_relations = await _count(db, UrbanismRelation, project_id)
    deliverables = await _count(db, Deliverable, project_id)
    ebios_records = await _count_ebios_records(db, project_id)
    ebios_links = await _count_ebios_links(db, project_id)
    grc_records = await _count_grc_records(db, project_id)
    orchestrations = await _count(db, OrchestrationRun, project_id)
    decisions = await _count(db, HumanDecision, project_id)
    graph_nodes = await _count(db, GraphNode, project_id)
    graph_edges = await _count(db, GraphEdge, project_id)

    items = [
        ProjectDependencyItem("Urbanisme", urbanism_entities + urbanism_relations),
        ProjectDependencyItem("Livrables", deliverables),
        ProjectDependencyItem("EBIOS RM", ebios_records + ebios_links),
        ProjectDependencyItem("GRC", grc_records),
        ProjectDependencyItem("Orchestration IA", orchestrations + decisions),
        ProjectDependencyItem("Graphe de connaissances", graph_nodes + graph_edges),
    ]
    return ProjectDependencies(items=items)


async def delete_empty_ebios_assessments(db: AsyncSession, project_id: UUID) -> None:
    """Retire les coquilles d'évaluation EBIOS sans enregistrements ni liens."""
    result = await db.execute(
        select(EbiosAssessment).where(EbiosAssessment.project_id == project_id)
    )
    for assessment in result.scalars().all():
        record_count = await db.scalar(
            select(func.count()).select_from(EbiosRecord).where(
                EbiosRecord.assessment_id == assessment.id
            )
        )
        link_count = await db.scalar(
            select(func.count()).select_from(EbiosLink).where(
                EbiosLink.assessment_id == assessment.id
            )
        )
        if (record_count or 0) == 0 and (link_count or 0) == 0:
            await db.delete(assessment)
