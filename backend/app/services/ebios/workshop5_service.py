"""Atelier 5 EBIOS RM — traitement des risques, PTR et progression."""

from __future__ import annotations

import uuid
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ebios import EbiosLink, EbiosRecord
from app.services.ebios.assessment_service import get_workshop, list_records
from app.services.ebios.risk_calculation import compute_initial_risk, compute_residual_risk
from app.services.ebios.security_measure_generator import (
    TREATMENT_DECISIONS,
    WORKFLOW_AUTO,
    WORKFLOW_VALIDATED,
    generate_ptr_action,
    generate_security_measures,
)
from app.services.ebios.urbanism_actor_resolver import load_urbanism_graph, resolve_urbanism_roles
from app.services.ebios.workshop4_service import is_operational_validated

LINK_TREATS_OPERATIONAL = "treats_operational"
LINK_EVALUATES_RISK = "evaluates_risk"
LINK_MITIGATES = "mitigates_evaluation"
LINK_IMPLEMENTS = "implements_measure"


def _props(record) -> dict:
    return record.properties or {}


def is_evaluation_validated(record) -> bool:
    return (
        record.record_type == "risk_evaluation"
        and _props(record).get("workflow_status") == WORKFLOW_VALIDATED
    )


def compute_workshop5_progress(records) -> int:
    evaluations = [r for r in records if r.record_type == "risk_evaluation"]
    if not evaluations:
        return 0
    validated = sum(1 for e in evaluations if is_evaluation_validated(e))
    return int(validated / len(evaluations) * 100)


async def _evaluation_for_operational(
    db: AsyncSession, assessment_id: UUID, operational_id: UUID
) -> EbiosRecord | None:
    result = await db.execute(
        select(EbiosRecord).where(
            EbiosRecord.assessment_id == assessment_id,
            EbiosRecord.workshop_number == 5,
            EbiosRecord.record_type == "risk_evaluation",
        )
    )
    for record in result.scalars().all():
        if str(_props(record).get("operational_scenario_id")) == str(operational_id):
            return record
    return None


async def _children(
    db: AsyncSession, assessment_id: UUID, parent_id: UUID, record_type: str, parent_key: str
) -> list[EbiosRecord]:
    result = await db.execute(
        select(EbiosRecord).where(
            EbiosRecord.assessment_id == assessment_id,
            EbiosRecord.workshop_number == 5,
            EbiosRecord.record_type == record_type,
        )
    )
    return [r for r in result.scalars().all() if str(_props(r).get(parent_key)) == str(parent_id)]


async def _delete_evaluation_bundle(
    db: AsyncSession, assessment_id: UUID, evaluation_id: UUID
) -> None:
    child_records: list[EbiosRecord] = []
    for record_type, key in (
        ("security_measure", "risk_evaluation_id"),
        ("treatment_action", "risk_evaluation_id"),
        ("residual_risk", "risk_evaluation_id"),
    ):
        child_records.extend(
            await _children(db, assessment_id, evaluation_id, record_type, key)
        )

    record_ids = {evaluation_id, *(r.id for r in child_records)}
    for record_id in record_ids:
        await db.execute(
            delete(EbiosLink).where(
                EbiosLink.assessment_id == assessment_id,
                EbiosLink.source_record_id == record_id,
            )
        )
        await db.execute(
            delete(EbiosLink).where(
                EbiosLink.assessment_id == assessment_id,
                EbiosLink.target_record_id == record_id,
            )
        )

    for child in child_records:
        await db.delete(child)


def _urbanism_asset_id(operational: EbiosRecord, assets_by_id: dict[str, EbiosRecord]) -> str | None:
    props = _props(operational)
    asset_ids = props.get("impacted_supporting_asset_ids") or []
    if not asset_ids:
        return None
    asset = assets_by_id.get(str(asset_ids[0]))
    if not asset:
        return None
    uid = (asset.properties or {}).get("urbanism_entity_id")
    return str(uid) if uid else None


def _recalculate_residual(props: dict, measures: list[EbiosRecord]) -> dict:
    retained = sum(1 for m in measures if _props(m).get("retained", True))
    return compute_residual_risk(
        int(props.get("initial_risk_score", 4)),
        retained,
        str(props.get("treatment_decision", "Réduire")),
    )


async def sync_evaluation_links(
    db: AsyncSession,
    evaluation: EbiosRecord,
    operational: EbiosRecord,
) -> None:
    props = _props(evaluation)
    await db.execute(
        delete(EbiosLink).where(
            EbiosLink.assessment_id == evaluation.assessment_id,
            EbiosLink.source_record_id == evaluation.id,
        )
    )
    db.add(
        EbiosLink(
            assessment_id=evaluation.assessment_id,
            source_record_id=evaluation.id,
            target_record_id=operational.id,
            link_type=LINK_TREATS_OPERATIONAL,
            properties={"evaluation_uid": props.get("evaluation_uid")},
        )
    )
    risk_source_id = props.get("risk_source_id")
    if risk_source_id:
        db.add(
            EbiosLink(
                assessment_id=evaluation.assessment_id,
                source_record_id=evaluation.id,
                target_record_id=UUID(str(risk_source_id)),
                link_type=LINK_EVALUATES_RISK,
                properties={},
            )
        )


