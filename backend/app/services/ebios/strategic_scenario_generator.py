"""Génération de scénarios stratégiques — moteur remplaçable (IA future).

Chaque scénario est construit à partir d'une source de risque de l'Atelier 2
**validée** (cf. :func:`workshop3_service.generate_strategic_scenarios`) et
porte, en plus de sa description narrative, les champs attendus par la
méthode EBIOS RM : motivation type de la source de risque, objectif
stratégique et bien essentiel ciblé (déduits des métiers/processus validés en
Atelier 1), ainsi qu'une justification et un score de confiance IA
(indicatifs, sans effet sur la progression) et sa traçabilité
(``generated_from``)."""

from __future__ import annotations

import uuid
from typing import Any
from uuid import UUID

SOURCE_CARTOGRAPHY = "cartography"

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

# Motivation type déduite du profil de la source de risque (méthodologie
# EBIOS RM — exemples : gain financier, espionnage, sabotage, déstabilisation,
# négligence, erreur humaine). Les libellés doivent correspondre exactement à
# ceux produits par ``risk_source_generator``.
_MOTIVATION_BY_RISK_SOURCE: dict[str, str] = {
    "Cybercriminel": "Gain financier",
    "Employé malveillant": "Sabotage",
    "Prestataire": "Négligence",
    "Sous-traitant": "Négligence",
    "Concurrent": "Espionnage",
    "APT (menace persistante avancée)": "Espionnage",
    "Erreur humaine": "Erreur humaine",
    "Défaillance technique": "Négligence",
    "Catastrophe naturelle": "Aléa non intentionnel",
}
_DEFAULT_MOTIVATION = "Déstabilisation"


def _labels_for_ids(records: list, ids: list[str]) -> list[str]:
    id_set = {str(i) for i in ids}
    return [r.label for r in records if str(r.id) in id_set]


def _first_segment(text: str) -> str:
    """Premier élément d'une liste texte « a ; b » ou « a, b » — utilisé pour
    isoler un bien essentiel ciblé unique depuis l'objectif visé agrégé."""
    for sep in (" ; ", "; ", ", "):
        if sep in text:
            return text.split(sep)[0].strip()
    return text.strip()


def _confidence_score(base_confidence: int, stakeholder_count: int, asset_count: int) -> int:
    score = base_confidence
    if stakeholder_count:
        score += 5
    if asset_count:
        score += 5
    return max(20, min(96, score))


def _confidence_label(score: int) -> str:
    if score >= 80:
        return "Élevée"
    if score >= 55:
        return "Moyenne"
    return "Faible"


def _justification_bullets(
    source_label: str,
    motivation: str,
    severity: str,
    stakeholder_count: int,
    asset_count: int,
) -> list[str]:
    bullets = [f"Source de risque « {source_label} » validée en Atelier 2"]
    bullets.append(f"Motivation type déduite du profil de la source : {motivation}")
    if stakeholder_count:
        bullets.append(f"{stakeholder_count} partie(s) prenante(s) concernée(s) (Atelier 1 validé)")
    if asset_count:
        bullets.append(f"{asset_count} bien(s) support impacté(s) (Atelier 2 validé)")
    bullets.append(f"Gravité « {severity} » reportée en vraisemblance proposée — à ajuster")
    return bullets


def generate_strategic_scenario(
    risk_source: Any,
    stakeholder_records: list[Any],
    asset_records: list[Any],
    *,
    auto: bool = True,
    cartography_id: UUID | None = None,
    cartography_version_id: UUID | None = None,
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

    motivation = _MOTIVATION_BY_RISK_SOURCE.get(source_label, _DEFAULT_MOTIVATION)
    targeted_essential_asset = (
        _first_segment(target) if target else "Activités critiques du périmètre étudié"
    )

    title = f"Scénario stratégique — {source_label}"
    narrative = (
        f"Dans le contexte de l'analyse EBIOS RM, la source de risque « {source_label} » "
        f"(motivation : {motivation}) poursuit l'objectif suivant : {target}. "
        f"L'événement redouté est : {feared}. "
        f"Ce scénario stratégique décrit comment cette menace pourrait affecter {assets_text}, "
        f"avec des impacts significatifs pour {stakeholders_text}. "
        f"La gravité estimée est {severity}, nécessitant une évaluation approfondie "
        f"des mesures de sécurité existantes et des scénarios opérationnels associés."
    )

    likelihood = _SEVERITY_TO_LIKELIHOOD.get(severity, "Modérée")
    scenario_uid = str(uuid.uuid4())

    base_confidence = int(props.get("confidence_score", 60) or 60)
    confidence_score = _confidence_score(base_confidence, len(stakeholder_ids), len(asset_ids))
    justification = _justification_bullets(
        source_label, motivation, severity, len(stakeholder_ids), len(asset_ids)
    )

    return {
        "scenario_uid": scenario_uid,
        "risk_source_id": str(risk_source.id),
        "risk_source_label": source_label,
        "motivation": motivation,
        "target_objective": target,
        "strategic_objective": target,
        "targeted_essential_asset": targeted_essential_asset,
        "feared_event": feared,
        "narrative_description": narrative,
        "stakeholder_ids": stakeholder_ids,
        "supporting_asset_ids": asset_ids,
        "stakeholder_labels": stakeholder_names,
        "supporting_asset_labels": asset_names,
        "severity": severity,
        "likelihood": likelihood,
        "comment": "",
        "justification": justification,
        "confidence_score": confidence_score,
        "confidence_label": _confidence_label(confidence_score),
        "workflow_status": WORKFLOW_AUTO if auto else WORKFLOW_PROPOSED,
        "generated_from": {
            "source": SOURCE_CARTOGRAPHY,
            "cartography_id": str(cartography_id) if cartography_id else None,
            "cartography_version_id": str(cartography_version_id) if cartography_version_id else None,
            "risk_source_id": str(risk_source.id),
        },
        "scenario_seed": {
            "strategic_scenario_uid": scenario_uid,
            "operational_ready": True,
            "risk_source_id": str(risk_source.id),
        },
        "title": title,
    }
