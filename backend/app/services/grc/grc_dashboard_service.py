"""Dashboard RSSI / COMEX — agrégation lecture seule depuis le registre des risques."""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ebios import EbiosRecord
from app.services.ebios.risk_calculation import score_to_label
from app.services.ebios.workshop5_service import get_workshop5_bundle
from app.services.grc.risk_register_service import build_risk_register_rows

LEVEL_LABELS = ["Faible", "Modérée", "Élevée", "Critique"]
SCORE_TO_LABEL = {i: LEVEL_LABELS[i - 1] for i in range(1, 5)}

CRITICALITY_RANK = {"Critique": 4, "Élevée": 3, "Modérée": 2, "Faible": 1}


def _props(record: EbiosRecord | None) -> dict:
    return (record.properties or {}) if record else {}


def _criticality_bucket(label: str) -> str:
    normalized = label.strip()
    if normalized in CRITICALITY_RANK:
        return normalized
    return "Modérée"


def compute_kpis(
    rows: list[dict[str, Any]],
    ptr_actions: list[dict[str, Any]],
    measures: list[dict[str, Any]],
) -> dict[str, Any]:
    total = len(rows)
    critical = sum(1 for r in rows if _criticality_bucket(r.get("criticality", "")) == "Critique")
    high = sum(1 for r in rows if _criticality_bucket(r.get("criticality", "")) == "Élevée")
    moderate = sum(1 for r in rows if _criticality_bucket(r.get("criticality", "")) == "Modérée")
    low = sum(1 for r in rows if _criticality_bucket(r.get("criticality", "")) == "Faible")
    critical_residual = sum(
        1
        for r in rows
        if r.get("residual_risk") == "Critique" or int(r.get("residual_risk_score", 0)) > 8
    )

    ptr_open = sum(1 for a in ptr_actions if a.get("category") != "completed")
    ptr_completed = sum(1 for a in ptr_actions if a.get("category") == "completed")

    validated = sum(1 for r in rows if r.get("status") == "Validé")
    treatment_rate = round(validated / total * 100, 1) if total else 0.0

    retained_measures = [m for m in measures if m.get("retained", True)]
    iso_covered = sum(
        1
        for m in retained_measures
        if str((m.get("framework_refs") or {}).get("iso27002", "")).strip()
    )
    iso_coverage = round(iso_covered / len(retained_measures) * 100, 1) if retained_measures else 0.0

    return {
        "total_risks": total,
        "critical_risks": critical,
        "high_risks": high,
        "moderate_risks": moderate,
        "low_risks": low,
        "critical_residual_risks": critical_residual,
        "ptr_open_actions": ptr_open,
        "ptr_completed_actions": ptr_completed,
        "treatment_rate_percent": treatment_rate,
        "iso27002_coverage_percent": iso_coverage,
    }


def build_heatmap(rows: list[dict[str, Any]]) -> dict[str, Any]:
    cells_map: dict[tuple[int, int], dict[str, Any]] = {}
    for row in rows:
        analytics = row.get("grc_analytics") or {}
        sev = int(analytics.get("severity_score", 2))
        lik = int(analytics.get("likelihood_score", 2))
        sev = max(1, min(4, sev))
        lik = max(1, min(4, lik))
        key = (sev, lik)
        if key not in cells_map:
            cells_map[key] = {
                "severity_score": sev,
                "likelihood_score": lik,
                "severity_label": SCORE_TO_LABEL[sev],
                "likelihood_label": SCORE_TO_LABEL[lik],
                "count": 0,
                "risk_ids": [],
                "criticalities": [],
            }
        cells_map[key]["count"] += 1
        cells_map[key]["risk_ids"].append(row.get("risk_id", ""))
        cells_map[key]["criticalities"].append(_criticality_bucket(row.get("criticality", "")))

    cells: list[dict[str, Any]] = []
    max_count = 0
    for sev in range(4, 0, -1):
        for lik in range(1, 5):
            cell = cells_map.get(
                (sev, lik),
                {
                    "severity_score": sev,
                    "likelihood_score": lik,
                    "severity_label": SCORE_TO_LABEL[sev],
                    "likelihood_label": SCORE_TO_LABEL[lik],
                    "count": 0,
                    "risk_ids": [],
                    "criticalities": [],
                },
            )
            crits = cell.pop("criticalities", [])
            cell["dominant_criticality"] = (
                max(crits, key=lambda c: CRITICALITY_RANK.get(c, 0)) if crits else ""
            )
            max_count = max(max_count, cell["count"])
            cells.append(cell)

    return {
        "severity_labels": LEVEL_LABELS,
        "likelihood_labels": LEVEL_LABELS,
        "cells": cells,
        "max_count": max_count,
    }


