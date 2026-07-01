"""Plan de Traitement des Risques (PTR) — agrégation depuis l'atelier 5 EBIOS RM."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ebios import EbiosRecord
from app.services.ebios.assessment_service import list_records
from app.services.ebios.workshop5_service import get_workshop5_bundle, update_treatment_action

PTR_STATUSES = ("Planifié", "En cours", "Bloqué", "Terminé", "En retard")
PTR_PRIORITIES = ("Critique", "Élevée", "Moyenne", "Faible")
EDITABLE_PTR_FIELDS = frozenset(
    {"status", "progress_percent", "budget", "budget_consumed", "due_date", "priority"}
)

EXPORT_HEADERS: list[tuple[str, str]] = [
    ("ptr_id", "ID PTR"),
    ("associated_risk", "Risque associé"),
    ("risk_source", "Source de risque"),
    ("strategic_scenario", "Scénario stratégique"),
    ("operational_scenario", "Scénario opérationnel"),
    ("security_measure", "Mesure de sécurité"),
    ("iso27002_reference", "Référence ISO 27002"),
    ("responsible", "Responsable"),
    ("organization", "Organisation"),
    ("priority", "Priorité"),
    ("budget", "Budget"),
    ("budget_consumed", "Budget consommé"),
    ("due_date", "Échéance"),
    ("status", "Statut"),
    ("progress_percent", "Progression (%)"),
    ("treatment_decision", "Décision EBIOS"),
    ("residual_risk", "Risque résiduel"),
    ("updated_at", "Dernière mise à jour"),
]


def _props(record: EbiosRecord | None) -> dict:
    return (record.properties or {}) if record else {}


def _ref_label(value: Any) -> str:
    if not value:
        return ""
    if isinstance(value, dict):
        return str(value.get("label", ""))
    return str(value)


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


def normalize_priority(action_props: dict[str, Any], eval_props: dict[str, Any]) -> str:
    raw = str(action_props.get("priority", "")).strip()
    if raw in PTR_PRIORITIES:
        return raw
    criticality = str(eval_props.get("criticality") or eval_props.get("initial_risk_label") or "")
    if criticality == "Critique":
        return "Critique"
    if raw.lower() in ("haute", "high", "élevée", "elevee"):
        return "Élevée"
    if raw.lower() in ("moyenne", "medium"):
        return "Moyenne"
    if raw.lower() in ("basse", "faible", "low"):
        return "Faible"
    return "Moyenne"


def derive_progress_percent(action_props: dict[str, Any], status: str) -> int:
    if action_props.get("progress_percent") is not None:
        return max(0, min(100, int(action_props["progress_percent"])))
    lowered = status.lower()
    if any(x in lowered for x in ("termin", "done", "clos")):
        return 100
    if "cours" in lowered:
        return 50
    if status == "Bloqué":
        return 25
    return 0


def effective_status(raw_status: str, *, overdue: bool) -> str:
    status = raw_status or "Planifié"
    if status == "Bloqué":
        return status
    if overdue and not any(x in status.lower() for x in ("termin", "done", "clos")):
        return "En retard"
    return status


def _is_completed(status: str) -> bool:
    return any(x in status.lower() for x in ("termin", "done", "clos"))


async def _load_operational_index(
    db: AsyncSession, assessment_id: UUID
) -> dict[str, EbiosRecord]:
    records = await list_records(db, assessment_id, workshop_number=4)
    return {str(r.id): r for r in records if r.record_type == "operational_scenario"}


async def build_ptr_rows(
    db: AsyncSession, assessment_id: UUID, project_id: UUID
) -> list[dict[str, Any]]:
    bundle_data = await get_workshop5_bundle(db, assessment_id, project_id)
    operational_by_id = await _load_operational_index(db, assessment_id)
    today = date.today()
    due_soon_limit = today + timedelta(days=7)
    rows: list[dict[str, Any]] = []

    for bundle in bundle_data["evaluations"]:
        evaluation: EbiosRecord = bundle["evaluation"]
        eval_props = _props(evaluation)
        operational = operational_by_id.get(str(eval_props.get("operational_scenario_id", "")))
        op_props = _props(operational)

        residual_record = bundle.get("residual_risk")
        residual_props = _props(residual_record)
        residual_label = str(
            eval_props.get("residual_risk_label")
            or residual_props.get("residual_risk_label")
            or ""
        )

        measures_by_id = {str(m.id): m for m in (bundle.get("measures") or [])}

        for action in bundle.get("actions") or []:
            ap = _props(action)
            measure = measures_by_id.get(str(ap.get("security_measure_id", "")))
            if measure:
                mp = _props(measure)
                if not mp.get("retained", True):
                    continue
            else:
                mp = {}

            raw_status = str(ap.get("status") or "Planifié")
            due = _parse_due_date(str(ap.get("due_date", "")))
            overdue = bool(due and due < today and not _is_completed(raw_status))
            due_soon = bool(
                due and today <= due <= due_soon_limit and not _is_completed(raw_status)
            )
            status = effective_status(raw_status, overdue=overdue)
            priority = normalize_priority(ap, eval_props)
            progress = derive_progress_percent(ap, raw_status)
            budget = ap.get("budget")
            budget_consumed = float(ap.get("budget_consumed") or 0)

            iso_ref = str((mp.get("framework_refs") or {}).get("iso27002", ""))

            rows.append(
                {
                    "ptr_id": str(ap.get("action_uid") or action.id),
                    "action_id": action.id,
                    "associated_risk": evaluation.label,
                    "risk_source": str(eval_props.get("risk_source_label") or ""),
                    "strategic_scenario": str(
                        op_props.get("strategic_scenario_label")
                        or eval_props.get("strategic_scenario_label")
                        or ""
                    ),
                    "operational_scenario": str(
                        eval_props.get("operational_scenario_label") or evaluation.label
                    ),
                    "security_measure": measure.label if measure else str(ap.get("label", "")),
                    "iso27002_reference": iso_ref,
                    "responsible": str(ap.get("responsible_actor_label") or ""),
                    "organization": _ref_label(eval_props.get("organization")),
                    "priority": priority,
                    "budget": float(budget) if budget is not None else None,
                    "budget_consumed": budget_consumed,
                    "due_date": str(ap.get("due_date") or ""),
                    "status": status,
                    "progress_percent": progress,
                    "treatment_decision": str(eval_props.get("treatment_decision") or ""),
                    "residual_risk": residual_label,
                    "updated_at": action.updated_at or datetime.now(timezone.utc),
                    "overdue": overdue,
                    "due_soon": due_soon,
                    "ptr_seed": {
                        "dashboard_ready": True,
                        "audit_ready": True,
                        "notification_ready": True,
                        "reporting_ready": True,
                        "governance_ready": True,
                    },
                }
            )

    rows.sort(key=lambda r: (r.get("due_date") or "9999", r["ptr_id"]))
    return rows


def _unique_sorted(values: list[str]) -> list[str]:
    return sorted({v for v in values if v})


def _build_filter_options(rows: list[dict[str, Any]]) -> dict[str, list[str]]:
    return {
        "responsibles": _unique_sorted([r["responsible"] for r in rows]),
        "organizations": _unique_sorted([r["organization"] for r in rows]),
        "priorities": _unique_sorted([r["priority"] for r in rows]),
        "statuses": _unique_sorted([r["status"] for r in rows]),
        "treatment_decisions": _unique_sorted([r["treatment_decision"] for r in rows]),
    }


def _matches_due_filter(row: dict[str, Any], due_filter: str | None, today: date) -> bool:
    if not due_filter:
        return True
    due = _parse_due_date(row.get("due_date", ""))
    if due_filter == "overdue":
        return bool(row.get("overdue"))
    if due_filter == "due_soon":
        return bool(row.get("due_soon"))
    if due_filter == "this_week":
        if not due:
            return False
        week_end = today + timedelta(days=7)
        return today <= due <= week_end
    if due_filter == "this_month":
        if not due:
            return False
        return due.year == today.year and due.month == today.month
    return True


def apply_ptr_query(
    rows: list[dict[str, Any]],
    *,
    search: str = "",
    responsible: str | None = None,
    organization: str | None = None,
    priority: str | None = None,
    status: str | None = None,
    treatment_decision: str | None = None,
    due_filter: str | None = None,
    page: int = 1,
    page_size: int = 50,
) -> tuple[list[dict[str, Any]], int]:
    today = date.today()
    needle = search.strip().lower()
    filtered = rows

    if needle:
        filtered = [
            r
            for r in filtered
            if needle
            in " ".join(
                [
                    r.get("ptr_id", ""),
                    r.get("associated_risk", ""),
                    r.get("security_measure", ""),
                    r.get("responsible", ""),
                    r.get("organization", ""),
                    r.get("risk_source", ""),
                    r.get("operational_scenario", ""),
                ]
            ).lower()
        ]
    if responsible:
        filtered = [r for r in filtered if r["responsible"] == responsible]
    if organization:
        filtered = [r for r in filtered if r["organization"] == organization]
    if priority:
        filtered = [r for r in filtered if r["priority"] == priority]
    if status:
        filtered = [r for r in filtered if r["status"] == status]
    if treatment_decision:
        filtered = [r for r in filtered if r["treatment_decision"] == treatment_decision]
    if due_filter:
        filtered = [r for r in filtered if _matches_due_filter(r, due_filter, today)]

    total = len(filtered)
    page = max(1, page)
    page_size = max(1, min(page_size, 200))
    start = (page - 1) * page_size
    return filtered[start : start + page_size], total


def _build_summary(rows: list[dict[str, Any]], *, project_name: str) -> dict[str, Any]:
    open_actions = sum(1 for r in rows if not _is_completed(r["status"]) and r["status"] != "Bloqué")
    in_progress = sum(1 for r in rows if r["status"] == "En cours")
    completed = sum(1 for r in rows if _is_completed(r["status"]))
    overdue = sum(1 for r in rows if r.get("overdue"))
    total_budget = sum(float(r["budget"] or 0) for r in rows)
    consumed = sum(float(r.get("budget_consumed") or 0) for r in rows)
    progress_values = [int(r.get("progress_percent") or 0) for r in rows]
    global_progress = round(sum(progress_values) / len(progress_values), 1) if progress_values else 0.0

    return {
        "project_name": project_name or "Projet",
        "generated_at": datetime.now(timezone.utc),
        "total_actions": len(rows),
        "open_actions": open_actions,
        "in_progress_actions": in_progress,
        "completed_actions": completed,
        "overdue_actions": overdue,
        "total_budget": round(total_budget, 2),
        "consumed_budget": round(consumed, 2),
        "global_progress_percent": global_progress,
    }


def build_timeline(rows: list[dict[str, Any]]) -> dict[str, Any]:
    today = date.today()

    def to_item(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "ptr_id": row["ptr_id"],
            "action_id": row["action_id"],
            "label": row["security_measure"],
            "responsible": row["responsible"],
            "due_date": row["due_date"],
            "status": row["status"],
            "priority": row["priority"],
            "progress_percent": row["progress_percent"],
            "overdue": row.get("overdue", False),
            "due_soon": row.get("due_soon", False),
        }

    overdue = [to_item(r) for r in rows if r.get("overdue")]
    due_soon = [to_item(r) for r in rows if r.get("due_soon") and not r.get("overdue")]
    items = [to_item(r) for r in rows if r.get("due_date")]

    return {
        "reference_date": today,
        "overdue": overdue,
        "due_soon": due_soon,
        "items": items,
    }


def _serialize_row(row: dict[str, Any]) -> dict[str, Any]:
    data = dict(row)
    updated = data.get("updated_at")
    if isinstance(updated, datetime):
        data["updated_at"] = updated
    return data


async def get_risk_treatment_plan(
    db: AsyncSession,
    project_id: UUID,
    assessment_id: UUID,
    *,
    project_name: str = "",
    search: str = "",
    responsible: str | None = None,
    organization: str | None = None,
    priority: str | None = None,
    status: str | None = None,
    treatment_decision: str | None = None,
    due_filter: str | None = None,
    page: int = 1,
    page_size: int = 50,
) -> dict[str, Any]:
    all_rows = await build_ptr_rows(db, assessment_id, project_id)
    page_rows, total = apply_ptr_query(
        all_rows,
        search=search,
        responsible=responsible,
        organization=organization,
        priority=priority,
        status=status,
        treatment_decision=treatment_decision,
        due_filter=due_filter,
        page=page,
        page_size=page_size,
    )

    return {
        "summary": _build_summary(all_rows, project_name=project_name or "Projet"),
        "rows": [_serialize_row(r) for r in page_rows],
        "timeline": build_timeline(all_rows),
        "total": total,
        "page": max(1, page),
        "page_size": max(1, min(page_size, 200)),
        "filter_options": _build_filter_options(all_rows),
        "metadata": {
            "project_id": project_id,
            "assessment_id": assessment_id,
            "read_only": False,
            "limited_edit": True,
            "editable_fields": sorted(EDITABLE_PTR_FIELDS),
        },
    }


async def get_ptr_for_export(
    db: AsyncSession,
    project_id: UUID,
    assessment_id: UUID,
    project_name: str = "",
    **filters: Any,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    all_rows = await build_ptr_rows(db, assessment_id, project_id)
    rows, _ = apply_ptr_query(all_rows, page=1, page_size=max(len(all_rows), 1), **filters)
    export_rows = []
    for row in rows:
        item = dict(row)
        updated = item.get("updated_at")
        if isinstance(updated, datetime):
            item["updated_at"] = updated.strftime("%Y-%m-%d %H:%M")
        export_rows.append(item)
    summary = _build_summary(all_rows, project_name=project_name or "Projet")
    return summary, export_rows


async def patch_ptr_action(
    db: AsyncSession,
    assessment_id: UUID,
    action_id: UUID,
    patch: dict[str, Any],
) -> EbiosRecord:
    properties = {k: v for k, v in patch.items() if k in EDITABLE_PTR_FIELDS and v is not None}
    if not properties:
        raise ValueError("Aucun champ modifiable fourni")
    if "status" in properties and properties["status"] not in PTR_STATUSES:
        if properties["status"] == "En retard":
            properties["status"] = "Planifié"
        elif properties["status"] not in ("Planifié", "En cours", "Bloqué", "Terminé"):
            raise ValueError("Statut PTR invalide")
    if "priority" in properties and properties["priority"] not in PTR_PRIORITIES:
        raise ValueError("Priorité PTR invalide")
    return await update_treatment_action(db, assessment_id, action_id, properties)
