"""Atelier 3 EBIOS RM — scénarios stratégiques et progression."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ebios import EbiosLink, EbiosRecord
from app.services.ebios.assessment_service import get_workshop, list_records
from app.services.ebios.strategic_scenario_generator import (
    WORKFLOW_MODIFIED,
    WORKFLOW_VALIDATED,
    generate_strategic_scenario,
)
from app.services.ebios.workshop2_service import is_risk_source_complete

LINK_DERIVES_FROM_RISK = "derives_from_risk_source"


def _props(record) -> dict:
    return record.properties or {}


def is_scenario_validated(record) -> bool:
    return (
        record.record_type == "strategic_scenario"
        and _props(record).get("workflow_status") == WORKFLOW_VALIDATED
    )


def compute_workshop3_progress(scenarios) -> int:
    strategic = [r for r in scenarios if r.record_type == "strategic_scenario"]
    if not strategic:
        return 0
    validated = sum(1 for s in strategic if is_scenario_validated(s))
    return int(validated / len(strategic) * 100)


async def _scenario_for_risk_source(
    db: AsyncSession, assessment_id: UUID, risk_source_id: UUID
) -> EbiosRecord | None:
    result = await db.execute(
        select(EbiosRecord).where(
            EbiosRecord.assessment_id == assessment_id,
            EbiosRecord.workshop_number == 3,
            EbiosRecord.record_type == "strategic_scenario",
        )
    )
    for record in result.scalars().all():
        if str(_props(record).get("risk_source_id")) == str(risk_source_id):
            return record
    return None


async def _delete_scenario_links(
    db: AsyncSession, assessment_id: UUID, scenario_id: UUID
) -> None:
    await db.execute(
        delete(EbiosLink).where(
            EbiosLink.assessment_id == assessment_id,
            EbiosLink.source_record_id == scenario_id,
        )
    )


async def sync_scenario_graph(db: AsyncSession, scenario: EbiosRecord) -> None:
    props = _props(scenario)
    risk_source_id = props.get("risk_source_id")
    if not risk_source_id:
        return
    await _delete_scenario_links(db, scenario.assessment_id, scenario.id)
    db.add(
        EbiosLink(
            assessment_id=scenario.assessment_id,
            source_record_id=scenario.id,
            target_record_id=UUID(str(risk_source_id)),
            link_type=LINK_DERIVES_FROM_RISK,
            properties={"scenario_uid": props.get("scenario_uid")},
        )
    )


async def cleanup_scenario_graph(db: AsyncSession, assessment_id: UUID, scenario_id: UUID) -> None:
    await _delete_scenario_links(db, assessment_id, scenario_id)


async def generate_strategic_scenarios(
    db: AsyncSession,
    assessment_id: UUID,
    *,
    regenerate: bool = False,
) -> list[EbiosRecord]:
    w2_records = await list_records(db, assessment_id, workshop_number=2)
    w1_records = await list_records(db, assessment_id, workshop_number=1)
    complete_sources = [r for r in w2_records if is_risk_source_complete(r)]
    stakeholder_records = [r for r in w1_records if r.record_type == "stakeholder"]
    asset_records = [r for r in w2_records if r.record_type == "supporting_asset"]

    if regenerate:
        existing = await list_records(db, assessment_id, workshop_number=3)
        for record in existing:
            if record.record_type == "strategic_scenario":
                await cleanup_scenario_graph(db, assessment_id, record.id)
                await db.delete(record)
        await db.flush()

    created: list[EbiosRecord] = []
    for source in complete_sources:
        if not regenerate:
            existing = await _scenario_for_risk_source(db, assessment_id, source.id)
            if existing:
                continue
        generated = generate_strategic_scenario(source, stakeholder_records, asset_records, auto=True)
        scenario = EbiosRecord(
            assessment_id=assessment_id,
            workshop_number=3,
            record_type="strategic_scenario",
            label=generated["title"],
            description=generated["narrative_description"],
            properties={k: v for k, v in generated.items() if k != "title"},
            status="draft",
        )
        db.add(scenario)
        await db.flush()
        await sync_scenario_graph(db, scenario)
        created.append(scenario)

    await db.commit()
    for record in created:
        await db.refresh(record)
    return created


async def recalculate_workshop3_progress(db: AsyncSession, assessment_id: UUID) -> int:
    records = await list_records(db, assessment_id, workshop_number=3)
    progress = compute_workshop3_progress(records)

    workshop3 = await get_workshop(db, assessment_id, 3)
    workshop3.progress_percent = progress

    if progress == 100:
        workshop3.status = "completed"
    elif progress > 0:
        workshop3.status = "in_progress"
    elif workshop3.status != "locked":
        workshop3.status = "available"

    workshop4 = await get_workshop(db, assessment_id, 4)
    if progress == 100:
        if workshop4.status == "locked":
            workshop4.status = "available"
    elif workshop4.progress_percent == 0 and workshop4.status == "available":
        workshop4.status = "locked"

    await db.commit()
    return progress


def mark_scenario_modified(record: EbiosRecord) -> None:
    props = _props(record)
    if props.get("workflow_status") not in (WORKFLOW_VALIDATED,):
        props["workflow_status"] = WORKFLOW_MODIFIED
        record.properties = props
