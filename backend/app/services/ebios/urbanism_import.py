"""Import des biens supports depuis la cartographie urbanisme (lecture seule)."""

from __future__ import annotations

from collections import defaultdict
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ebios import EbiosLink, EbiosRecord
from app.models.entities import UrbanismEntity

LINK_IMPACTS_ASSET = "impacts_asset"


def _urbanism_entity_id(record: EbiosRecord) -> str | None:
    value = (record.properties or {}).get("urbanism_entity_id")
    return str(value) if value else None


def _asset_props(entity: UrbanismEntity) -> dict:
    return {
        "urbanism_entity_id": str(entity.id),
        "entity_type": entity.entity_type,
        "couche": entity.couche,
        "import_source": "urbanism",
        "scenario_seed": {"strategic_ready": True, "operational_ready": True},
    }


async def _rewire_asset_references(
    db: AsyncSession,
    assessment_id: UUID,
    deleted_ids: set[str],
    id_remap: dict[str, str],
) -> None:
    if not deleted_ids:
        return

    result = await db.execute(
        select(EbiosRecord).where(
            EbiosRecord.assessment_id == assessment_id,
            EbiosRecord.workshop_number == 2,
            EbiosRecord.record_type == "risk_source",
        )
    )
    for record in result.scalars().all():
        props = dict(record.properties or {})
        asset_ids = [str(x) for x in props.get("supporting_asset_ids", [])]
        if not any(aid in deleted_ids for aid in asset_ids):
            continue
        seen: set[str] = set()
        remapped: list[str] = []
        for aid in asset_ids:
            target = id_remap.get(aid, aid)
            if target in deleted_ids or target in seen:
                continue
            seen.add(target)
            remapped.append(target)
        props["supporting_asset_ids"] = remapped
        record.properties = props

    link_result = await db.execute(
        select(EbiosLink).where(
            EbiosLink.assessment_id == assessment_id,
            EbiosLink.link_type == LINK_IMPACTS_ASSET,
            EbiosLink.target_record_id.in_([UUID(x) for x in deleted_ids]),
        )
    )
    for link in link_result.scalars().all():
        replacement = id_remap.get(str(link.target_record_id))
        if replacement:
            link.target_record_id = UUID(replacement)
        else:
            await db.delete(link)


async def _dedupe_existing_assets(
    existing: list[EbiosRecord],
) -> tuple[dict[str, EbiosRecord], list[EbiosRecord], dict[str, str]]:
    """Conserve un seul supporting_asset par urbanism_entity_id (le plus ancien)."""
    grouped: dict[str, list[EbiosRecord]] = defaultdict(list)
    for record in existing:
        uid = _urbanism_entity_id(record)
        if uid:
            grouped[uid].append(record)

    canonical: dict[str, EbiosRecord] = {}
    duplicates: list[EbiosRecord] = []
    id_remap: dict[str, str] = {}

    for uid, records in grouped.items():
        records.sort(key=lambda r: r.created_at)
        keeper = records[0]
        canonical[uid] = keeper
        for duplicate in records[1:]:
            duplicates.append(duplicate)
            id_remap[str(duplicate.id)] = str(keeper.id)

    return canonical, duplicates, id_remap


async def import_urbanism_supporting_assets(
    db: AsyncSession,
    assessment_id: UUID,
    project_id: UUID,
) -> tuple[list[EbiosRecord], int]:
    """Synchronise les biens supports — idempotent sur (assessment_id, urbanism_entity_id)."""
    urbanism_result = await db.execute(
        select(UrbanismEntity)
        .where(UrbanismEntity.project_id == project_id)
        .order_by(UrbanismEntity.couche, UrbanismEntity.label)
    )
    urbanism_entities = list(urbanism_result.scalars().all())

    existing_result = await db.execute(
        select(EbiosRecord).where(
            EbiosRecord.assessment_id == assessment_id,
            EbiosRecord.workshop_number == 2,
            EbiosRecord.record_type == "supporting_asset",
        )
    )
    existing = list(existing_result.scalars().all())

    canonical, duplicates, id_remap = await _dedupe_existing_assets(existing)
    deleted_ids = {str(r.id) for r in duplicates}

    if duplicates:
        await _rewire_asset_references(db, assessment_id, deleted_ids, id_remap)
        for duplicate in duplicates:
            await db.delete(duplicate)
        await db.flush()

    created: list[EbiosRecord] = []
    touched = False

    for entity in urbanism_entities:
        uid = str(entity.id)
        props = _asset_props(entity)

        if uid in canonical:
            record = canonical[uid]
            record.label = entity.label
            record.description = entity.description
            record.properties = {**(record.properties or {}), **props}
            touched = True
            continue

        record = EbiosRecord(
            assessment_id=assessment_id,
            workshop_number=2,
            record_type="supporting_asset",
            label=entity.label,
            description=entity.description,
            properties=props,
            status="imported",
        )
        db.add(record)
        created.append(record)
        canonical[uid] = record
        touched = True

    if touched:
        await db.commit()
        for record in created:
            await db.refresh(record)

    return created, len(created)
