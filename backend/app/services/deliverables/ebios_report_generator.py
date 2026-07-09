"""Générateur de livrables EBIOS RM — agrégation en lecture seule des données
validées d'une étude (Ateliers 1 à 5) en structures JSON prêtes à afficher.

Ce module ne modifie jamais les ateliers, le workflow ou la progression : il
ne fait que lire les enregistrements déjà persistés (via les services
existants) pour produire quatre livrables :

- le rapport EBIOS RM complet (synthèse narrative par atelier) ;
- le registre des risques (réutilise ``risk_register_service``) ;
- le plan de traitement des risques (réutilise ``ptr_service``) ;
- la synthèse exécutive COMEX (indicateurs clés + faits marquants).

Chaque livrable indique si l'étude est complète à 100 % et porte un
avertissement explicite dans le cas contraire — la génération reste
toujours possible (aucun blocage), la responsabilité de diffusion d'un
livrable non finalisé revenant à l'utilisateur.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ebios import EbiosAssessment, EbiosRecord
from app.models.entities import Project
from app.services.ebios.assessment_service import build_overview, list_records
from app.services.ebios.workshop2_service import is_risk_source_complete
from app.services.ebios.workshop3_service import is_scenario_validated
from app.services.ebios.workshop4_service import is_operational_validated
from app.services.ebios.workshop5_service import is_evaluation_validated
from app.services.grc.ptr_service import build_ptr_rows, build_timeline
from app.services.grc.ptr_service import (
    EXPORT_HEADERS as PTR_EXPORT_HEADERS,
)
from app.services.grc.risk_register_service import (
    EXPORT_HEADERS as RISK_REGISTER_EXPORT_HEADERS,
)
from app.services.grc.risk_register_service import build_risk_register_rows

# Une étude n'est jamais bloquée pour générer un livrable, mais tout livrable
# produit à partir d'une étude incomplète (< 100 %) porte un avertissement
# explicite — la validation humaine reste le socle de la méthodologie EBIOS RM.
_EXCLUDED_STATUSES = {"proposed", "rejected"}


def _props(record: EbiosRecord | None) -> dict[str, Any]:
    return (record.properties or {}) if record else {}


def _usable(record: EbiosRecord) -> bool:
    """Un enregistrement d'atelier 1 ou 2 « compte » pour un livrable dès lors
    qu'il n'est pas une proposition IA encore en attente, ni rejeté — c'est la
    même définition que celle utilisée pour le calcul de progression."""
    return getattr(record, "status", None) not in _EXCLUDED_STATUSES


def _columns(headers: list[tuple[str, str]]) -> list[dict[str, str]]:
    return [{"key": key, "label": label} for key, label in headers]


async def _completeness(db: AsyncSession, assessment: EbiosAssessment) -> tuple[int, bool, str | None]:
    overview = await build_overview(db, assessment)
    percent = int(overview["overall_progress_percent"])
    is_complete = percent >= 100
    warning = None
    if not is_complete:
        warning = (
            f"Cette étude EBIOS RM n'est pas encore complète (progression globale : {percent} %). "
            "Ce livrable reflète uniquement les éléments validés à ce jour ; certaines sections "
            "peuvent rester incomplètes ou absentes tant que les ateliers correspondants n'ont pas "
            "été entièrement validés. Il est recommandé de finaliser la validation de tous les "
            "ateliers avant toute diffusion officielle."
        )
    return percent, is_complete, warning


def _envelope(
    *,
    deliverable_type: str,
    title: str,
    project: Project,
    assessment: EbiosAssessment,
    overall_progress_percent: int,
    is_complete: bool,
    completeness_warning: str | None,
    sections: list[dict[str, Any]],
    data: dict[str, Any],
) -> dict[str, Any]:
    return {
        "deliverable_type": deliverable_type,
        "title": title,
        "project_id": project.id,
        "project_name": project.name,
        "assessment_id": assessment.id,
        "generated_at": datetime.now(timezone.utc),
        "overall_progress_percent": overall_progress_percent,
        "is_complete": is_complete,
        "completeness_warning": completeness_warning,
        "sections": sections,
        "data": data,
    }


def _bullets(items: list[str], fallback: str) -> list[str]:
    cleaned = [str(i).strip() for i in items if i and str(i).strip()]
    return cleaned if cleaned else [fallback]


def _top(items: list[str], limit: int = 8) -> list[str]:
    if len(items) <= limit:
        return items
    return [*items[:limit], f"… et {len(items) - limit} autre(s)"]


def _is_completed_status(status: str) -> bool:
    return any(x in status.lower() for x in ("termin", "done", "clos"))


def _ptr_summary(rows: list[dict[str, Any]], *, project_name: str) -> dict[str, Any]:
    """Ré-implémentation en lecture seule du résumé PTR (mêmes règles que
    ``ptr_service._build_summary``), afin d'éviter toute dépendance à un
    symbole privé d'un autre module."""
    completed = sum(1 for r in rows if _is_completed_status(r["status"]))
    overdue = sum(1 for r in rows if r.get("overdue"))
    total_budget = sum(float(r["budget"] or 0) for r in rows)
    consumed = sum(float(r.get("budget_consumed") or 0) for r in rows)
    progress_values = [int(r.get("progress_percent") or 0) for r in rows]
    global_progress = round(sum(progress_values) / len(progress_values), 1) if progress_values else 0.0
    return {
        "project_name": project_name or "Projet",
        "total_actions": len(rows),
        "completed_actions": completed,
        "overdue_actions": overdue,
        "total_budget": round(total_budget, 2),
        "consumed_budget": round(consumed, 2),
        "global_progress_percent": global_progress,
    }


