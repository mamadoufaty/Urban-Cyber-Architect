export type SoaSeed = {
  risk_register_ready: boolean;
  audit_ready: boolean;
  certification_ready: boolean;
  dashboard_ready: boolean;
};

export type SoaControlRow = {
  control_id: string;
  iso_reference: string;
  control_name: string;
  applicable: string;
  justification: string;
  implemented: string;
  ebios_source: string;
  associated_measure: string;
  decision: string;
  responsible: string;
  status: string;
  comment: string;
  soa_seed: SoaSeed;
};

export type SoaSummary = {
  soa_version: string;
  project_name: string;
  generated_at: string;
  total_controls: number;
  applicable_controls: number;
  non_applicable_controls: number;
  implemented_controls: number;
  coverage_rate_percent: number;
};

export type SoaFilterOptions = {
  iso_references: string[];
  responsibles: string[];
  statuses: string[];
};

export type SoaMetadata = {
  project_id: string;
  assessment_id: string;
  read_only: boolean;
  standard: string;
  framework: string;
};

export type SoaResponse = {
  summary: SoaSummary;
  rows: SoaControlRow[];
  total: number;
  page: number;
  page_size: number;
  filter_options: SoaFilterOptions;
  metadata: SoaMetadata;
};

export type SoaQuery = {
  search?: string;
  iso_reference?: string;
  applicable?: string;
  implemented?: string;
  responsible?: string;
  status?: string;
  page?: number;
  page_size?: number;
};

export type SoaKpiKey = "total" | "applicable" | "non_applicable" | "implemented" | "coverage";
