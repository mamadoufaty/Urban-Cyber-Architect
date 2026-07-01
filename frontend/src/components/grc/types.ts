export interface RiskRegisterRow {
  risk_id: string;
  evaluation_id: string;
  organization: string;
  supporting_asset: string;
  risk_source: string;
  strategic_scenario: string;
  operational_scenario: string;
  owner_actor: string;
  decision_maker: string;
  severity: string;
  likelihood: string;
  criticality: string;
  treatment_decision: string;
  retained_measures: string[];
  retained_measure_count: number;
  residual_risk: string;
  residual_risk_score: number;
  initial_risk_score: number;
  status: string;
  updated_at: string;
  grc_analytics: Record<string, unknown>;
}

export interface RiskRegisterFilterOptions {
  organizations: string[];
  severities: string[];
  criticalities: string[];
  treatment_decisions: string[];
  statuses: string[];
}

export interface RiskRegisterResponse {
  rows: RiskRegisterRow[];
  total: number;
  page: number;
  page_size: number;
  filter_options: RiskRegisterFilterOptions;
  metadata: {
    project_id: string;
    assessment_id: string;
    total_risks: number;
    generated_at: string;
    read_only: boolean;
    extensions_ready: Record<string, boolean>;
  };
}

export type RiskRegisterSortField =
  | "risk_id"
  | "organization"
  | "supporting_asset"
  | "risk_source"
  | "strategic_scenario"
  | "operational_scenario"
  | "owner_actor"
  | "decision_maker"
  | "severity"
  | "likelihood"
  | "criticality"
  | "treatment_decision"
  | "residual_risk_score"
  | "status"
  | "updated_at";

export interface RiskRegisterQuery {
  search?: string;
  organization?: string;
  severity?: string;
  criticality?: string;
  treatment_decision?: string;
  status?: string;
  sort_by?: RiskRegisterSortField;
  sort_dir?: "asc" | "desc";
  page?: number;
  page_size?: number;
}

export const RISK_REGISTER_COLUMNS: {
  key: RiskRegisterSortField | "retained_measures" | "residual_risk";
  label: string;
  sortable?: boolean;
}[] = [
  { key: "risk_id", label: "Identifiant", sortable: true },
  { key: "organization", label: "Organisation", sortable: true },
  { key: "supporting_asset", label: "Bien support", sortable: true },
  { key: "risk_source", label: "Source de risque", sortable: true },
  { key: "strategic_scenario", label: "Scénario stratégique", sortable: true },
  { key: "operational_scenario", label: "Scénario opérationnel", sortable: true },
  { key: "owner_actor", label: "Acteur propriétaire", sortable: true },
  { key: "decision_maker", label: "Décideur métier", sortable: true },
  { key: "severity", label: "Gravité", sortable: true },
  { key: "likelihood", label: "Probabilité", sortable: true },
  { key: "criticality", label: "Criticité", sortable: true },
  { key: "treatment_decision", label: "Décision", sortable: true },
  { key: "retained_measures", label: "Mesures retenues" },
  { key: "residual_risk", label: "Risque résiduel" },
  { key: "status", label: "Statut", sortable: true },
  { key: "updated_at", label: "Date de mise à jour", sortable: true },
];