async def generate_risk_treatments(
    db: AsyncSession,
    assessment_id: UUID,
    project_id: UUID,
    *,
    regenerate: bool = False,
) -> list[EbiosRecord]:
    w4 = await list_records(db, assessment_id, workshop_number=4)
    w2 = await list_records(db, assessment_id, workshop_number=2)
    validated_ops = [r for r in w4 if is_operational_validated(r)]
    assets_by_id = {str(r.id): r for r in w2 if r.record_type == "supporting_asset"}
    entities, relations = await load_urbanism_graph(db, project_id)

    if regenerate:
        existing = await list_records(db, assessment_id, workshop_number=5)
        for record in existing:
            if record.record_type == "risk_evaluation":
                await _delete_evaluation_bundle(db, assessment_id, record.id)
                await db.delete(record)
        await db.flush()

    created: list[EbiosRecord] = []
    for operational in validated_ops:
        if not regenerate:
            if await _evaluation_for_operational(db, assessment_id, operational.id):
                continue

        op_props = _props(operational)
        urbanism_asset_id = _urbanism_asset_id(operational, assets_by_id)
        roles = resolve_urbanism_roles(entities, relations, urbanism_entity_id=urbanism_asset_id)

        initial = compute_initial_risk(
            str(op_props.get("severity", "Modérée")),
            str(op_props.get("likelihood", "Modérée")),
            str(op_props.get("calculated_criticality", "Modérée")),
        )
        treatment_decision = "Réduire"
        measure_defs = generate_security_measures(op_props)
        residual = compute_residual_risk(
            initial["initial_risk_score"], len(measure_defs), treatment_decision
        )

        evaluation_uid = str(uuid.uuid4())
        eval_props = {
            "evaluation_uid": evaluation_uid,
            "operational_scenario_id": str(operational.id),
            "operational_scenario_uid": op_props.get("operational_scenario_uid"),
            "operational_scenario_label": operational.label,
            "risk_source_id": op_props.get("risk_source_id"),
            "risk_source_label": op_props.get("risk_source_label"),
            "supporting_asset": op_props.get("impacted_supporting_asset"),
            "supporting_asset_ids": op_props.get("impacted_supporting_asset_ids", []),
            "organization": roles.get("organization"),
            "owner_actor": roles.get("owner_actor"),
            "decision_maker_actor": roles.get("decision_maker_actor"),
            "validator_actor": roles.get("validator_actor"),
            "treatment_decision": treatment_decision,
            "workflow_status": WORKFLOW_AUTO,
            **initial,
            **residual,
            "grc_seed": {
                "evaluation_uid": evaluation_uid,
                "risk_register_ready": True,
                "ptr_ready": True,
                "soa_ready": True,
                "rssi_dashboard_ready": True,
                "ebios_report_ready": True,
            },
        }

        evaluation = EbiosRecord(
            assessment_id=assessment_id,
            workshop_number=5,
            record_type="risk_evaluation",
            label=f"Évaluation — {operational.label.replace('Scénario opérationnel — ', '')}",
            description=op_props.get("consequence"),
            properties=eval_props,
            status="draft",
        )
        db.add(evaluation)
        await db.flush()
        await sync_evaluation_links(db, evaluation, operational)

        owner = roles.get("owner_actor")
        for measure_def in measure_defs:
            m_props = {
                **measure_def,
                "risk_evaluation_id": str(evaluation.id),
            }
            measure = EbiosRecord(
                assessment_id=assessment_id,
                workshop_number=5,
                record_type="security_measure",
                label=measure_def["label"],
                description=measure_def.get("description"),
                properties=m_props,
                status="proposed",
            )
            db.add(measure)
            await db.flush()

            ptr = generate_ptr_action(measure_def, owner)
            action = EbiosRecord(
                assessment_id=assessment_id,
                workshop_number=5,
                record_type="treatment_action",
                label=ptr["label"],
                description=None,
                properties={
                    **ptr,
                    "risk_evaluation_id": str(evaluation.id),
                    "security_measure_id": str(measure.id),
                },
                status="planned",
            )
            db.add(action)
            await db.flush()

            db.add(
                EbiosLink(
                    assessment_id=assessment_id,
                    source_record_id=evaluation.id,
                    target_record_id=measure.id,
                    link_type=LINK_MITIGATES,
                    properties={},
                )
            )
            db.add(
                EbiosLink(
                    assessment_id=assessment_id,
                    source_record_id=action.id,
                    target_record_id=measure.id,
                    link_type=LINK_IMPLEMENTS,
                    properties={},
                )
            )

        residual_record = EbiosRecord(
            assessment_id=assessment_id,
            workshop_number=5,
            record_type="residual_risk",
            label=f"Risque résiduel — {evaluation.label}",
            description=None,
            properties={
                "risk_evaluation_id": str(evaluation.id),
                **residual,
                "grc_seed": {"risk_register_ready": True},
            },
            status="computed",
        )
        db.add(residual_record)
        created.append(evaluation)

    await db.commit()
    for record in created:
        await db.refresh(record)
    return created