# ---------------------------------------------------------------------------
# Atelier par atelier — extraction pour le rapport complet
# ---------------------------------------------------------------------------


def _workshop1_section(records: list[EbiosRecord]) -> dict[str, Any]:
    usable = [r for r in records if _usable(r)]
    scopes = [r for r in usable if r.record_type == "security_scope"]
    stakeholders = [r for r in usable if r.record_type == "stakeholder"]
    baselines = [r for r in usable if r.record_type == "security_baseline"]
    documents = [r for r in usable if r.record_type == "reference_document"]

    scope_content = scopes[0].description or scopes[0].label if scopes else None
    bullets = [
        f"Périmètre étudié : {scopes[0].label}" if scopes else "Périmètre étudié : non validé",
        f"Parties prenantes validées : {len(stakeholders)}",
        f"Éléments du socle de sécurité : {len(baselines)}",
        f"Documents de référence : {len(documents)}",
    ]
    bullets.extend([f"— Partie prenante : {s.label}" for s in stakeholders[:5]])
    if len(stakeholders) > 5:
        bullets.append(f"— … et {len(stakeholders) - 5} autre(s) partie(s) prenante(s)")

    return {
        "id": "atelier1",
        "title": "Atelier 1 — Cadrage et socle de sécurité",
        "content": scope_content or "Périmètre en attente de validation.",
        "bullets": _bullets(bullets, "Aucune donnée validée pour cet atelier."),
    }


def _workshop2_section(records: list[EbiosRecord]) -> dict[str, Any]:
    risk_sources = [r for r in records if r.record_type == "risk_source" and is_risk_source_complete(r)]
    supporting_assets = [r for r in records if r.record_type == "supporting_asset" and _usable(r)]

    bullets = [f"Sources de risque qualifiées : {len(risk_sources)}", f"Biens supports recensés : {len(supporting_assets)}"]
    for r in risk_sources[:5]:
        props = _props(r)
        bullets.append(
            f"— {r.label} → {props.get('target_objective', '—')} "
            f"(gravité {props.get('severity', '—')})"
        )
    if len(risk_sources) > 5:
        bullets.append(f"— … et {len(risk_sources) - 5} autre(s) source(s) de risque")

    return {
        "id": "atelier2",
        "title": "Atelier 2 — Sources de risque",
        "content": (
            f"{len(risk_sources)} source(s) de risque validée(s), couvrant "
            f"{len(supporting_assets)} bien(s) support(s)."
        ),
        "bullets": _bullets(bullets, "Aucune source de risque qualifiée à ce jour."),
    }


