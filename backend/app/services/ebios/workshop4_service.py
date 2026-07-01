"""Atelier 4 EBIOS RM — scénarios opérationnels et progression."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ebios import EbiosLink, EbiosRecord
from app.services.ebios.assessment_service import get_workshop, list_records
from app.services.ebios.operational_scenario_generator import (
    WORKFLOW_MODIFIED,
    WORKFLOW_VALIDATED,
    generate_operational_scenario,
)
from app.services.ebios.workshop3_service import is_scenario_validated

LINK_GENERATES_OPERATIONAL = "generates_operational"
LINK_REFERENCES_ASSET = "references_supporting_asset"
LINK_REFERENCES_STAKEHOLDER = "references_stakeholder"
LINK_REFERENCES_RISK_SOURCE = "references_risk_source"


def _props(record) -> dict:
    return record.properties or {}


def is_operational_validated(record) -> bool:
    return (
        record.record_type == "operational_scenario"
        and _props(record).get("workflow_status") == WORKFLOW_VALIDATED
    )


def compute_workshop4_progress(scenarios) -> int:
    operational = [r for r in scenarios if r.record_type == "operational_scenario"]
    if not operational:
        return 0
    validated = sum(1 for s in operational if is_operational_validated(s))
    return int(validated / len(operational) * 100)


async def _operational_for_strategic(
    db: AsyncSession, assessment_id: UUID, strategic_id: UUID
) -> EbiosRecord | None:
    result = await db.execute(
        select(EbiosRecord).where(
            EbiosRecord.assessment_id == assessment_id,
            EbiosRecord.workshop_number == 4,
            EbiosRecord.record_type == "operational_scenario",
        )
    )
    for record in result.scalars().all():
        if str(_props(record).get("strategic_scenario_id")) == str(strategic_id):
            return record
    return None


async def _delete_operational_links(
    db: AsyncSession, assessment_id: UUID, operational_id: UUID
) -> None:
    await db.execute(
        delete(EbiosLink).where(
            EbiosLink.assessment_id == assessment_id,
            EbiosLink.source_record_id == operational_id,
        )
    )
    await db.execute(
        delete(EbiosLink).where(
            EbiosLink.assessment_id == assessment_id,
            EbiosLink.target_record_id == operational_id,
        )
    )


async def sync_operational_graph(
    db: AsyncSession,
    operational: EbiosRecord,
    strategic: EbiosRecord,
) -> None:
    props = _props(operational)
    await _delete_operational_links(db, operational.assessment_id, operational.id)

    db.add(
        EbiosLink(
            assessment_id=operational.assessment_id,
            source_record_id=strategic.id,
            target_record_id=operational.id,
            link_type=LINK_GENERATES_OPERATIONAL,
            properties={
                "strategic_scenario_uid": props.get("strategic_scenario_uid"),
                "operational_scenario_uid": props.get("operational_scenario_uid"),
            },
        )
    )

    risk_source_id = props.get("risk_source_id")
    if risk_source_id:
        db.add(
            EbiosLink(
                assessment_id=operational.assessment_id,
                source_record_id=operational.id,
                target_record_id=UUID(str(risk_source_id)),
                link_type=LINK_REFERENCES_RISK_SOURCE,
                properties={},
            )
        )

    for stakeholder_id in props.get("stakeholder_ids", []):
        db.add(
            EbiosLink(
                assessment_id=operational.assessment_id,
                source_record_id=operational.id,
                target_record_id=UUID(str(stakeholder_id)),
                link_type=LINK_REFERENCES_STAKEHOLDER,
                properties={},
            )
        )

    for asset_id in props.get("impacted_supporting_asset_ids", []):
        db.add(
            EbiosLink(
                assessment_id=operational.assessment_id,
                source_record_id=operational.id,
                target_record_id=UUID(str(asset_id)),
                link_type=LINK_REFERENCES_ASSET,
                properties={},
            )
        )


async def cleanup_operational_graph(
    db: AsyncSession, assessment_id: UUID, operational_id: UUID
) -> None:
    await _delete_operational_links(db, assessment_id, operational_id)


async def list_workshop4_scenarios(db: AsyncSession, assessment_id: UUID) -> list[EbiosRecord]:
    records = await list_records(db, assessment_id, workshop_number=4)
    return [r for r in records if r.record_type == "operational_scenario"]


async def generate_operational_scenarios(
    db: AsyncSession,
    assessment_id: UUID,
    *,
    regenerate: bool = False,
) -> list[EbiosRecord]:
    w3_records = await list_records(db, assessment_id, workshop_number=3)
    w2_records = await list_records(db, assessment_id, workshop_number=2)
    w1_records = await list_records(db, assessment_id, workshop_number=1)

    validated_strategic = [r for r in w3_records if is_scenario_validated(r)]
    stakeholder_records = [r for r in w1_records if r.record_type == "stakeholder"]
    asset_records = [r for r in w2_records if r.record_type == "supporting_asset"]
    risk_by_id = {str(r.id): r for r in w2_records if r.record_type == "risk_source"}

    if regenerate:
        existing = await list_workshop4_scenarios(db, assessment_id)
        for record in existing:
            await cleanup_operational_graph(db, assessment_id, record.id)
            await db.delete(record)
        await db.flush()

    created: list[EbiosRecord] = []
    for strategic in validated_strategic:
        if not regenerate:
            existing = await _operational_for_strategic(db, assessment_id, strategic.id)
            if existing:
                continue

        risk_source = risk_by_id.get(str(_props(strategic).get("risk_source_id", "")))
        generated = generate_operational_scenario(
            strategic, risk_source, stakeholder_records, asset_records, auto=True
        )
        operational = EbiosRecord(
            assessment_id=assessment_id,
            workshop_number=4,
            record_type="operational_scenario",
            label=generated["title"],
            description=generated["attack_path"],
            properties={k: v for k, v in generated.items() if k != "title"},
            status="draft",
        )
        db.add(operational)
        await db.flush()
        await sync_operational_graph(db, operational, strategic)
        created.append(operational)

    await db.commit()
    for record in created:
        await db.refresh(record)
    return created


async def update_operational_scenario(
    db: AsyncSession,
    assessment_id: UUID,
    scenario_id: UUID,
    *,
    label: str | None = None,
    properties: dict | None = None,
    validate: bool = False,
) -> EbiosRecord:
    record = await db.get(EbiosRecord, scenario_id)
    if (
        not record
        or record.assessment_id != assessment_id
        or record.workshop_number != 4
        or record.record_type != "operational_scenario"
    ):
        raise ValueError("Scénario opérationnel introuvable")

    if label is not None:
        record.label = label

    props = dict(_props(record))
    if properties:
        props = {**props, **properties}
    if validate:
        props["workflow_status"] = WORKFLOW_VALIDATED
    elif properties and props.get("workflow_status") != WORKFLOW_VALIDATED:
        props["workflow_status"] = WORKFLOW_MODIFIED
    record.properties = props

    strategic_id = props.get("strategic_scenario_id")
    if strategic_id:
        strategic = await db.get(EbiosRecord, UUID(str(strategic_id)))
        if strategic:
            await sync_operational_graph(db, record, strategic)

    await db.commit()
    await db.refresh(record)
    return record


async def delete_operational_scenario(
    db: AsyncSession, assessment_id: UUID, scenario_id: UUID
) -> None:
    record = await db.get(EbiosRecord, scenario_id)
    if (
        not record
        or record.assessment_id != assessment_id
        or record.record_type != "operational_scenario"
    ):
        raise ValueError("Scénario opérationnel introuvable")
    await cleanup_operational_graph(db, assessment_id, record.id)
    await db.delete(record)
    await db.commit()


async def recalculate_workshop4_progress(db: AsyncSession, assessment_id: UUID) -> int:
    records = await list_records(db, assessment_id, workshop_number=4)
    progress = compute_workshop4_progress(records)

    workshop4 = await get_workshop(db, assessment_id, 4)
    workshop4.progress_percent = progress

    if progress == 100:
        workshop4.status = "completed"
    elif progress > 0:
        workshop4.status = "in_progress"
    elif workshop4.status != "locked":
        workshop4.status = "available"

    workshop5 = await get_workshop(db, assessment_id, 5)
    if progress == 100:
        if workshop5.status == "locked":
            workshop5.status = "available"
    elif workshop5.progress_percent == 0 and workshop5.status == "available":
        workshop5.status = "locked"

    await db.commit()
    return progress


def mark_operational_modified(record: EbiosRecord) -> None:
    props = _props(record)
    if props.get("workflow_status") != WORKFLOW_VALIDATED:
        props["workflow_status"] = WORKFLOW_MODIFIED
        record.properties = props
