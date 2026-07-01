"""Générateur documentaire — moteur déterministe basé sur templates."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.deliverables import Deliverable
from app.models.entities import OrchestrationRun, Project
from app.schemas.deliverables import DELIVERABLE_TYPES
from app.services.deliverables.serialize_json import serialize_json
from app.services.deliverables.templates import build_document_content
from app.services.ebios.assessment_service import get_or_create_assessment, list_records
from app.services.ebios.urbanism_actor_resolver import load_urbanism_graph
from app.services.grc.grc_dashboard_service import get_rssi_dashboard
from app.services.grc.ptr_service import get_risk_treatment_plan
from app.services.grc.risk_register_service import build_risk_register_rows
from app.services.grc.soa_service import get_statement_of_applicability
from app.connectors.wazuh.service import get_wazuh_status


def _type_label(deliverable_type: str) -> str:
    for key, label in DELIVERABLE_TYPES:
        if key == deliverable_type:
            return label
    return deliverable_type


def _entity_labels(entities, entity_type: str) -> list[str]:
    return [e.label for e in entities if e.entity_type == entity_type]


def _entity_details(entities, entity_type: str) -> list[dict[str, Any]]:
    rows = []
    for e in entities:
        if e.entity_type != entity_type:
            continue
        props = e.properties or {}
        rows.append(
            {
                "label": e.label,
                "couche": e.couche,
                "description": e.description or "",
                "properties": props,
            }
        )
    return rows


async def collect_project_context(
    db: AsyncSession,
    project_id: UUID,
    data_sources: list[str],
) -> dict[str, Any]:
    project = await db.get(Project, project_id)
    if not project:
        raise ValueError("Projet introuvable")

    sources = {s.lower().strip() for s in data_sources if s}
    ctx: dict[str, Any] = {
        "project": {
            "id": str(project.id),
            "name": project.name,
            "description": project.description or "",
            "organization": project.organization or {},
            "referentials": project.referentials or [],
            "objectives": project.objectives or [],
            "urbanism_meta": project.urbanism or {},
        },
        "data_sources_used": sorted(sources),
    }

    if "urbanism" in sources:
        entities, relations = await load_urbanism_graph(db, project_id)
        ctx["urbanism"] = {
            "entities_count": len(entities),
            "relations_count": len(relations),
            "organisations": _entity_labels(entities, "organisation"),
            "acteurs": _entity_labels(entities, "acteur"),
            "processus": _entity_labels(entities, "processus"),
            "applications": _entity_labels(entities, "application"),
            "biens_supports": _entity_labels(entities, "serveur") + _entity_labels(entities, "bien_support"),
            "acteurs_detail": _entity_details(entities, "acteur"),
            "organisations_detail": _entity_details(entities, "organisation"),
            "processus_detail": _entity_details(entities, "processus"),
            "applications_detail": _entity_details(entities, "application"),
        }

    assessment = None
    if any(s in sources for s in ("ebios", "grc")):
        assessment = await get_or_create_assessment(db, project_id)

    if "ebios" in sources and assessment:
        w1 = await list_records(db, assessment.id, workshop_number=1)
        w2 = await list_records(db, assessment.id, workshop_number=2)
        ctx["ebios"] = {
            "assessment_id": str(assessment.id),
            "status": assessment.status,
            "workshop1_records": len(w1),
            "workshop2_records": len(w2),
            "stakeholders": [r.label for r in w1 if r.record_type == "stakeholder"],
            "supporting_assets": [r.label for r in w2 if r.record_type == "supporting_asset"],
        }

    if "grc" in sources and assessment:
        risk_rows = await build_risk_register_rows(db, assessment.id, project_id)
        ctx["grc"] = {
            "risk_register_total": len(risk_rows),
            "risk_register_sample": risk_rows[:8],
            "top_risks": [
                {
                    "id": r.get("risk_id"),
                    "asset": r.get("supporting_asset"),
                    "criticality": r.get("criticality"),
                    "decision": r.get("treatment_decision"),
                }
                for r in sorted(
                    risk_rows,
                    key=lambda x: float(x.get("residual_risk_score") or 0),
                    reverse=True,
                )[:5]
            ],
        }
        try:
            dashboard = await get_rssi_dashboard(
                db, project_id, assessment.id, project_name=project.name
            )
            ctx["grc"]["rssi_dashboard"] = dashboard.get("summary") or {}
        except Exception:
            ctx["grc"]["rssi_dashboard"] = {}
        try:
            soa = await get_statement_of_applicability(
                db, project_id, assessment.id, project_name=project.name
            )
            ctx["grc"]["soa_total"] = soa.get("total") or len(soa.get("rows") or [])
        except Exception:
            ctx["grc"]["soa_total"] = 0
        try:
            ptr = await get_risk_treatment_plan(
                db, project_id, assessment.id, project_name=project.name
            )
            ctx["grc"]["ptr_total"] = ptr.get("total") or len(ptr.get("rows") or [])
            ctx["grc"]["ptr_progress"] = (ptr.get("summary") or {}).get("global_progress_percent")
        except Exception:
            ctx["grc"]["ptr_total"] = 0

    if "soc" in sources:
        try:
            from app.services.soc.correlation_service import get_soc_correlations

            soc = await get_soc_correlations(db, project_id, limit=5, project_name=project.name)
            ctx["soc"] = {
                "incidents_count": soc.get("summary", {}).get("incidents_count", 0),
                "correlated_risks": soc.get("summary", {}).get("correlated_risks", 0),
                "assets_matched": soc.get("summary", {}).get("assets_matched", 0),
                "wazuh_error": soc.get("metadata", {}).get("wazuh_error"),
            }
        except Exception as exc:
            ctx["soc"] = {"error": str(exc)}

    if "wazuh" in sources:
        try:
            status = await get_wazuh_status(db)
            ctx["wazuh"] = {
                "connected": status.get("connected"),
                "agents_total": status.get("agents_total"),
                "agents_active": status.get("agents_active"),
                "wazuh_version": status.get("wazuh_version"),
                "error": status.get("error"),
            }
        except Exception as exc:
            ctx["wazuh"] = {"error": str(exc)}

    if "ai" in sources:
        result = await db.execute(
            select(OrchestrationRun)
            .where(OrchestrationRun.project_id == project_id)
            .order_by(OrchestrationRun.created_at.desc())
            .limit(5)
        )
        runs = result.scalars().all()
        ctx["ai"] = {
            "runs_count": len(runs),
            "recent": [
                {
                    "id": str(r.id),
                    "template_name": r.template_name,
                    "status": r.status,
                    "prompt_excerpt": (r.prompt or "")[:200],
                    "created_at": r.created_at.isoformat() if r.created_at else "",
                }
                for r in runs
            ],
        }

    return ctx


def _to_summary(record: Deliverable) -> dict[str, Any]:
    return {
        "id": record.id,
        "project_id": record.project_id,
        "title": record.title,
        "deliverable_type": record.deliverable_type,
        "user_need": record.user_need,
        "data_sources": record.data_sources or [],
        "export_format": record.export_format,
        "status": record.status,
        "created_at": record.created_at,
        "updated_at": record.updated_at,
    }


def _to_detail(record: Deliverable) -> dict[str, Any]:
    payload = _to_summary(record)
    payload["generated_content"] = record.generated_content or {}
    return payload


async def list_project_deliverables(db: AsyncSession, project_id: UUID) -> dict[str, Any]:
    project = await db.get(Project, project_id)
    if not project:
        raise ValueError("Projet introuvable")
    result = await db.execute(
        select(Deliverable)
        .where(Deliverable.project_id == project_id)
        .order_by(Deliverable.created_at.desc())
    )
    rows = result.scalars().all()
    return {
        "deliverables": [_to_summary(r) for r in rows],
        "total": len(rows),
        "types": [{"id": k, "label": v} for k, v in DELIVERABLE_TYPES],
        "data_sources": ["urbanism", "ebios", "grc", "soc", "wazuh", "ai"],
        "export_formats": ["pdf", "docx", "markdown"],
    }


async def get_project_deliverable(
    db: AsyncSession, project_id: UUID, deliverable_id: UUID
) -> dict[str, Any]:
    record = await db.get(Deliverable, deliverable_id)
    if not record or record.project_id != project_id:
        raise ValueError("Livrable introuvable")
    return _to_detail(record)


async def generate_deliverable(
    db: AsyncSession,
    project_id: UUID,
    *,
    title: str,
    deliverable_type: str,
    user_need: str,
    data_sources: list[str],
    export_format: str = "markdown",
    preview: bool = False,
) -> dict[str, Any]:
    project = await db.get(Project, project_id)
    if not project:
        raise ValueError("Projet introuvable")

    context = await collect_project_context(db, project_id, data_sources)
    generated_content = serialize_json(
        build_document_content(
            deliverable_type=deliverable_type,
            title=title,
            user_need=user_need,
            context=context,
            type_label=_type_label(deliverable_type),
        )
    )
    serialized_sources = serialize_json(data_sources)

    if preview:
        return {
            "preview": True,
            "deliverable": None,
            "generated_content": generated_content,
        }

    now = datetime.now(timezone.utc)
    record = Deliverable(
        project_id=project_id,
        title=title.strip(),
        deliverable_type=deliverable_type,
        user_need=user_need,
        data_sources=serialized_sources,
        export_format=export_format,
        generated_content=generated_content,
        status="generated",
        created_at=now,
        updated_at=now,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)

    return {
        "preview": False,
        "deliverable": _to_detail(record),
        "generated_content": generated_content,
    }