def _workshop3_section(records: list[EbiosRecord]) -> dict[str, Any]:
    scenarios = [r for r in records if r.record_type == "strategic_scenario" and is_scenario_validated(r)]
    bullets = [f"Scénarios stratégiques validés : {len(scenarios)}"]
    for r in scenarios[:5]:
        props = _props(r)
        bullets.append(
            f"— {r.label} — motivation : {props.get('motivation', '—')}, "
            f"bien essentiel ciblé : {props.get('targeted_essential_asset', '—')}"
        )
    if len(scenarios) > 5:
        bullets.append(f"— … et {len(scenarios) - 5} autre(s) scénario(s) stratégique(s)")

    return {
        "id": "atelier3",
        "title": "Atelier 3 — Scénarios stratégiques",
        "content": f"{len(scenarios)} scénario(s) stratégique(s) validé(s).",
        "bullets": _bullets(bullets, "Aucun scénario stratégique validé à ce jour."),
    }


def _workshop4_section(records: list[EbiosRecord]) -> dict[str, Any]:
    scenarios = [r for r in records if r.record_type == "operational_scenario" and is_operational_validated(r)]
    bullets = [f"Scénarios opérationnels validés : {len(scenarios)}"]
    for r in scenarios[:5]:
        props = _props(r)
        bullets.append(
            f"— {r.label} — vraisemblance : {props.get('likelihood', '—')}"
        )
    if len(scenarios) > 5:
        bullets.append(f"— … et {len(scenarios) - 5} autre(s) scénario(s) opérationnel(s)")

    return {
        "id": "atelier4",
        "title": "Atelier 4 — Scénarios opérationnels",
        "content": f"{len(scenarios)} scénario(s) opérationnel(s) validé(s).",
        "bullets": _bullets(bullets, "Aucun scénario opérationnel validé à ce jour."),
    }


def _workshop5_section(evaluations: list[EbiosRecord]) -> dict[str, Any]:
    validated = [r for r in evaluations if is_evaluation_validated(r)]
    bullets = [f"Décisions de traitement validées : {len(validated)} / {len(evaluations)}"]
    for r in validated[:5]:
        props = _props(r)
        bullets.append(
            f"— {r.label} : {props.get('treatment_decision', '—')} — "
            f"risque initial {props.get('initial_risk_label', '—')} → "
            f"risque résiduel {props.get('residual_risk_label', '—')}"
        )
    if len(validated) > 5:
        bullets.append(f"— … et {len(validated) - 5} autre(s) décision(s) de traitement")

    return {
        "id": "atelier5",
        "title": "Atelier 5 — Traitement du risque",
        "content": f"{len(validated)} décision(s) de traitement validée(s) sur {len(evaluations)}.",
        "bullets": _bullets(bullets, "Aucune décision de traitement validée à ce jour."),
    }


# ---------------------------------------------------------------------------
# Livrable 1 — Rapport EBIOS RM complet
# ---------------------------------------------------------------------------


async def build_full_report(
    db: AsyncSession, project: Project, assessment: EbiosAssessment
) -> dict[str, Any]:
    percent, is_complete, warning = await _completeness(db, assessment)
    overview = await build_overview(db, assessment)

    w1 = await list_records(db, assessment.id, workshop_number=1)
    w2 = await list_records(db, assessment.id, workshop_number=2)
    w3 = await list_records(db, assessment.id, workshop_number=3)
    w4 = await list_records(db, assessment.id, workshop_number=4)
    w5 = await list_records(db, assessment.id, workshop_number=5)
    w5_evaluations = [r for r in w5 if r.record_type == "risk_evaluation"]

    intro_bullets = [
        f"Projet : {project.name}",
        f"Progression globale de l'étude : {percent} %",
        f"Ateliers validés : "
        + ", ".join(
            f"A{w.workshop_number} ({w.progress_percent}%)" for w in overview["workshops"]
        ),
    ]

    sections = [
        {
            "id": "synthese",
            "title": "Synthèse de l'étude",
            "content": (
                f"Ce rapport présente l'analyse de risques EBIOS RM réalisée pour le projet "
                f"« {project.name} ». Il agrège l'ensemble des éléments validés au cours des "
                f"cinq ateliers de la méthode."
            ),
            "bullets": intro_bullets,
        },
        _workshop1_section(w1),
        _workshop2_section(w2),
        _workshop3_section(w3),
        _workshop4_section(w4),
        _workshop5_section(w5_evaluations),
        {
            "id": "conclusion",
            "title": "Conclusion",
            "content": (
                "Étude finalisée à 100 % — les résultats ci-dessus peuvent être diffusés."
                if is_complete
                else "Étude en cours — certains ateliers restent à valider avant diffusion officielle."
            ),
            "bullets": _bullets(
                [
                    f"Registre des risques et plan de traitement disponibles depuis ce module « Livrables ».",
                ],
                "Poursuivre la validation des ateliers restants.",
            ),
        },
    ]

    data = {
        "workshops": [
            {
                "workshop_number": w.workshop_number,
                "code": w.code,
                "status": w.status,
                "progress_percent": w.progress_percent,
                "record_count": overview["record_counts_by_workshop"].get(str(w.workshop_number), 0),
            }
            for w in overview["workshops"]
        ],
        "record_counts_by_workshop": overview["record_counts_by_workshop"],
        "link_count": overview["link_count"],
    }

    return _envelope(
        deliverable_type="ebios_report",
        title=f"Rapport EBIOS RM complet — {project.name}",
        project=project,
        assessment=assessment,
        overall_progress_percent=percent,
        is_complete=is_complete,
        completeness_warning=warning,
        sections=sections,
        data=data,
    )


