"""Déclaration d'Applicabilité (SoA) — génération depuis l'atelier 5 EBIOS RM."""

from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.ebios.workshop5_service import get_workshop5_bundle
from app.services.grc.iso27002_catalog import ISO27002_CONTROLS, SOA_VERSION_LABEL


def _normalize_iso_ref(value: str) -> str:
    return str(value).strip()


def _sort_iso_key(ref: str) -> tuple[int, int]:
    parts = ref.split(".", 1)
    try:
        return (int(parts[0]), int(parts[1]) if len(parts) > 1 else 0)
    except ValueError:
        return (999, 0)


def _is_implemented(action_status: str, eval_status: str) -> bool:
    status = f"{action_status} {eval_status}".lower()
    return any(x in status for x in ("termin", "validé", "valid", "done", "clos"))


async def _collect_measure_links(
    db: AsyncSession, assessment_id: UUID, project_id: UUID
) -> list[dict[str, Any]]:
    bundle_data = await get_workshop5_bundle(db, assessment_id, project_id)
    links: list[dict[str, Any]] = []

    for bundle in bundle_data["evaluations"]:
        evaluation = bundle["evaluation"]
        eval_props = evaluation.properties or {}
        treatment = str(eval_props.get("treatment_decision", ""))
        ebios_source = str(
            eval_props.get("operational_scenario_label") or evaluation.label
        )
        owner = str((eval_props.get("owner_actor") or {}).get("label", ""))
        eval_status = str(eval_props.get("workflow_status", ""))

        actions_by_measure: dict[str, Any] = {}
        for action in bundle.get("actions") or []:
            ap = action.properties or {}
            mid = ap.get("security_measure_id")
            if mid:
                actions_by_measure[str(mid)] = action

        for measure in bundle.get("measures") or []:
            mp = measure.properties or {}
            if not mp.get("retained", True):
                continue
            iso_raw = str((mp.get("framework_refs") or {}).get("iso27002", "")).strip()
            if not iso_raw:
                continue
            ref = _normalize_iso_ref(iso_raw)
            action = actions_by_measure.get(str(measure.id))
            ap = (action.properties or {}) if action else {}
            responsible = str(ap.get("responsible_actor_label") or owner)
            action_status = str(ap.get("status") or "Planifié")
            implemented = _is_implemented(action_status, eval_status)

            links.append(
                {
                    "iso_reference": ref,
                    "associated_measure": measure.label,
                    "measure_description": str(
                        measure.description or mp.get("description") or ""
                    ),
                    "ebios_source": ebios_source,
                    "decision": treatment,
                    "responsible": responsible,
                    "status": action_status if action else eval_status,
                    "implemented": "Oui" if implemented else "Non",
                    "comment": str(mp.get("description") or ""),
                }
            )

    return links


def build_soa_rows(links: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_ref: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for link in links:
        by_ref[link["iso_reference"]].append(link)

    all_refs = set(ISO27002_CONTROLS.keys()) | set(by_ref.keys())
    rows: list[dict[str, Any]] = []

    for ref in sorted(all_refs, key=_sort_iso_key):
        name = ISO27002_CONTROLS.get(ref, f"Control ISO/IEC 27002 — {ref}")
        items = by_ref.get(ref, [])
        applicable = "Oui" if items else "Non"

        if items:
            measures = "; ".join(dict.fromkeys(i["associated_measure"] for i in items))
            sources = "; ".join(dict.fromkeys(i["ebios_source"] for i in items))
            decisions = "; ".join(dict.fromkeys(i["decision"] for i in items if i["decision"]))
            responsibles = "; ".join(
                dict.fromkeys(i["responsible"] for i in items if i["responsible"])
            )
            statuses = "; ".join(dict.fromkeys(i["status"] for i in items if i["status"]))
            justification = next(
                (i["measure_description"] for i in items if i["measure_description"]),
                f"Mesure(s) EBIOS retenue(s) : {measures}",
            )
            implemented = "Oui" if any(i["implemented"] == "Oui" for i in items) else "Non"
            comment = "; ".join(dict.fromkeys(i["comment"] for i in items if i["comment"]))
        else:
            measures = ""
            sources = ""
            decisions = ""
            responsibles = ""
            statuses = "Non applicable"
            justification = "Non requis par l'analyse de risques EBIOS RM (atelier 5)."
            implemented = "Non"
            comment = ""

        control_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"iso27002:{ref}"))
        rows.append(
            {
                "control_id": control_id,
                "iso_reference": ref,
                "control_name": name,
                "applicable": applicable,
                "justification": justification,
                "implemented": implemented if applicable == "Oui" else "Non",
                "ebios_source": sources,
                "associated_measure": measures,
                "decision": decisions,
                "responsible": responsibles,
                "status": statuses,
                "comment": comment,
                "soa_seed": {
                    "risk_register_ready": True,
                    "audit_ready": True,
                    "certification_ready": True,
                    "dashboard_ready": True,
                },
            }
        )

    return rows