def compute_top_risks(rows: list[dict[str, Any]], limit: int = 5) -> list[dict[str, Any]]:
    ranked = sorted(
        rows,
        key=lambda r: (
            int(r.get("initial_risk_score", 0)),
            CRITICALITY_RANK.get(_criticality_bucket(r.get("criticality", "")), 0),
        ),
        reverse=True,
    )
    return [
        {
            "risk_id": r.get("risk_id", ""),
            "supporting_asset": r.get("supporting_asset", ""),
            "organization": r.get("organization", ""),
            "risk_source": r.get("risk_source", ""),
            "criticality": r.get("criticality", ""),
            "residual_risk": r.get("residual_risk", ""),
            "treatment_decision": r.get("treatment_decision", ""),
            "initial_risk_score": int(r.get("initial_risk_score", 0)),
        }
        for r in ranked[:limit]
    ]


def compute_exposure_by_organization(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    buckets: dict[str, dict[str, int]] = {}
    for row in rows:
        org = row.get("organization") or "Non renseignée"
        if org not in buckets:
            buckets[org] = {"count": 0, "critical_count": 0}
        buckets[org]["count"] += 1
        if _criticality_bucket(row.get("criticality", "")) == "Critique":
            buckets[org]["critical_count"] += 1
    return sorted(
        [{"label": k, **v} for k, v in buckets.items()],
        key=lambda x: x["count"],
        reverse=True,
    )


def compute_exposure_by_supporting_asset(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    buckets: dict[str, dict[str, int]] = {}
    for row in rows:
        asset = row.get("supporting_asset") or "Non renseigné"
        if asset not in buckets:
            buckets[asset] = {"count": 0, "critical_count": 0}
        buckets[asset]["count"] += 1
        if _criticality_bucket(row.get("criticality", "")) == "Critique":
            buckets[asset]["critical_count"] += 1
    return sorted(
        [{"label": k, **v} for k, v in buckets.items()],
        key=lambda x: x["count"],
        reverse=True,
    )


def _parse_due_date(value: str) -> date | None:
    if not value or not str(value).strip():
        return None
    text = str(value).strip()[:10]
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def _classify_ptr_status(status: str) -> str:
    normalized = status.lower()
    if any(x in normalized for x in ("termin", "done", "clos")):
        return "completed"
    if "cours" in normalized:
        return "in_progress"
    if "planif" in normalized:
        return "planned"
    return "open"


def compute_ptr_tracking(actions: list[dict[str, Any]]) -> dict[str, Any]:
    today = date.today()
    enriched: list[dict[str, Any]] = []
    counts = {"open": 0, "planned": 0, "in_progress": 0, "completed": 0, "overdue": 0}

    for action in actions:
        category = action.get("category") or _classify_ptr_status(action.get("status", ""))
        due = _parse_due_date(action.get("due_date", ""))
        overdue = bool(due and due < today and category != "completed")
        if overdue:
            counts["overdue"] += 1
        counts[category] = counts.get(category, 0) + 1
        enriched.append({**action, "category": category, "overdue": overdue})

    return {
        "open_count": counts.get("open", 0),
        "planned_count": counts.get("planned", 0),
        "in_progress_count": counts.get("in_progress", 0),
        "completed_count": counts.get("completed", 0),
        "overdue_count": counts["overdue"],
        "actions": enriched,
    }


def compute_comex_summary(
    rows: list[dict[str, Any]],
    ptr_actions: list[dict[str, Any]],
    *,
    project_name: str,
) -> dict[str, Any]:
    total = len(rows)
    if not total:
        return {
            "global_risk_level": "Non évalué",
            "residual_risk_level": "Non évalué",
            "decisions_to_arbitrate": 0,
            "estimated_budget_total": 0.0,
            "executive_message": (
                f"Le projet {project_name} ne compte aucun risque consolidé dans le registre. "
                "Complétez les ateliers EBIOS RM pour alimenter le tableau de bord."
            ),
        }

    initial_scores = [int(r.get("initial_risk_score", 1)) for r in rows]
    residual_scores = [int(r.get("residual_risk_score", 1)) for r in rows]
    avg_initial = sum(initial_scores) / len(initial_scores)
    avg_residual = sum(residual_scores) / len(residual_scores)

    critical_count = sum(1 for r in rows if _criticality_bucket(r.get("criticality", "")) == "Critique")
    decisions = sum(1 for r in rows if r.get("status") != "Validé")
    budget_total = sum(float(a.get("budget") or 0) for a in ptr_actions if a.get("budget") is not None)

    global_level = score_to_label(int(round(avg_initial)))
    residual_level = score_to_label(int(round(avg_residual)))

    message = (
        f"Le projet {project_name} présente {total} risque{'s' if total > 1 else ''} analysé"
        f"{'s' if total > 1 else ''}, dont {critical_count} critique{'s' if critical_count > 1 else ''}. "
        f"Le plan de traitement proposé réduit le risque résiduel global à un niveau "
        f"{residual_level.lower()}, sous réserve de mise en œuvre des mesures prioritaires."
    )

    return {
        "global_risk_level": global_level,
        "residual_risk_level": residual_level,
        "decisions_to_arbitrate": decisions,
        "estimated_budget_total": round(budget_total, 2),
        "executive_message": message,
    }


async def _load_ptr_and_measures(
    db: AsyncSession, assessment_id: UUID, project_id: UUID
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    bundle = await get_workshop5_bundle(db, assessment_id, project_id)
    actions: list[dict[str, Any]] = []
    measures: list[dict[str, Any]] = []

    for item in bundle["evaluations"]:
        evaluation = item["evaluation"]
        eval_props = _props(evaluation)
        eval_uid = str(eval_props.get("evaluation_uid", ""))

        for measure in item.get("measures") or []:
            m_props = _props(measure)
            measures.append(
                {
                    "measure_id": str(measure.id),
                    "label": measure.label,
                    "retained": m_props.get("retained", True),
                    "framework_refs": m_props.get("framework_refs") or {},
                }
            )

        for action in item.get("actions") or []:
            a_props = _props(action)
            status = str(a_props.get("status", "Planifié"))
            category = _classify_ptr_status(status)
            actions.append(
                {
                    "action_id": str(action.id),
                    "label": action.label,
                    "status": status,
                    "category": category,
                    "due_date": str(a_props.get("due_date", "")),
                    "priority": str(a_props.get("priority", "")),
                    "budget": a_props.get("budget"),
                    "evaluation_uid": eval_uid,
                }
            )

    return actions, measures


def _export_endpoints(project_id: UUID) -> dict[str, Any]:
    base = f"/api/projects/{project_id}/grc/dashboard-rssi/export"
    return {
        "dashboard_pdf": f"{base}?format=dashboard_pdf",
        "comex_summary": f"{base}?format=comex_summary",
        "rssi_report": f"{base}?format=rssi_report",
        "implemented": False,
    }


async def get_rssi_dashboard(
    db: AsyncSession,
    project_id: UUID,
    assessment_id: UUID,
    *,
    project_name: str = "",
) -> dict[str, Any]:
    rows = await build_risk_register_rows(db, assessment_id, project_id)
    ptr_actions, measures = await _load_ptr_and_measures(db, assessment_id, project_id)
    ptr_tracking = compute_ptr_tracking(ptr_actions)

    return {
        "kpis": compute_kpis(rows, ptr_actions, measures),
        "heatmap": build_heatmap(rows),
        "top_risks": compute_top_risks(rows),
        "exposure_by_organization": compute_exposure_by_organization(rows),
        "exposure_by_supporting_asset": compute_exposure_by_supporting_asset(rows),
        "ptr_tracking": ptr_tracking,
        "comex": compute_comex_summary(rows, ptr_actions, project_name=project_name or "Projet"),
        "metadata": {
            "project_id": project_id,
            "project_name": project_name or "Projet",
            "assessment_id": assessment_id,
            "generated_at": datetime.now(timezone.utc),
            "read_only": True,
            "export_endpoints": _export_endpoints(project_id),
        },
    }
