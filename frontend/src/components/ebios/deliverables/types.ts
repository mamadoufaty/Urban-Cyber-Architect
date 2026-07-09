export type EbiosDeliverableSection = {
  id: string;
  title: string;
  content?: string | null;
  bullets?: string[];
};

export type EbiosDeliverableColumn = {
  key: string;
  label: string;
};

export type EbiosDeliverableResponse = {
  deliverable_type: string;
  title: string;
  project_id: string;
  project_name: string;
  assessment_id: string;
  generated_at: string;
  overall_progress_percent: number;
  is_complete: boolean;
  completeness_warning: string | null;
  sections: EbiosDeliverableSection[];
  data: Record<string, unknown>;
};

export type EbiosDeliverableKind =
  | "report"
  | "risk-register"
  | "treatment-plan"
  | "executive-summary";

export const DELIVERABLE_BUTTONS: Array<{
  kind: EbiosDeliverableKind;
  label: string;
  description: string;
}> = [
  {
    kind: "report",
    label: "Générer Rapport EBIOS RM",
    description: "Rapport complet agrégé des cinq ateliers validés.",
  },
  {
    kind: "risk-register",
    label: "Générer Registre des risques",
    description: "Registre structuré des risques évalués (Atelier 5).",
  },
  {
    kind: "treatment-plan",
    label: "Générer Plan de traitement",
    description: "Actions PTR, échéances et budget estimé.",
  },
  {
    kind: "executive-summary",
    label: "Générer Synthèse COMEX",
    description: "Indicateurs clés et risques prioritaires pour le COMEX.",
  },
];
