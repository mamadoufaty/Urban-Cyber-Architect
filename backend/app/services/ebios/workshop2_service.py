"""Atelier 2 EBIOS RM — sources de risque, biens supports et progression."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ebios import EbiosLink, EbiosRecord
from app.services.ebios.assessment_service import get_workshop, list_records

SEVERITY_LEVELS = ("Faible", "Modérée", "Élevée", "Critique")
LINK_CONCERNS_STAKEHOLDER = "concerns_stakeholder"
LINK_IMPACTS_ASSET = "impacts_asset"
LINK_EXPRESSES_FEAR = "expresses_fear"
SECTION_WEIGHT = 25


def _props(record) -> dict:
    return record.properties or {}


def is_risk_source_complete(record) -> bool:
    if record.record_type != "risk_source":
        return False
    props = _props(record)
    if not record.label.strip():
        return False
    if not str(props.get("target_objective", "")).strip():
        return False
    if not str(props.get("feared_event", "")).strip():
        return False
    if props.get("severity") not in SEVERITY_LEVELS:
        return False
    if not props.get("stakeholder_ids"):
        return False
    if not props.get("supporting_asset_ids"):
        return False
    return True


def compute_workshop2_progress(records) -> int:
    complete = sum(1 for r in records if is_risk_source_complete(r))
    return min(100, complete * SECTION_WEIGHT)


async def _find_feared_event_for_source(
    db: AsyncSession, assessment_id: UUID, risk_source_id: UUID
) -> EbiosRecord | None:
    result = await db.execute(
        select(EbiosRecord).where(
            EbiosRecord.assessment_id == assessment_id,
            EbiosRecord.workshop_number == 2,
            EbiosRecord.record_type == "feared_event",
        )
    )
    for record in result.scalars().all():
        if str(_props(record).get("risk_source_id")) == str(risk_source_id):
            return record
    return None


async def _delete_outgoing_links(
    db: AsyncSession, assessment_id: UUID, source_record_id: UUID, link_types: tuple[str, ...]
) -> None:
    await db.execute(
        delete(EbiosLink).where(
            EbiosLink.assessment_id == assessment_id,
            EbiosLink.source_record_id == source_record_id,
            EbiosLink.link_type.in_(link_types),
        )
    )


async def sync_risk_source_graph(db: AsyncSession, risk_source: EbiosRecord) -> None:
    """Synchronise événement redouté et liens pour génération future de scénarios."""
    props = _props(risk_source)
    feared_text = str(props.get("feared_event", "")).strip()
    stakeholder_ids = [str(x) for x in props.get("stakeholder_ids", [])]
    asset_ids = [str(x) for x in props.get("supporting_asset_ids", [])]

    feared = await _find_feared_event_for_source(db, risk_source.assessment_id, risk_source.id)
    if feared_text:
        if feared:
            feared.label = feared_text
            feared.description = props.get("comment")
            feared.properties = {
                **(_props(feared)),
                "risk_source_id": str(risk_source.id),
                "severity": props.get("severity"),
                "target_objective": props.get("target_objective"),
                "scenario_seed": {"strategic_ready": True, "operational_ready": False},
            }
        else:
            feared = EbiosRecord(
                assessment_id=risk_source.assessment_id,
                workshop_number=2,
                record_type="feared_event",
                label=feared_text,
                description=props.get("comment"),
                properties={
                    "risk_source_id": str(risk_source.id),
                    "severity": props.get("severity"),
                    "target_objective": props.get("target_objective"),
                    "scenario_seed": {"strategic_ready": True, "operational_ready": False},
                },
            )
            db.add(feared)
            await db.flush()
    elif feared:
        await db.delete(feared)
        feared = None

    await _delete_outgoing_links(
        db,
        risk_source.assessment_id,
        risk_source.id,
        (LINK_CONCERNS_STAKEHOLDER, LINK_IMPACTS_ASSET, LINK_EXPRESSES_FEAR),
    )

    if feared:
        db.add(
            EbiosLink(
                assessment_id=risk_source.assessment_id,
                source_record_id=risk_source.id,
                target_record_id=feared.id,
                link_type=LINK_EXPRESSES_FEAR,
                properties={"method": "ebios_rm"},
            )
        )

    for stakeholder_id in stakeholder_ids:
        db.add(
            EbiosLink(
                assessment_id=risk_source.assessment_id,
                source_record_id=risk_source.id,
                target_record_id=UUID(stakeholder_id),
                link_type=LINK_CONCERNS_STAKEHOLDER,
                properties={},
            )
        )

    for asset_id in asset_ids:
        db.add(
            EbiosLink(
                assessment_id=risk_source.assessment_id,
                source_record_id=risk_source.id,
                target_record_id=UUID(asset_id),
                link_type=LINK_IMPACTS_ASSET,
                properties={},
            )
        )


async def cleanup_risk_source_graph(db: AsyncSession, assessment_id: UUID, risk_source_id: UUID) -> None:
    feared = await _find_feared_event_for_source(db, assessment_id, risk_source_id)
    await _delete_outgoing_links(
        db,
        assessment_id,
        risk_source_id,
        (LINK_CONCERNS_STAKEHOLDER, LINK_IMPACTS_ASSET, LINK_EXPRESSES_FEAR),
    )
    if feared:
        await db.delete(feared)


async def recalculate_workshop2_progress(db: AsyncSession, assessment_id: UUID) -> int:
    records = await list_records(db, assessment_id, workshop_number=2)
    progress = compute_workshop2_progress(records)

    workshop2 = await get_workshop(db, assessment_id, 2)
    workshop2.progress_percent = progress

    if progress == 100:
        workshop2.status = "completed"
    elif progress > 0:
        workshop2.status = "in_progress"
    elif workshop2.status != "locked":
        workshop2.status = "available"

    workshop3 = await get_workshop(db, assessment_id, 3)
    if progress == 100:
        if workshop3.status == "locked":
            workshop3.status = "available"
    elif workshop3.progress_percent == 0 and workshop3.status == "available":
        workshop3.status = "locked"

    await db.commit()
    return progress
