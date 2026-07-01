import type { EbiosWorkshopSpec } from "./types";

/** Fallback local si l'API métamodèle est indisponible. */
export const EBIOS_WORKSHOPS_FALLBACK: EbiosWorkshopSpec[] = [
  {
    number: 1,
    code: "framing",
    label: "Cadrage et socle de sécurité",
    short_label: "Cadrage",
    description: "Périmètre, parties prenantes et socle de sécurité.",
    record_types: ["security_scope", "stakeholder", "security_baseline", "reference_document"],
  },
  {
    number: 2,
    code: "risk_sources",
    label: "Sources de risque",
    short_label: "Sources",
    description: "Événements redoutés, biens supports et sources de risque.",
    record_types: ["feared_event", "supporting_asset", "risk_source", "vulnerability"],
  },
  {
    number: 3,
    code: "strategic_scenarios",
    label: "Scénarios stratégiques",
    short_label: "Stratégiques",
    description: "Scénarios stratégiques et impacts.",
    record_types: ["strategic_scenario", "impact_assessment", "stakeholder_concern"],
  },
  {
    number: 4,
    code: "operational_scenarios",
    label: "Scénarios opérationnels",
    short_label: "Opérationnels",
    description: "Scénarios opérationnels et chemins d'attaque.",
    record_types: ["operational_scenario", "attack_path", "operational_risk"],
  },
  {
    number: 5,
    code: "risk_treatment",
    label: "Traitement des risques",
    short_label: "Traitement",
    description: "Évaluation, mesures et plan de traitement.",
    record_types: ["risk_evaluation", "security_measure", "treatment_action", "residual_risk"],
  },
];

export const WORKSHOP_STATUS_LABELS: Record<string, string> = {
  locked: "Verrouillé",
  available: "Disponible",
  in_progress: "En cours",
  completed: "Terminé",
};