def _build_summary(rows: list[dict[str, Any]], *, project_name: str) -> dict[str, Any]:
    applicable = [r for r in rows if r["applicable"] == "Oui"]
    implemented = [r for r in applicable if r["implemented"] == "Oui"]
    total = len(rows)
    app_count = len(applicable)
    coverage = round(len(implemented) / app_count * 100, 1) if app_count else 0.0

    return {
        "soa_version": SOA_VERSION_LABEL,
        "project_name": project_name,
        "generated_at": datetime.now(timezone.utc),
        "total_controls": total,
        "applicable_controls": app_count,
        "non_applicable_controls": total - app_count,
        "implemented_controls": len(implemented),
        "coverage_rate_percent": coverage,
    }


def _unique_sorted(values: list[str]) -> list[str]:
    return sorted({v for v in values if v})


def _build_filter_options(rows: list[dict[str, Any]]) -> dict[str, list[str]]:
    return {
        "iso_references": _unique_sorted([r["iso_reference"] for r in rows]),
        "responsibles": _unique_sorted([r["responsible"] for r in rows]),
        "statuses": _unique_sorted([r["status"] for r in rows]),
    }


def apply_soa_query(
    rows: list[dict[str, Any]],
    *,
    search: str = "",
    iso_reference: str | None = None,
    applicable: str | None = None,
    implemented: str | None = None,
    responsible: str | None = None,
    status: str | None = None,
    page: int = 1,
    page_size: int = 50,
) -> tuple[list[dict[str, Any]], int]:
    needle = search.strip().lower()
    filtered = rows
    if needle:
        filtered = [
            r
            for r in filtered
            if needle
            in " ".join(
                [
                    r.get("iso_reference", ""),
                    r.get("control_name", ""),
                    r.get("associated_measure", ""),
                    r.get("ebios_source", ""),
                    r.get("justification", ""),
                    r.get("responsible", ""),
                ]
            ).lower()
        ]
    if iso_reference:
        filtered = [r for r in filtered if r["iso_reference"] == iso_reference]
    if applicable:
        filtered = [r for r in filtered if r["applicable"] == applicable]
    if implemented:
        filtered = [r for r in filtered if r["implemented"] == implemented]
    if responsible:
        filtered = [r for r in filtered if responsible in r.get("responsible", "")]
    if status:
        filtered = [r for r in filtered if status in r.get("status", "")]

    total = len(filtered)
    page = max(1, page)
    page_size = max(1, min(page_size, 200))
    start = (page - 1) * page_size
    return filtered[start : start + page_size], total


async def get_statement_of_applicability(
    db: AsyncSession,
    project_id: UUID,
    assessment_id: UUID,
    *,
    project_name: str = "",
    search: str = "",
    iso_reference: str | None = None,
    applicable: str | None = None,
    implemented: str | None = None,
    responsible: str | None = None,
    status: str | None = None,
    page: int = 1,
    page_size: int = 50,
) -> dict[str, Any]:
    links = await _collect_measure_links(db, assessment_id, project_id)
    all_rows = build_soa_rows(links)
    page_rows, total = apply_soa_query(
        all_rows,
        search=search,
        iso_reference=iso_reference,
        applicable=applicable,
        implemented=implemented,
        responsible=responsible,
        status=status,
        page=page,
        page_size=page_size,
    )

    return {
        "summary": _build_summary(all_rows, project_name=project_name or "Projet"),
        "rows": page_rows,
        "total": total,
        "page": max(1, page),
        "page_size": max(1, min(page_size, 200)),
        "filter_options": _build_filter_options(all_rows),
        "metadata": {
            "project_id": project_id,
            "assessment_id": assessment_id,
            "read_only": True,
            "standard": "ISO/IEC 27001:2022",
            "framework": "ISO/IEC 27002:2022",
        },
    }


async def get_soa_for_export(
    db: AsyncSession,
    project_id: UUID,
    assessment_id: UUID,
    project_name: str = "",
    **filters: Any,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    links = await _collect_measure_links(db, assessment_id, project_id)
    all_rows = build_soa_rows(links)
    rows, _ = apply_soa_query(all_rows, page=1, page_size=max(len(all_rows), 1), **filters)
    summary = _build_summary(all_rows, project_name=project_name or "Projet")
    return summary, rows
