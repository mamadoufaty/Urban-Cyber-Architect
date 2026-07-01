export type PtrSeed = {
  dashboard_ready: boolean;
  audit_ready: boolean;
  notification_ready: boolean;
  reporting_ready: boolean;
  governance_ready: boolean;
};

export type PtrActionRow = {
  ptr_id: string;
  action_id: string;
  associated_risk: string;
  risk_source: string;
  strategic_scenario: string;
  operational_scenario: string;
  security_measure: string;
  iso27002_reference: string;
  responsible: string;
  organization: string;
  priority: string;
  budget: number | null;
  budget_consumed: number;
  due_date: string;
  status: string;
  progress_percent: number;
  treatment_decision: string;
  residual_risk: string;
  updated_at: string;
  overdue: boolean;
  due_soon: boolean;
  ptr_seed: PtrSeed;
};

export type PtrSummary = {
  project_name: string;
  generated_at: string;
  total_actions: number;
  open_actions: number;
  in_progress_actions: number;
  completed_actions: number;
  overdue_actions: number;
  total_budget: number;
  consumed_budget: number;
  global_progress_percent: number;
};

export type PtrTimelineItem = {
  ptr_id: string;
  action_id: string;
  label: string;
  responsible: string;
  due_date: string;
  status: string;
  priority: string;
  progress_percent: number;
  overdue: boolean;
  due_soon: boolean;
};

export type PtrTimeline = {
  reference_date: string;
  overdue: PtrTimelineItem[];
  due_soon: PtrTimelineItem[];
  items: PtrTimelineItem[];
};

export type PtrFilterOptions = {
  responsibles: string[];
  organizations: string[];
  priorities: string[];
  statuses: string[];
  treatment_decisions: string[];
};

export type PtrMetadata = {
  project_id: string;
  assessment_id: string;
  read_only: boolean;
  limited_edit: boolean;
  editable_fields: string[];
};

export type PtrResponse = {
  summary: PtrSummary;
  rows: PtrActionRow[];
  timeline: PtrTimeline;
  total: number;
  page: number;
  page_size: number;
  filter_options: PtrFilterOptions;
  metadata: PtrMetadata;
};

export type PtrQuery = {
  search?: string;
  responsible?: string;
  organization?: string;
  priority?: string;
  status?: string;
  treatment_decision?: string;
  due_filter?: "overdue" | "due_soon" | "this_week" | "this_month";
  page?: number;
  page_size?: number;
};

export type PtrKpiKey =
  | "total"
  | "open"
  | "in_progress"
  | "completed"
  | "overdue"
  | "coverage";

export type PtrActionPatch = {
  status?: string;
  progress_percent?: number;
  budget?: number;
  budget_consumed?: number;
  due_date?: string;
  priority?: string;
};

export type TimelineScale = "today" | "week" | "month";