# ---------------------------------------------------------------------------
# Livrable 2 — Registre des risques
# ---------------------------------------------------------------------------


async def build_risk_register_deliverable(
    db: AsyncSession, project: Project, assessment: EbiosAssessment
) -> dict[str, Any]:
    percent, is_complete, warning = await _completeness(db, assessment)
    rows = await build_risk_register_rows(db, assessment.id, project.id)

    by_criticality: dict[str, int] = {}
    for row in rows:
        key = row.get("criticality") or "Non qualifié"
        by_criticality[key] = by_criticality.get(key, 0) + 1

    sections = [
        {
            "id": "synthese",
            "title": "Synthèse du registre des risques",
            "content": f"{len(rows)} risque(s) recensé(s) depuis les évaluations de l'Atelier 5.",
            "bullets": _bullets(
                [f"{crit} : {count}" for crit, count in sorted(by_criticality.items())],
                "Aucun risque évalué à ce jour.",
            ),
        }
    ]

    data = {
        "rows": rows,
        "columns": _columns(RISK_REGISTER_EXPORT_HEADERS),
        "total": len(rows),
        "by_criticality": by_criticality,
    }

    return _envelope(
        deliverable_type="risk_register",
        title=f"Registre des risques — {project.name}",
        project=project,
        assessment=assessment,
        overall_progress_percent=percent,
        is_complete=is_complete,
        completeness_warning=warning,
        sections=sections,
        data=data,
    )


# ---------------------------------------------------------------------------
# Livrable 3 — Plan de traitement des risques
# ---------------------------------------------------------------------------


async def build_treatment_plan_deliverable(
    db: AsyncSession, project: Project, assessment: EbiosAssessment
) -> dict[str, Any]:
    percent, is_complete, warning = await _completeness(db, assessment)
    rows = await build_ptr_rows(db, assessment.id, project.id)
    summary = _ptr_summary(rows, project_name=project.name)
    timeline = build_timeline(rows)

    sections = [
        {
            "id": "synthese",
            "title": "Synthèse du plan de traitement",
            "content": (
                f"{summary['total_actions']} action(s) de traitement, dont "
                f"{summary['completed_actions']} terminée(s) et {summary['overdue_actions']} en retard."
            ),
            "bullets": _bullets(
                [
                    f"Budget total estimé : {summary['total_budget']} €",
                    f"Budget consommé : {summary['consumed_budget']} €",
                    f"Avancement global : {summary['global_progress_percent']} %",
                ],
                "Aucune action de traitement planifiée à ce jour.",
            ),
        }
    ]

    data = {
        "rows": rows,
        "columns": _columns(PTR_EXPORT_HEADERS),
        "summary": summary,
        "timeline": {
            "overdue": timeline["overdue"],
            "due_soon": timeline["due_soon"],
        },
        "total": len(rows),
    }

    return _envelope(
        deliverable_type="treatment_plan",
        title=f"Plan de traitement des risques — {project.name}",
        project=project,
        assessment=assessment,
        overall_progress_percent=percent,
        is_complete=is_complete,
        completeness_warning=warning,
        sections=sections,
        data=data,
    )


