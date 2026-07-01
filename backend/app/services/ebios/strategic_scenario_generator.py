"""Génération de scénarios stratégiques — moteur remplaçable (IA future)."""

from __future__ import annotations

import uuid
from typing import Any

LIKELIHOOD_LEVELS = ("Faible", "Modérée", "Élevée", "Critique")
WORKFLOW_AUTO = "Proposé automatiquement"
WORKFLOW_PROPOSED = "Proposé"
WORKFLOW_MODIFIED = "Modifié"
WORKFLOW_VALIDATED = "Validé"

_SEVERITY_TO_LIKELIHOOD = {
    "Faible": "Faible",
    "Modérée": "Modérée",
    "Élevée": "Élevée",
    "Critique": "Critique",
}


def _labels_for_ids(records: list, ids: list[str]) -> list[str]:
    id_set = {str(i) for i in ids}
    return [r.label for r in records if str(r.id) in id_set]


def generate_strategic_scenario(
    risk_source: Any,
    stakeholder_records: list[Any],
    asset_records: list[Any],
    *,
    auto: bool = True,
) -> dict[str, Any]:
    """Construit un scénario stratégique cohérent à partir d'une source de risque complète."""
    props = risk_source.properties or {}
    stakeholder_ids = [str(x) for x in props.get("stakeholder_ids", [])]
    asset_ids = [str(x) for x in props.get("supporting_asset_ids", [])]
    severity = str(props.get("severity", "Modérée"))
    target = str(props.get("target_objective", "")).strip()
    feared = str(props.get("feared_event", "")).strip()
    source_label = risk_source.label.strip()

    stakeholder_names = _labels_for_ids(stakeholder_records, stakeholder_ids)
    asset_names = _labels_for_ids(asset_records, asset_ids)
    stakeholders_text = ", ".join(stakeholder_names) if stakeholder_names else "les parties prenantes identifiées"
    assets_text = ", ".join(asset_names) if asset_names else "les biens supports concernés"

    title = f"Scénario stratégique — {source_label}"
    narrative = (
        f"Dans le contexte de l'analyse EBIOS RM, la source de risque « {source_label} » "
        f"poursuit l'objectif suivant : {target}. "
        f"L'événement redouté est : {feared}. "
        f"Ce scénario stratégique décrit comment cette menace pourrait affecter {assets_text}, "
        f"avec des impacts significatifs pour {stakeholders_text}. "
        f"La gravité estimée est {severity}, nécessitant une évaluation approfondie "
        f"des mesures de sécurité existantes et des scénarios opérationnels associés."
    )

    likelihood = _SEVERITY_TO_LIKELIHOOD.get(severity, "Modérée")
    scenario_uid = str(uuid.uuid4())

    return {
        "scenario_uid": scenario_uid,
        "risk_source_id": str(risk_source.id),
        "risk_source_label": source_label,
        "target_objective": target,
        "feared_event": feared,
        "narrative_description": narrative,
        "stakeholder_ids": stakeholder_ids,
        "supporting_asset_ids": asset_ids,
        "stakeholder_labels": stakeholder_names,
        "supporting_asset_labels": asset_names,
        "severity": severity,
        "likelihood": likelihood,
        "comment": "",
        "workflow_status": WORKFLOW_AUTO if auto else WORKFLOW_PROPOSED,
        "scenario_seed": {
            "strategic_scenario_uid": scenario_uid,
            "operational_ready": True,
            "risk_source_id": str(risk_source.id),
        },
        "title": title,
    }
