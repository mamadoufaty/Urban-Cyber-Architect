"""Génération de scénarios opérationnels — moteur remplaçable (IA / Knowledge Graph)."""

from __future__ import annotations

import uuid
from typing import Any

WORKFLOW_AUTO = "Proposé automatiquement"
WORKFLOW_PROPOSED = "Proposé"
WORKFLOW_MODIFIED = "Modifié"
WORKFLOW_VALIDATED = "Validé"

LEVEL_SCORE = {"Faible": 1, "Modérée": 2, "Élevée": 3, "Critique": 4}


def _labels_for_ids(records: list, ids: list[str]) -> list[str]:
    id_set = {str(i) for i in ids}
    return [r.label for r in records if str(r.id) in id_set]


def calculate_criticality(severity: str, likelihood: str) -> str:
    score = LEVEL_SCORE.get(severity, 2) * LEVEL_SCORE.get(likelihood, 2)
    if score <= 4:
        return "Faible"
    if score <= 6:
        return "Modérée"
    if score <= 9:
        return "Élevée"
    return "Critique"


def _infer_threatening_actor(risk_source_label: str) -> str:
    label = risk_source_label.lower()
    if any(k in label for k in ("ransom", "cyber", "criminel", "hacker")):
        return "Cybercriminels spécialisés ransomware"
    if any(k in label for k in ("erreur", "humain", "interne")):
        return "Erreur humaine interne"
    if any(k in label for k in ("fournisseur", "prestataire", "supply")):
        return "Attaquant via chaîne d'approvisionnement"
    if any(k in label for k in ("insider", "malveillant")):
        return "Insider malveillant"
    return f"Acteur externe — {risk_source_label}"


def _build_attack_path(
    actor: str,
    entry_point: str,
    target: str,
    technical_event: str,
    consequence: str,
) -> tuple[list[str], str]:
    steps = [
        actor,
        entry_point,
        "Vol d'identifiants",
        "Connexion VPN",
        target,
        technical_event,
        consequence.split("—")[0].strip() if "—" in consequence else consequence,
    ]
    steps = [s for s in steps if s]
    return steps, " → ".join(steps)


def generate_operational_scenario(
    strategic_scenario: Any,
    risk_source: Any | None,
    stakeholder_records: list[Any],
    asset_records: list[Any],
    *,
    auto: bool = True,
) -> dict[str, Any]:
    """Construit un scénario opérationnel déterministe à partir d'un scénario stratégique validé."""
    s_props = strategic_scenario.properties or {}
    stakeholder_ids = [str(x) for x in s_props.get("stakeholder_ids", [])]
    asset_ids = [str(x) for x in s_props.get("supporting_asset_ids", [])]
    stakeholder_names = _labels_for_ids(stakeholder_records, stakeholder_ids)
    asset_names = _labels_for_ids(asset_records, asset_ids)

    risk_label = str(
        s_props.get("risk_source_label")
        or (risk_source.label if risk_source else "Source de risque")
    )
    feared = str(s_props.get("feared_event", "")).strip()
    target_objective = str(s_props.get("target_objective", "")).strip()
    severity = str(s_props.get("severity", "Modérée"))
    likelihood = str(s_props.get("likelihood", severity))
    primary_asset = asset_names[0] if asset_names else "Bien support critique"
    primary_stakeholder = stakeholder_names[0] if stakeholder_names else "SOC"

    actor = _infer_threatening_actor(risk_label)
    entry_point = "Phishing ciblé" if "cyber" in actor.lower() or "ransom" in actor.lower() else "Exploitation d'une faille exposée"
    technical_event = (
        "Déploiement ransomware"
        if "ransom" in actor.lower() or "chiffr" in feared.lower()
        else "Compromission du système cible"
    )
    consequence = (
        f"{feared} — impact sur {primary_stakeholder}"
        if feared
        else f"Indisponibilité opérationnelle — {primary_stakeholder}"
    )

    attack_steps, attack_path = _build_attack_path(
        actor, entry_point, primary_asset, technical_event, consequence
    )
    criticality = calculate_criticality(severity, likelihood)
    operational_uid = str(uuid.uuid4())
    strategic_uid = str(s_props.get("scenario_uid", ""))

    title = f"Scénario opérationnel — {strategic_scenario.label.replace('Scénario stratégique — ', '')}"

    return {
        "title": title,
        "operational_scenario_uid": operational_uid,
        "strategic_scenario_id": str(strategic_scenario.id),
        "strategic_scenario_uid": strategic_uid,
        "strategic_scenario_label": strategic_scenario.label,
        "risk_source_id": str(s_props.get("risk_source_id", "")),
        "risk_source_label": risk_label,
        "threatening_actor": actor,
        "entry_point": entry_point,
        "target": primary_asset,
        "impacted_supporting_asset": primary_asset,
        "impacted_supporting_asset_ids": asset_ids,
        "supporting_asset_labels": asset_names,
        "stakeholder_ids": stakeholder_ids,
        "stakeholder_labels": stakeholder_names,
        "attack_path": attack_path,
        "attack_steps": attack_steps,
        "technical_event": technical_event,
        "consequence": consequence,
        "likelihood": likelihood,
        "severity": severity,
        "calculated_criticality": criticality,
        "comment": "",
        "workflow_status": WORKFLOW_AUTO if auto else WORKFLOW_PROPOSED,
        "scenario_seed": {
            "operational_scenario_uid": operational_uid,
            "strategic_scenario_uid": strategic_uid,
            "treatment_ready": True,
        },
    }