# ---------------------------------------------------------------------------
# Livrable 4 — Synthèse exécutive COMEX
# ---------------------------------------------------------------------------


async def build_executive_summary(
    db: AsyncSession, project: Project, assessment: EbiosAssessment
) -> dict[str, Any]:
    percent, is_complete, warning = await _completeness(db, assessment)
    overview = await build_overview(db, assessment)
    risk_rows = await build_risk_register_rows(db, assessment.id, project.id)
    ptr_rows = await build_ptr_rows(db, assessment.id, project.id)
    ptr_summary = _ptr_summary(ptr_rows, project_name=project.name)

    initial_by_level: dict[str, int] = {}
    residual_by_level: dict[str, int] = {}
    for row in risk_rows:
        residual_key = row.get("residual_risk") or "Non qualifié"
        residual_by_level[residual_key] = residual_by_level.get(residual_key, 0) + 1
        initial_key = row.get("criticality") or "Non qualifié"
        initial_by_level[initial_key] = initial_by_level.get(initial_key, 0) + 1

    top_risks = sorted(risk_rows, key=lambda r: r.get("residual_risk_score", 0), reverse=True)[:5]

    kpis = {
        "overall_progress_percent": percent,
        "workshops_completed": sum(1 for w in overview["workshops"] if w.progress_percent >= 100),
        "workshops_total": len(overview["workshops"]),
        "risks_total": len(risk_rows),
        "treatment_actions_total": ptr_summary["total_actions"],
        "treatment_actions_completed": ptr_summary["completed_actions"],
        "treatment_actions_overdue": ptr_summary["overdue_actions"],
        "estimated_budget": ptr_summary["total_budget"],
        "budget_consumed": ptr_summary["consumed_budget"],
    }

    sections = [
        {
            "id": "contexte",
            "title": "Contexte",
            "content": (
                f"Synthèse à destination du COMEX de l'étude EBIOS RM menée pour le projet "
                f"« {project.name} », établie à partir des ateliers validés."
            ),
            "bullets": [f"Progression globale de l'étude : {percent} %"],
        },
        {
            "id": "resultats",
            "title": "Résultats clés",
            "content": f"{len(risk_rows)} risque(s) évalué(s) au global.",
            "bullets": _bullets(
                [f"Risque résiduel « {level} » : {count}" for level, count in sorted(residual_by_level.items())],
                "Aucun risque résiduel qualifié à ce jour.",
            ),
        },
        {
            "id": "risques_prioritaires",
            "title": "Risques prioritaires",
            "content": "Risques résiduels les plus élevés identifiés :" if top_risks else "Aucun risque à date.",
            "bullets": _bullets(
                [
                    f"{r.get('risk_source') or r.get('operational_scenario') or 'Risque'} — "
                    f"résiduel : {r.get('residual_risk', '—')} (décision : {r.get('treatment_decision', '—')})"
                    for r in top_risks
                ],
                "Aucun risque prioritaire identifié.",
            ),
        },
        {
            "id": "budget",
            "title": "Investissement et plan de traitement",
            "content": (
                f"Budget estimé : {ptr_summary['total_budget']} € — "
                f"consommé : {ptr_summary['consumed_budget']} € — "
                f"avancement : {ptr_summary['global_progress_percent']} %."
            ),
            "bullets": _bullets(
                [
                    f"Actions terminées : {ptr_summary['completed_actions']} / {ptr_summary['total_actions']}",
                    f"Actions en retard : {ptr_summary['overdue_actions']}",
                ],
                "Aucune action de traitement à ce jour.",
            ),
        },
    ]

    data = {
        "kpis": kpis,
        "initial_risk_by_level": initial_by_level,
        "residual_risk_by_level": residual_by_level,
        "top_risks": _top([r.get("risk_source") or r.get("operational_scenario") or "" for r in top_risks], 5),
    }

    return _envelope(
        deliverable_type="executive_summary",
        title=f"Synthèse exécutive COMEX — {project.name}",
        project=project,
        assessment=assessment,
        overall_progress_percent=percent,
        is_complete=is_complete,
        completeness_warning=warning,
        sections=sections,
        data=data,
    )
