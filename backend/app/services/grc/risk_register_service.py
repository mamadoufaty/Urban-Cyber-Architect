"""Registre des risques — agrégation lecture seule depuis les ateliers EBIOS."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ebios import EbiosRecord
from app.services.ebios.assessment_service import list_records
from app.services.ebios.risk_calculation import LEVEL_SCORE
from app.services.ebios.workshop5_service import get_workshop5_bundle

SORTABLE_FIELDS = frozenset(
    {
        "risk_id",
        "organization",
        "supporting_asset",
        "risk_source",
        "strategic_scenario",
        "operational_scenario",
        "owner_actor",
        "decision_maker",
        "severity",
        "likelihood",
        "criticality",
        "treatment_decision",
        "residual_risk_score",
        "status",
        "updated_at",
    }
)

EXPORT_HEADERS = [
    ("risk_id", "Identifiant"),
    ("organization", "Organisation"),
    ("supporting_asset", "Bien support"),
    ("risk_source", "Source de risque"),
    ("strategic_scenario", "Scénario stratégique"),
    ("operational_scenario", "Scénario opérationnel"),
    ("owner_actor", "Acteur propriétaire"),
    ("decision_maker", "Décideur métier"),
    ("severity", "Gravité"),
    ("likelihood", "Probabilité"),
    ("criticality", "Criticité"),
    ("treatment_decision", "Décision"),
    ("retained_measures_text", "Mesures retenues"),
    ("residual_risk", "Risque résiduel"),
    ("status", "Statut"),
    ("updated_at", "Date de mise à jour"),
]


def _props(record: EbiosRecord | None) -> dict:
    return (record.properties or {}) if record else {}


def _ref_label(value: Any) -> str:
    if not value:
        return ""
    if isinstance(value, dict):
        return str(value.get("label", ""))
    return str(value)


def _normalize_status(workflow_status: str) -> str:
    if workflow_status == "Validé":
        return "Validé"
    if workflow_status in ("Proposé automatiquement", "En cours"):
        return "En cours"
    if workflow_status == "Modifié":
        return "Modifié"
    return workflow_status or "En cours"


def _row_to_export_dict(row: dict[str, Any]) -> dict[str, Any]:
    data = dict(row)
    data["retained_measures_text"] = "; ".join(row.get("retained_measures", []))
    if isinstance(data.get("updated_at"), datetime):
        data["updated_at"] = data["updated_at"].strftime("%Y-%m-%d %H:%M")
    return data


async def _load_operational_index(
    db: AsyncSession, assessment_id: UUID
) -> dict[str, EbiosRecord]:
    records = await list_records(db, assessment_id, workshop_number=4)
    return {
        str(r.id): r
        for r in records
        if r.record_type == "operational_scenario"
    }


async def build_risk_register_rows(
    db: AsyncSession, assessment_id: UUID, project_id: UUID
) -> list[dict[str, Any]]:
    """Construit les lignes du registre à partir des évaluations atelier 5."""
    bundle_data = await get_workshop5_bundle(db, assessment_id, project_id)
    operational_by_id = await _load_operational_index(db, assessment_id)
    rows: list[dict[str, Any]] = []

    for bundle in bundle_data["evaluations"]:
        evaluation: EbiosRecord = bundle["evaluation"]
        props = _props(evaluation)
        grc_seed = props.get("grc_seed") or {}
        if grc_seed.get("risk_register_ready") is False:
            continue

        operational = operational_by_id.get(str(props.get("operational_scenario_id", "")))
        op_props = _props(operational)

        measures = bundle.get("measures") or []
        retained = [
            m.label
            for m in measures
            if (_props(m).get("retained", True))
        ]

        severity = str(props.get("severity", ""))
        likelihood = str(props.get("likelihood", ""))
        residual_score = int(props.get("residual_risk_score", 1))
        initial_score = int(props.get("initial_risk_score", 1))

        row = {
            "risk_id": str(props.get("evaluation_uid") or evaluation.id),
            "evaluation_id": evaluation.id,
            "organization": _ref_label(props.get("organization")),
            "supporting_asset": str(props.get("supporting_asset") or ""),
            "risk_source": str(props.get("risk_source_label") or ""),
            "strategic_scenario": str(
                op_props.get("strategic_scenario_label")
                or props.get("strategic_scenario_label")
                or ""
            ),
            "operational_scenario": str(
                props.get("operational_scenario_label") or evaluation.label
            ),
            "owner_actor": _ref_label(props.get("owner_actor")),
            "decision_maker": _ref_label(props.get("decision_maker_actor")),
            "severity": severity,
            "likelihood": likelihood,
            "criticality": str(props.get("criticality") or props.get("initial_risk_label") or ""),
            "treatment_decision": str(props.get("treatment_decision") or ""),
            "retained_measures": retained,
            "retained_measure_count": len(retained),
            "residual_risk": str(props.get("residual_risk_label") or ""),
            "residual_risk_score": residual_score,
            "initial_risk_score": initial_score,
            "status": _normalize_status(str(props.get("workflow_status", ""))),
            "updated_at": evaluation.updated_at,
            "grc_analytics": {
                "heatmap_ready": True,
                "kpi_ready": True,
                "kri_ready": True,
                "rssi_dashboard_ready": grc_seed.get("rssi_dashboard_ready", True),
                "comex_board_ready": True,
                "severity_score": LEVEL_SCORE.get(severity, 2),
                "likelihood_score": LEVEL_SCORE.get(likelihood, 2),
                "initial_risk_score": initial_score,
                "residual_risk_score": residual_score,
                "evaluation_uid": props.get("evaluation_uid"),
            },
        }
        rows.append(row)

    rows.sort(key=lambda r: r["updated_at"], reverse=True)
    return rows


def _unique_sorted(values: list[str]) -> list[str]:
    return sorted({v for v in values if v})


def _build_filter_options(rows: list[dict[str, Any]]) -> dict[str, list[str]]:
    return {
        "organizations": _unique_sorted([r["organization"] for r in rows]),
        "severities": _unique_sorted([r["severity"] for r in rows]),
        "criticalities": _unique_sorted([r["criticality"] for r in rows]),
        "treatment_decisions": _unique_sorted([r["treatment_decision"] for r in rows]),
        "statuses": _unique_sorted([r["status"] for r in rows]),
    }


def _matches_search(row: dict[str, Any], search: str) -> bool:
    needle = search.strip().lower()
    if not needle:
        return True
    haystack = " ".join(
        [
            row.get("risk_id", ""),
            row.get("organization", ""),
            row.get("supporting_asset", ""),
            row.get("risk_source", ""),
            row.get("strategic_scenario", ""),
            row.get("operational_scenario", ""),
            row.get("owner_actor", ""),
            row.get("decision_maker", ""),
            row.get("treatment_decision", ""),
            row.get("status", ""),
            " ".join(row.get("retained_measures", [])),
        ]
    ).lower()
    return needle in haystack


def apply_risk_register_query(
    rows: list[dict[str, Any]],
    *,
    search: str = "",
    organization: str | None = None,
    severity: str | None = None,
    criticality: str | None = None,
    treatment_decision: str | None = None,
    status: str | None = None,
    sort_by: str = "updated_at",
    sort_dir: str = "desc",
    page: int = 1,
    page_size: int = 25,
) -> tuple[list[dict[str, Any]], int]:
    filtered = [r for r in rows if _matches_search(r, search)]
    if organization:
        filtered = [r for r in filtered if r["organization"] == organization]
    if severity:
        filtered = [r for r in filtered if r["severity"] == severity]
    if criticality:
        filtered = [r for r in filtered if r["criticality"] == criticality]
    if treatment_decision:
        filtered = [r for r in filtered if r["treatment_decision"] == treatment_decision]
    if status:
        filtered = [r for r in filtered if r["status"] == status]

    field = sort_by if sort_by in SORTABLE_FIELDS else "updated_at"
    reverse = sort_dir.lower() != "asc"
    filtered.sort(key=lambda r: r.get(field) or "", reverse=reverse)

    total = len(filtered)
    page = max(1, page)
    page_size = max(1, min(page_size, 200))
    start = (page - 1) * page_size
    return filtered[start : start + page_size], total


async def get_risk_register(
    db: AsyncSession,
    project_id: UUID,
    assessment_id: UUID,
    *,
    search: str = "",
    organization: str | None = None,
    severity: str | None = None,
    criticality: str | None = None,
    treatment_decision: str | None = None,
    status: str | None = None,
    sort_by: str = "updated_at",
    sort_dir: str = "desc",
    page: int = 1,
    page_size: int = 25,
) -> dict[str, Any]:
    all_rows = await build_risk_register_rows(db, assessment_id, project_id)
    page_rows, total = apply_risk_register_query(
        all_rows,
        search=search,
        organization=organization,
        severity=severity,
        criticality=criticality,
        treatment_decision=treatment_decision,
        status=status,
        sort_by=sort_by,
        sort_dir=sort_dir,
        page=page,
        page_size=page_size,
    )
    return {
        "rows": page_rows,
        "total": total,
        "page": max(1, page),
        "page_size": max(1, min(page_size, 200)),
        "filter_options": _build_filter_options(all_rows),
        "metadata": {
            "project_id": project_id,
            "assessment_id": assessment_id,
            "total_risks": len(all_rows),
            "generated_at": datetime.now(timezone.utc),
            "read_only": True,
            "extensions_ready": {
                "rssi_dashboard": True,
                "heatmap": True,
                "kpi": True,
                "kri": True,
                "comex_board": True,
            },
        },
    }


async def get_risk_register_for_export(
    db: AsyncSession,
    project_id: UUID,
    assessment_id: UUID,
    **filters: Any,
) -> list[dict[str, Any]]:
    all_rows = await build_risk_register_rows(db, assessment_id, project_id)
    rows, _ = apply_risk_register_query(
        all_rows,
        page=1,
        page_size=max(len(all_rows), 1),
        **filters,
    )
    return [_row_to_export_dict(r) for r in rows]
