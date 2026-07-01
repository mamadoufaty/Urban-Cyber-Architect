export interface DashboardKpi {
  total_risks: number;
  critical_risks: number;
  high_risks: number;
  moderate_risks: number;
  low_risks: number;
  critical_residual_risks: number;
  ptr_open_actions: number;
  ptr_completed_actions: number;
  treatment_rate_percent: number;
  iso27002_coverage_percent: number;
}

export interface HeatmapCell {
  severity_score: number;
  likelihood_score: number;
  severity_label: string;
  likelihood_label: string;
  count: number;
  risk_ids: string[];
  dominant_criticality: string;
}

export interface RiskHeatmap {
  severity_labels: string[];
  likelihood_labels: string[];
  cells: HeatmapCell[];
  max_count: number;
}

export interface TopRiskItem {
  risk_id: string;
  supporting_asset: string;
  organization: string;
  risk_source: string;
  criticality: string;
  residual_risk: string;
  treatment_decision: string;
  initial_risk_score: number;
}

export interface ExposureItem {
  label: string;
  count: number;
  critical_count: number;
}

export interface PtrActionItem {
  action_id: string;
  label: string;
  status: string;
  due_date: string;
  priority: string;
  budget: number | null;
  evaluation_uid: string;
  overdue: boolean;
  category?: string;
}

export interface PtrTracking {
  open_count: number;
  planned_count: number;
  in_progress_count: number;
  completed_count: number;
  overdue_count: number;
  actions: PtrActionItem[];
}

export interface ComexSummary {
  global_risk_level: string;
  residual_risk_level: string;
  decisions_to_arbitrate: number;
  estimated_budget_total: number;
  executive_message: string;
}

export interface RssiDashboardResponse {
  kpis: DashboardKpi;
  heatmap: RiskHeatmap;
  top_risks: TopRiskItem[];
  exposure_by_organization: ExposureItem[];
  exposure_by_supporting_asset: ExposureItem[];
  ptr_tracking: PtrTracking;
  comex: ComexSummary;
  metadata: {
    project_id: string;
    project_name: string;
    assessment_id: string;
    generated_at: string;
    read_only: boolean;
    export_endpoints: {
      dashboard_pdf: string;
      comex_summary: string;
      rssi_report: string;
      implemented: boolean;
    };
  };
}
