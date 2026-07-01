"""Métamodèle EBIOS RM — ateliers, types d'entités et points d'extension GRC."""

from __future__ import annotations

from typing import Any

WORKSHOPS: list[dict[str, Any]] = [
    {
        "number": 1,
        "code": "framing",
        "label": "Cadrage et socle de sécurité",
        "short_label": "Cadrage",
        "description": "Définir le périmètre, les parties prenantes et le socle de sécurité.",
        "record_types": ["security_scope", "stakeholder", "security_baseline", "reference_document"],
    },
    {
        "number": 2,
        "code": "risk_sources",
        "label": "Sources de risque",
        "short_label": "Sources",
        "description": "Identifier et qualifier les sources de risque (événements redoutés, biens supports).",
        "record_types": ["feared_event", "supporting_asset", "risk_source", "vulnerability"],
    },
    {
        "number": 3,
        "code": "strategic_scenarios",
        "label": "Scénarios stratégiques",
        "short_label": "Stratégiques",
        "description": "Construire les scénarios stratégiques et estimer les impacts.",
        "record_types": ["strategic_scenario", "impact_assessment", "stakeholder_concern"],
    },
    {
        "number": 4,
        "code": "operational_scenarios",
        "label": "Scénarios opérationnels",
        "short_label": "Opérationnels",
        "description": "Décliner les scénarios opérationnels et les chemins d'attaque.",
        "record_types": ["operational_scenario", "attack_path", "operational_risk"],
    },
    {
        "number": 5,
        "code": "risk_treatment",
        "label": "Traitement des risques",
        "short_label": "Traitement",
        "description": "Évaluer les risques résiduels et définir le plan de traitement.",
        "record_types": ["risk_evaluation", "security_measure", "treatment_action", "residual_risk"],
    },
]

WORKSHOP_BY_NUMBER = {w["number"]: w for w in WORKSHOPS}
WORKSHOP_BY_CODE = {w["code"]: w for w in WORKSHOPS}

RECORD_TYPE_LABELS: dict[str, str] = {
    "security_scope": "Périmètre",
    "stakeholder": "Partie prenante",
    "security_baseline": "Socle de sécurité",
    "reference_document": "Document de référence",
    "feared_event": "Événement redouté",
    "supporting_asset": "Bien support",
    "risk_source": "Source de risque",
    "target_objective": "Objectif visé",
    "vulnerability": "Vulnérabilité",
    "strategic_scenario": "Scénario stratégique",
    "impact_assessment": "Évaluation d'impact",
    "stakeholder_concern": "Enjeu partie prenante",
    "operational_scenario": "Scénario opérationnel",
    "attack_path": "Chemin d'attaque",
    "operational_risk": "Risque opérationnel",
    "risk_evaluation": "Évaluation de risque",
    "security_measure": "Mesure de sécurité",
    "treatment_action": "Action de traitement",
    "residual_risk": "Risque résiduel",
}

# Points d'extension — plateforme GRC cible (non implémentés)
EXTENSION_MODULES: list[dict[str, Any]] = [
    {
        "id": "iso27005",
        "label": "ISO 27005",
        "status": "planned",
        "description": "Alignement du processus d'analyse de risques ISO 27005.",
    },
    {
        "id": "iso27002",
        "label": "ISO 27002",
        "status": "planned",
        "description": "Référentiel de mesures de sécurité ISO 27002.",
    },
    {
        "id": "iso27001_soa",
        "label": "ISO 27001 — SoA",
        "status": "planned",
        "description": "Déclaration d'Applicabilité et contrôles Annex A.",
    },
    {
        "id": "auto_risk_calc",
        "label": "Calcul automatique des risques",
        "status": "planned",
        "description": "Moteur de calcul probabiliste / matrice de risques.",
    },
    {
        "id": "auto_measures",
        "label": "Mesures de sécurité automatiques",
        "status": "planned",
        "description": "Recommandation IA des mesures à partir des scénarios.",
    },
    {
        "id": "ptr_generation",
        "label": "Plan de Traitement des Risques",
        "status": "planned",
        "description": "Génération automatique du PTR et suivi des actions.",
    },
    {
        "id": "rssi_dashboard",
        "label": "Tableaux de bord RSSI",
        "status": "planned",
        "description": "Indicateurs, heatmaps et reporting exécutif.",
    },
]

INTEGRATION_HOOKS: list[dict[str, Any]] = [
    {
        "id": "urbanism_sync",
        "label": "Synchronisation urbanisme SI",
        "status": "planned",
        "description": "Import des biens supports depuis la cartographie Club Urba.",
    },
    {
        "id": "knowledge_graph",
        "label": "Knowledge Graph",
        "status": "available",
        "description": "Alimentation du graphe projet (nœuds risque).",
    },
    {
        "id": "orchestration_ai",
        "label": "Orchestration IA",
        "status": "available",
        "description": "Prompt template ebios_analysis pour assistance aux ateliers.",
    },
    {
        "id": "context_builder",
        "label": "Context Builder",
        "status": "planned",
        "description": "Injection des données EBIOS dans le contexte multi-LLM.",
    },
]


def list_ebios_metamodel() -> dict[str, Any]:
    return {
        "workshops": WORKSHOPS,
        "record_type_labels": RECORD_TYPE_LABELS,
        "extension_modules": EXTENSION_MODULES,
        "integration_hooks": INTEGRATION_HOOKS,
        "version": "1.0.0-beta",
    }


def default_workshop_content(code: str) -> dict[str, Any]:
    return {"placeholder": True, "workshop_code": code, "items": []}