async def get_workshop5_bundle(db: AsyncSession, assessment_id: UUID, project_id: UUID) -> dict:
    w4 = await list_records(db, assessment_id, workshop_number=4)
    records = await list_records(db, assessment_id, workshop_number=5)
    evaluations = [r for r in records if r.record_type == "risk_evaluation"]
    entities, relations = await load_urbanism_graph(db, project_id)
    roles = resolve_urbanism_roles(entities, relations)

    bundles = []
    for evaluation in evaluations:
        eid = str(evaluation.id)
        measures = await _children(db, assessment_id, evaluation.id, "security_measure", "risk_evaluation_id")
        actions = await _children(db, assessment_id, evaluation.id, "treatment_action", "risk_evaluation_id")
        residual_list = await _children(db, assessment_id, evaluation.id, "residual_risk", "risk_evaluation_id")
        bundles.append(
            {
                "evaluation": evaluation,
                "measures": measures,
                "actions": actions,
                "residual_risk": residual_list[0] if residual_list else None,
            }
        )

    return {
        "evaluations": bundles,
        "validated_operational_count": sum(1 for r in w4 if is_operational_validated(r)),
        "urbanism_acteurs": roles.get("available_acteurs", []),
        "treatment_decisions": list(TREATMENT_DECISIONS),
    }


async def update_risk_evaluation(
    db: AsyncSession,
    assessment_id: UUID,
    evaluation_id: UUID,
    *,
    treatment_decision: str | None = None,
    properties: dict | None = None,
    set_validated: bool = False,
) -> EbiosRecord:
    record = await db.get(EbiosRecord, evaluation_id)
    if (
        not record
        or record.assessment_id != assessment_id
        or record.record_type != "risk_evaluation"
    ):
        raise ValueError("Évaluation introuvable")

    props = dict(_props(record))
    if properties:
        props = {**props, **properties}
    if treatment_decision:
        props["treatment_decision"] = treatment_decision
    if set_validated:
        props["workflow_status"] = WORKFLOW_VALIDATED

    measures = await _children(db, assessment_id, record.id, "security_measure", "risk_evaluation_id")
    props.update(_recalculate_residual(props, measures))
    record.properties = props

    residual_children = await _children(db, assessment_id, record.id, "residual_risk", "risk_evaluation_id")
    for residual in residual_children:
        residual.properties = {
            **(_props(residual)),
            "residual_risk_score": props["residual_risk_score"],
            "residual_risk_label": props["residual_risk_label"],
        }

    await db.commit()
    await db.refresh(record)
    return record


async def update_security_measure(
    db: AsyncSession,
    assessment_id: UUID,
    measure_id: UUID,
    properties: dict,
) -> EbiosRecord:
    record = await db.get(EbiosRecord, measure_id)
    if not record or record.record_type != "security_measure":
        raise ValueError("Mesure introuvable")
    record.properties = {**_props(record), **properties}
    evaluation_id = _props(record).get("risk_evaluation_id")
    if evaluation_id:
        evaluation = await db.get(EbiosRecord, UUID(str(evaluation_id)))
        if evaluation:
            measures = await _children(db, assessment_id, evaluation.id, "security_measure", "risk_evaluation_id")
            ep = dict(_props(evaluation))
            ep.update(_recalculate_residual(ep, measures))
            evaluation.properties = ep
    await db.commit()
    await db.refresh(record)
    return record


async def update_treatment_action(
    db: AsyncSession,
    assessment_id: UUID,
    action_id: UUID,
    properties: dict,
) -> EbiosRecord:
    record = await db.get(EbiosRecord, action_id)
    if not record or record.record_type != "treatment_action":
        raise ValueError("Action PTR introuvable")
    record.properties = {**_props(record), **properties}
    await db.commit()
    await db.refresh(record)
    return record


async def delete_risk_evaluation(
    db: AsyncSession, assessment_id: UUID, evaluation_id: UUID
) -> None:
    record = await db.get(EbiosRecord, evaluation_id)
    if not record or record.record_type != "risk_evaluation":
        raise ValueError("Évaluation introuvable")
    await _delete_evaluation_bundle(db, assessment_id, evaluation_id)
    await db.delete(record)
    await db.commit()


async def recalculate_workshop5_progress(db: AsyncSession, assessment_id: UUID) -> int:
    records = await list_records(db, assessment_id, workshop_number=5)
    progress = compute_workshop5_progress(records)

    workshop5 = await get_workshop(db, assessment_id, 5)
    workshop5.progress_percent = progress
    if progress == 100:
        workshop5.status = "completed"
    elif progress > 0:
        workshop5.status = "in_progress"
    elif workshop5.status != "locked":
        workshop5.status = "available"

    await db.commit()
    return progress
