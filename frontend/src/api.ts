import type { UrbanismGraph } from "./components/urbanism/metamodel";

const API = "/api";

export async function fetchJSON<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API}${path}`, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `HTTP ${res.status}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

export interface Organization {
  name: string;
  sector: string;
  size: string;
  country: string;
}

export interface Project {
  id: string;
  name: string;
  description: string | null;
  organization: Organization;
  referentials: string[];
  objectives: string[];
  urbanism: Record<string, unknown>;
  status: string;
  created_at?: string;
  updated_at?: string;
}

export interface ProjectTemplate {
  id: string;
  label: string;
  description: string;
  default_name?: string;
  sector: string;
  is_example?: boolean;
}

export interface ProjectCreatePayload {
  name: string;
  template?: string;
  description?: string;
  organization?: Organization;
  referentials?: string[];
  objectives?: string[];
  urbanism?: Record<string, unknown>;
}

export function listProjects() {
  return fetchJSON<Project[]>("/projects");
}

export function getProject(id: string) {
  return fetchJSON<Project>(`/projects/${id}`);
}

export function listProjectTemplates() {
  return fetchJSON<ProjectTemplate[]>("/projects/templates/list");
}

export async function createProject(data: ProjectCreatePayload): Promise<Project> {
  const res = await fetch(`${API}/projects`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  const text = await res.text();
  if (!res.ok) {
    throw new Error(text || `HTTP ${res.status}`);
  }
  if (!text.trim()) {
    throw new Error("Projet créé mais ID absent dans la réponse API");
  }
  let project: Project;
  try {
    project = JSON.parse(text) as Project;
  } catch {
    throw new Error("Réponse API invalide (JSON)");
  }
  if (!project?.id) {
    throw new Error("Projet créé mais ID absent dans la réponse API");
  }
  return project;
}

export function updateProject(id: string, data: Partial<ProjectCreatePayload> & { status?: string }) {
  return fetchJSON<Project>(`/projects/${id}`, { method: "PUT", body: JSON.stringify(data) });
}

export class ProjectDeleteConflictError extends Error {
  dependencies: { name: string; count: number }[];

  constructor(message: string, dependencies: { name: string; count: number }[]) {
    super(message);
    this.name = "ProjectDeleteConflictError";
    this.dependencies = dependencies;
  }
}

export async function deleteProject(id: string) {
  const res = await fetch(`${API}/projects/${id}`, { method: "DELETE" });
  if (res.status === 409) {
    const body = (await res.json()) as {
      detail?: string;
      dependencies?: { name: string; count: number }[];
    };
    throw new ProjectDeleteConflictError(
      body.detail ?? "Impossible de supprimer ce projet : il contient encore des données liées.",
      body.dependencies ?? [],
    );
  }
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `HTTP ${res.status}`);
  }
}

export function duplicateProject(id: string) {
  return fetchJSON<Project>(`/projects/${id}/duplicate`, { method: "POST" });
}

export function orchestrate(projectId: string, template = "architecture_analysis") {
  return fetchJSON<Record<string, unknown>>(`/projects/${projectId}/orchestrate`, {
    method: "POST",
    body: JSON.stringify({ template_name: template }),
  });
}

export function getGovernance() {
  return fetchJSON<Record<string, unknown>>("/ai-governance");
}

export function listPrompts() {
  return fetchJSON<Array<{ name: string; version: string; description: string }>>("/prompts");
}

export function listSectors() {
  return fetchJSON<Array<{ id: string; name: string; domains: string[] }>>("/knowledge-base/sectors");
}

export function validateDecision(projectId: string, data: Record<string, unknown>) {
  return fetchJSON(`/projects/${projectId}/decisions`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function getUrbanismGraph(projectId: string, categories?: string[]) {
  const qs = categories?.length ? `?categories=${categories.join(",")}` : "";
  return fetchJSON<UrbanismGraph>(`/projects/${projectId}/urbanism/graph${qs}`);
}

/** @deprecated Utiliser getUrbanismGraph */
export function getUrbanismSchema(projectId: string, categories?: string[]) {
  const qs = categories?.length ? `?categories=${categories.join(",")}` : "";
  return fetchJSON<UrbanismGraph>(`/projects/${projectId}/urbanism-schema${qs}`);
}

export function getMetamodel() {
  return fetchJSON<import("./components/urbanism/metamodel").Metamodel>("/metamodel");
}

export function getMetamodelValidation() {
  return fetchJSON<import("./components/urbanism/metamodel").MetamodelValidationReport>("/metamodel/validation");
}

export function listUrbanismEntities(projectId: string) {
  return fetchJSON<import("./components/urbanism/metamodel").UrbanismEntity[]>(
    `/projects/${projectId}/urbanism/entities`
  );
}

export function createUrbanismEntity(
  projectId: string,
  data: {
    entity_type: string;
    label: string;
    description?: string;
    relations?: Array<{ relation_type: string; target_id?: string; source_id?: string; criticite?: string }>;
  }
) {
  return fetchJSON(`/projects/${projectId}/urbanism/entities`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function deleteUrbanismEntity(projectId: string, entityId: string) {
  return fetchJSON<void>(`/projects/${projectId}/urbanism/entities/${entityId}`, { method: "DELETE" });
}

export function listUrbanismRelations(projectId: string) {
  return fetchJSON<import("./components/urbanism/metamodel").UrbanismRelation[]>(
    `/projects/${projectId}/urbanism/relations`
  );
}

export function deleteUrbanismRelation(projectId: string, relationId: string) {
  return fetchJSON<void>(`/projects/${projectId}/urbanism/relations/${relationId}`, { method: "DELETE" });
}

export function saveEdgeLayout(
  projectId: string,
  edgeId: string,
  layout: import("./components/urbanism/edgeLayoutTypes").EdgeLayoutOverride
) {
  return fetchJSON<{ edge_id: string; layout: import("./components/urbanism/edgeLayoutTypes").EdgeLayoutOverride }>(
    `/projects/${projectId}/urbanism/edges/${encodeURIComponent(edgeId)}/layout`,
    { method: "PUT", body: JSON.stringify({ layout }) }
  );
}

export function clearEdgeLayout(projectId: string, edgeId: string) {
  return fetchJSON<void>(
    `/projects/${projectId}/urbanism/edges/${encodeURIComponent(edgeId)}/layout`,
    { method: "DELETE" }
  );
}

export function saveEntityLayout(
  projectId: string,
  entityId: string,
  layout: { x: number; y: number }
) {
  return fetchJSON<{ entity_id: string; layout: import("./components/urbanism/nodeLayoutTypes").NodeLayoutOverride }>(
    `/projects/${projectId}/urbanism/entities/${entityId}/layout`,
    { method: "PUT", body: JSON.stringify({ layout }) }
  );
}

export function saveEntityLayoutsBulk(
  projectId: string,
  layouts: Array<{ entity_id: string; layout: { x: number; y: number } }>
) {
  return fetchJSON<{ layouts: Array<{ entity_id: string; layout: import("./components/urbanism/nodeLayoutTypes").NodeLayoutOverride }> }>(
    `/projects/${projectId}/urbanism/entities/layout/bulk`,
    { method: "PUT", body: JSON.stringify({ layouts }) }
  );
}

export function clearEntityLayout(projectId: string, entityId: string) {
  return fetchJSON<void>(`/projects/${projectId}/urbanism/entities/${entityId}/layout`, { method: "DELETE" });
}

export function getAssistantFormSchema(projectId: string, entityType: string) {
  return fetchJSON<import("./components/urbanism/metamodel").AssistedFormSchema>(
    `/projects/${projectId}/urbanism/assistant/form-schema?entity_type=${encodeURIComponent(entityType)}`
  );
}

export function assistantCreate(
  projectId: string,
  data: { entity_type: string; label: string; bindings: Record<string, string[]> }
) {
  return fetchJSON<import("./components/urbanism/metamodel").AssistedCreateResponse>(
    `/projects/${projectId}/urbanism/assistant/create`,
    { method: "POST", body: JSON.stringify(data) }
  );
}

export function assistantLink(
  projectId: string,
  data: { action: "add" | "remove" | "replace"; rule_id: string; source_id: string; target_id: string }
) {
  return fetchJSON<import("./components/urbanism/metamodel").AssistedLinkResponse>(
    `/projects/${projectId}/urbanism/assistant/link`,
    { method: "POST", body: JSON.stringify(data) }
  );
}

export function getUrbanismProgress(projectId: string) {
  return fetchJSON<import("./components/urbanism/metamodel").UrbanismProgress>(
    `/projects/${projectId}/urbanism/progress`
  );
}

export function deduplicateUrbanism(projectId: string) {
  return fetchJSON<import("./components/urbanism/metamodel").DeduplicateResponse>(
    `/projects/${projectId}/urbanism/deduplicate`,
    { method: "POST" }
  );
}

export function getGraph(projectId: string) {
  return fetchJSON<{ nodes: unknown[]; edges: unknown[] }>(`/projects/${projectId}/graph`);
}

// ——— EBIOS RM ———

export function getEbiosMetamodel() {
  return fetchJSON<import("./components/ebios/types").EbiosMetamodel>("/metamodel/ebios");
}

export function getEbiosExtensions() {
  return fetchJSON<import("./components/ebios/types").EbiosExtensionRegistry>("/ebios/extensions");
}

export function getEbiosAssessment(projectId: string) {
  return fetchJSON<import("./components/ebios/types").EbiosAssessment>(
    `/projects/${projectId}/ebios/assessment`
  );
}

export function getEbiosOverview(projectId: string, assessmentId: string) {
  return fetchJSON<import("./components/ebios/types").EbiosOverview>(
    `/projects/${projectId}/ebios/assessments/${assessmentId}/overview`
  );
}

export function getEbiosRecords(projectId: string, assessmentId: string, workshopNumber?: number) {
  const qs = workshopNumber != null ? `?workshop_number=${workshopNumber}` : "";
  return fetchJSON<import("./components/ebios/types").EbiosRecord[]>(
    `/projects/${projectId}/ebios/assessments/${assessmentId}/records${qs}`
  );
}

export type EbiosRecordPayload = {
  workshop_number: number;
  record_type: string;
  label: string;
  description?: string | null;
  properties?: Record<string, unknown>;
  status?: string;
  sort_order?: number;
};

export type EbiosRecordUpdatePayload = {
  label?: string;
  description?: string | null;
  properties?: Record<string, unknown>;
  status?: string;
  sort_order?: number;
};

export function createEbiosRecord(
  projectId: string,
  assessmentId: string,
  data: EbiosRecordPayload
) {
  return fetchJSON<import("./components/ebios/types").EbiosRecord>(
    `/projects/${projectId}/ebios/assessments/${assessmentId}/records`,
    { method: "POST", body: JSON.stringify(data) }
  );
}

export function updateEbiosRecord(
  projectId: string,
  assessmentId: string,
  recordId: string,
  data: EbiosRecordUpdatePayload
) {
  return fetchJSON<import("./components/ebios/types").EbiosRecord>(
    `/projects/${projectId}/ebios/assessments/${assessmentId}/records/${recordId}`,
    { method: "PATCH", body: JSON.stringify(data) }
  );
}

export function deleteEbiosRecord(projectId: string, assessmentId: string, recordId: string) {
  return fetchJSON<void>(
    `/projects/${projectId}/ebios/assessments/${assessmentId}/records/${recordId}`,
    { method: "DELETE" }
  );
}

export function importEbiosUrbanismAssets(projectId: string, assessmentId: string) {
  return fetchJSON<{ imported_count: number; records: import("./components/ebios/types").EbiosRecord[] }>(
    `/projects/${projectId}/ebios/assessments/${assessmentId}/workshop2/import-urbanism-assets`,
    { method: "POST" }
  );
}

export function generateEbiosStrategicScenarios(
  projectId: string,
  assessmentId: string,
  regenerate = false
) {
  const qs = regenerate ? "?regenerate=true" : "";
  return fetchJSON<{
    generated_count: number;
    records: import("./components/ebios/types").EbiosRecord[];
  }>(
    `/projects/${projectId}/ebios/assessments/${assessmentId}/workshop3/generate-scenarios${qs}`,
    { method: "POST" }
  );
}

export function getEbiosWorkshop4(projectId: string, assessmentId: string) {
  return fetchJSON<{
    scenarios: import("./components/ebios/types").EbiosRecord[];
    validated_strategic_count: number;
    operational_count: number;
  }>(`/projects/${projectId}/ebios/assessments/${assessmentId}/workshop4`);
}

export function generateEbiosOperationalScenarios(
  projectId: string,
  assessmentId: string,
  regenerate = false
) {
  const qs = regenerate ? "?regenerate=true" : "";
  return fetchJSON<{
    generated_count: number;
    records: import("./components/ebios/types").EbiosRecord[];
  }>(
    `/projects/${projectId}/ebios/assessments/${assessmentId}/workshop4/generate-operational-scenarios${qs}`,
    { method: "POST" }
  );
}

export function patchEbiosOperationalScenario(
  projectId: string,
  assessmentId: string,
  scenarioId: string,
  data: { label?: string; properties?: Record<string, unknown>; set_validated?: boolean }
) {
  return fetchJSON<import("./components/ebios/types").EbiosRecord>(
    `/projects/${projectId}/ebios/assessments/${assessmentId}/workshop4/scenarios/${scenarioId}`,
    { method: "PATCH", body: JSON.stringify(data) }
  );
}

export function deleteEbiosOperationalScenario(
  projectId: string,
  assessmentId: string,
  scenarioId: string
) {
  return fetchJSON<void>(
    `/projects/${projectId}/ebios/assessments/${assessmentId}/workshop4/scenarios/${scenarioId}`,
    { method: "DELETE" }
  );
}

export function getEbiosWorkshop5(projectId: string, assessmentId: string) {
  return fetchJSON<import("./components/ebios/workshop5/constants").Workshop5Data>(
    `/projects/${projectId}/ebios/assessments/${assessmentId}/workshop5`
  );
}

export function generateEbiosTreatments(
  projectId: string,
  assessmentId: string,
  regenerate = false
) {
  const qs = regenerate ? "?regenerate=true" : "";
  return fetchJSON<{
    generated_count: number;
    records: import("./components/ebios/types").EbiosRecord[];
  }>(
    `/projects/${projectId}/ebios/assessments/${assessmentId}/workshop5/generate-treatments${qs}`,
    { method: "POST" }
  );
}

export function patchEbiosRiskEvaluation(
  projectId: string,
  assessmentId: string,
  evaluationId: string,
  data: { treatment_decision?: string; properties?: Record<string, unknown>; set_validated?: boolean }
) {
  return fetchJSON<import("./components/ebios/types").EbiosRecord>(
    `/projects/${projectId}/ebios/assessments/${assessmentId}/workshop5/evaluations/${evaluationId}`,
    { method: "PATCH", body: JSON.stringify(data) }
  );
}

export function patchEbiosSecurityMeasure(
  projectId: string,
  assessmentId: string,
  measureId: string,
  properties: Record<string, unknown>
) {
  return fetchJSON<import("./components/ebios/types").EbiosRecord>(
    `/projects/${projectId}/ebios/assessments/${assessmentId}/workshop5/measures/${measureId}`,
    { method: "PATCH", body: JSON.stringify({ properties }) }
  );
}

export function patchEbiosTreatmentAction(
  projectId: string,
  assessmentId: string,
  actionId: string,
  properties: Record<string, unknown>
) {
  return fetchJSON<import("./components/ebios/types").EbiosRecord>(
    `/projects/${projectId}/ebios/assessments/${assessmentId}/workshop5/actions/${actionId}`,
    { method: "PATCH", body: JSON.stringify({ properties }) }
  );
}

export function deleteEbiosRiskEvaluation(
  projectId: string,
  assessmentId: string,
  evaluationId: string
) {
  return fetchJSON<void>(
    `/projects/${projectId}/ebios/assessments/${assessmentId}/workshop5/evaluations/${evaluationId}`,
    { method: "DELETE" }
  );
}

// ——— GRC ———

function buildRiskRegisterQuery(params: import("./components/grc/types").RiskRegisterQuery): string {
  const qs = new URLSearchParams();
  if (params.search) qs.set("search", params.search);
  if (params.organization) qs.set("organization", params.organization);
  if (params.severity) qs.set("severity", params.severity);
  if (params.criticality) qs.set("criticality", params.criticality);
  if (params.treatment_decision) qs.set("treatment_decision", params.treatment_decision);
  if (params.status) qs.set("status", params.status);
  if (params.sort_by) qs.set("sort_by", params.sort_by);
  if (params.sort_dir) qs.set("sort_dir", params.sort_dir);
  if (params.page) qs.set("page", String(params.page));
  if (params.page_size) qs.set("page_size", String(params.page_size));
  const text = qs.toString();
  return text ? `?${text}` : "";
}

export function getRiskRegister(
  projectId: string,
  params: import("./components/grc/types").RiskRegisterQuery = {}
) {
  return fetchJSON<import("./components/grc/types").RiskRegisterResponse>(
    `/projects/${projectId}/grc/risk-register${buildRiskRegisterQuery(params)}`
  );
}

export async function exportRiskRegister(
  projectId: string,
  format: "csv" | "xlsx" | "pdf",
  params: import("./components/grc/types").RiskRegisterQuery = {}
) {
  const qs = new URLSearchParams(buildRiskRegisterQuery(params).replace(/^\?/, ""));
  qs.set("format", format);
  const res = await fetch(`${API}/projects/${projectId}/grc/risk-register/export?${qs.toString()}`);
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `HTTP ${res.status}`);
  }
  const blob = await res.blob();
  const ext = format === "xlsx" ? "xlsx" : format;
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `registre-risques.${ext}`;
  anchor.click();
  URL.revokeObjectURL(url);
}

export function getRssiDashboard(projectId: string) {
  return fetchJSON<import("./components/grc/dashboardTypes").RssiDashboardResponse>(
    `/projects/${projectId}/grc/dashboard-rssi`
  );
}

function buildSoaQuery(params: import("./components/grc/soa/types").SoaQuery): string {
  const qs = new URLSearchParams();
  if (params.search) qs.set("search", params.search);
  if (params.iso_reference) qs.set("iso_reference", params.iso_reference);
  if (params.applicable) qs.set("applicable", params.applicable);
  if (params.implemented) qs.set("implemented", params.implemented);
  if (params.responsible) qs.set("responsible", params.responsible);
  if (params.status) qs.set("status", params.status);
  if (params.page) qs.set("page", String(params.page));
  if (params.page_size) qs.set("page_size", String(params.page_size));
  const text = qs.toString();
  return text ? `?${text}` : "";
}

export function getSoa(
  projectId: string,
  params: import("./components/grc/soa/types").SoaQuery = {}
) {
  return fetchJSON<import("./components/grc/soa/types").SoaResponse>(
    `/projects/${projectId}/grc/soa${buildSoaQuery(params)}`
  );
}

export async function exportSoa(
  projectId: string,
  format: "csv" | "xlsx" | "pdf",
  params: import("./components/grc/soa/types").SoaQuery = {}
) {
  const qs = new URLSearchParams(buildSoaQuery(params).replace(/^\?/, ""));
  qs.set("format", format);
  const res = await fetch(`${API}/projects/${projectId}/grc/soa/export?${qs.toString()}`);
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `HTTP ${res.status}`);
  }
  const blob = await res.blob();
  const ext = format === "xlsx" ? "xlsx" : format;
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `declaration-applicabilite.${ext}`;
  anchor.click();
  URL.revokeObjectURL(url);
}

function buildPtrQuery(params: import("./components/grc/ptr/types").PtrQuery): string {
  const qs = new URLSearchParams();
  if (params.search) qs.set("search", params.search);
  if (params.responsible) qs.set("responsible", params.responsible);
  if (params.organization) qs.set("organization", params.organization);
  if (params.priority) qs.set("priority", params.priority);
  if (params.status) qs.set("status", params.status);
  if (params.treatment_decision) qs.set("treatment_decision", params.treatment_decision);
  if (params.due_filter) qs.set("due_filter", params.due_filter);
  if (params.page) qs.set("page", String(params.page));
  if (params.page_size) qs.set("page_size", String(params.page_size));
  const text = qs.toString();
  return text ? `?${text}` : "";
}

export function getPtr(
  projectId: string,
  params: import("./components/grc/ptr/types").PtrQuery = {}
) {
  return fetchJSON<import("./components/grc/ptr/types").PtrResponse>(
    `/projects/${projectId}/grc/ptr${buildPtrQuery(params)}`
  );
}

export function patchPtrAction(
  projectId: string,
  actionId: string,
  patch: import("./components/grc/ptr/types").PtrActionPatch
) {
  return fetchJSON<unknown>(`/projects/${projectId}/grc/ptr/actions/${actionId}`, {
    method: "PATCH",
    body: JSON.stringify(patch),
  });
}

export async function exportPtr(
  projectId: string,
  format: "csv" | "xlsx" | "pdf",
  params: import("./components/grc/ptr/types").PtrQuery = {}
) {
  const qs = new URLSearchParams(buildPtrQuery(params).replace(/^\?/, ""));
  qs.set("format", format);
  const res = await fetch(`${API}/projects/${projectId}/grc/ptr/export?${qs.toString()}`);
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `HTTP ${res.status}`);
  }
  const blob = await res.blob();
  const ext = format === "xlsx" ? "xlsx" : format;
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `plan-traitement-risques.${ext}`;
  anchor.click();
  URL.revokeObjectURL(url);
}

// ——— Connecteur Wazuh (SOC) ———

export type WazuhConfig = {
  base_url: string;
  username: string;
  password_configured: boolean;
  verify_ssl: boolean;
  indexer_url: string;
  indexer_username: string;
  indexer_password_configured: boolean;
  enabled: boolean;
  last_sync_at: string | null;
  updated_at: string | null;
};

export type WazuhTestResult = {
  success: boolean;
  error?: string | null;
  api_version?: string | null;
  wazuh_version?: string | null;
  manager?: string | null;
  agents_total?: number | null;
};

export type WazuhStatus = {
  connected: boolean;
  configured: boolean;
  wazuh_version: string;
  api_version: string;
  manager: string;
  agents_total: number;
  agents_active: number;
  last_sync_at: string | null;
  read_only: boolean;
  error: string | null;
  alerts_source: string;
};

export type WazuhAlertItem = {
  id: string;
  timestamp: string;
  rule_id: string;
  rule_level: number;
  rule_description: string;
  agent_id: string;
  agent_name: string;
  full_log: string;
  groups: string[];
};

export function getWazuhConfig() {
  return fetchJSON<WazuhConfig>("/connectors/wazuh/config");
}

export function saveWazuhConfig(
  payload: Partial<WazuhConfig> & { password?: string; indexer_password?: string }
) {
  return fetchJSON<WazuhConfig>("/connectors/wazuh/config", {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export function testWazuhConnection() {
  return fetchJSON<WazuhTestResult>("/connectors/wazuh/test", { method: "POST" });
}

export function getWazuhStatus() {
  return fetchJSON<WazuhStatus>("/connectors/wazuh/status");
}

export function getWazuhAgents(params: { limit?: number; offset?: number } = {}) {
  const qs = new URLSearchParams();
  if (params.limit) qs.set("limit", String(params.limit));
  if (params.offset) qs.set("offset", String(params.offset));
  const q = qs.toString();
  return fetchJSON<{ agents: Array<Record<string, string>>; total: number }>(
    `/connectors/wazuh/agents${q ? `?${q}` : ""}`
  );
}

export function getWazuhAlerts(params: { limit?: number; offset?: number } = {}) {
  const qs = new URLSearchParams();
  if (params.limit) qs.set("limit", String(params.limit));
  if (params.offset) qs.set("offset", String(params.offset));
  const q = qs.toString();
  return fetchJSON<{ alerts: WazuhAlertItem[]; total: number }>(
    `/connectors/wazuh/alerts${q ? `?${q}` : ""}`
  );
}

export function getWazuhAlert(alertId: string) {
  return fetchJSON<{ alert: WazuhAlertItem }>(`/connectors/wazuh/alert/${encodeURIComponent(alertId)}`);
}

// ——— SOC Corrélations ———

export type SocIncident = {
  incident_id: string;
  alert: {
    id: string;
    timestamp: string;
    rule_id: string;
    rule_level: number;
    rule_description: string;
    severity: string;
    category: string;
    full_log: string;
  };
  agent: { id: string; name: string; ip: string };
  supporting_asset: string;
  urbanism_entity_id: string | null;
  urbanism_entity_label: string;
  organization: string;
  processus: string;
  operational_scenario: string;
  strategic_scenario: string;
  risk_source: string;
  grc_risk: {
    risk_id: string;
    criticality: string;
    treatment_decision: string;
    residual_risk: string;
    status: string;
  };
  business_owner: string;
  asset_match: { method: string; confidence: number };
  mitre: Record<string, unknown>;
  correlation_seed: Record<string, boolean>;
  correlated_at: string;
  read_only: boolean;
};

export type SocCorrelationsResponse = {
  summary: {
    project_name: string;
    generated_at: string;
    alerts_total: number;
    incidents_count: number;
    correlated_risks: number;
    assets_matched: number;
    read_only: boolean;
  };
  incidents: SocIncident[];
  total: number;
  limit: number;
  offset: number;
  metadata: {
    project_id: string;
    assessment_id: string;
    wazuh_error: string | null;
    risk_register_rows: number;
    urbanism_entities: number;
    read_only: boolean;
  };
};

export function getSocCorrelations(
  projectId: string,
  params: { limit?: number; offset?: number } = {}
) {
  const qs = new URLSearchParams({ project_id: projectId });
  if (params.limit) qs.set("limit", String(params.limit));
  if (params.offset) qs.set("offset", String(params.offset));
  return fetchJSON<SocCorrelationsResponse>(`/soc/correlations?${qs.toString()}`);
}

// ——— Livrables documentaires ———

export type DeliverableTypeOption = { id: string; label: string };

export type DeliverableSummary = {
  id: string;
  project_id: string;
  title: string;
  deliverable_type: string;
  user_need: string;
  data_sources: string[];
  export_format: string;
  status: string;
  created_at: string;
  updated_at: string;
};

export type DeliverableSection = {
  id?: string;
  title: string;
  content: string;
  bullets?: string[];
};

export type DeliverableContent = {
  title: string;
  user_need: string;
  sections: DeliverableSection[];
  metadata?: {
    generated_at?: string;
    project_name?: string;
    deliverable_type_label?: string;
  };
};

export type DeliverableDetail = DeliverableSummary & {
  generated_content: DeliverableContent;
};

export type DeliverablesListResponse = {
  deliverables: DeliverableSummary[];
  total: number;
  types: DeliverableTypeOption[];
  data_sources: string[];
  export_formats: string[];
};

export type DeliverableGenerateRequest = {
  title: string;
  deliverable_type: string;
  user_need: string;
  data_sources: string[];
  export_format: "pdf" | "docx" | "markdown";
  preview?: boolean;
};

export type DeliverableGenerateResponse = {
  preview: boolean;
  deliverable: DeliverableDetail | null;
  generated_content: DeliverableContent;
};

export function getDeliverables(projectId: string) {
  return fetchJSON<DeliverablesListResponse>(`/projects/${projectId}/deliverables`);
}

export function generateDeliverable(projectId: string, payload: DeliverableGenerateRequest) {
  return fetchJSON<DeliverableGenerateResponse>(`/projects/${projectId}/deliverables/generate`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getDeliverable(projectId: string, deliverableId: string) {
  return fetchJSON<DeliverableDetail>(`/projects/${projectId}/deliverables/${deliverableId}`);
}

export async function exportDeliverable(
  projectId: string,
  deliverableId: string,
  format: "pdf" | "docx" | "markdown" = "pdf"
) {
  const response = await fetch(
    `${API}/projects/${projectId}/deliverables/${deliverableId}/export?format=${format}`
  );
  if (!response.ok) {
    throw new Error(`Export échoué (${response.status})`);
  }
  const blob = await response.blob();
  const ext = format === "markdown" ? "md" : format;
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `livrable.${ext}`;
  anchor.click();
  URL.revokeObjectURL(url);
}

// ——— Administration ———

export interface AdminUser {
  id: string;
  username: string;
  first_name: string | null;
  last_name: string | null;
  email: string | null;
  phone: string | null;
  organization_id: string | null;
  function: string | null;
  role_id: string | null;
  status: string;
  avatar: string | null;
  last_login_at: string | null;
  failed_login_count: number;
  locked_until: string | null;
  created_at: string;
  updated_at: string;
  role_code: string | null;
  organization_name: string | null;
}

export interface AdminUsersListResponse {
  total: number;
  items: AdminUser[];
}

export interface AdminRole {
  id: string;
  name: string;
  code: string;
  description: string | null;
  is_system: boolean;
}

export interface AdminRolesListResponse {
  total: number;
  items: AdminRole[];
}

export interface AdminOrganization {
  id: string;
  name: string;
  code: string;
  description: string | null;
  status: string;
}

export interface AdminOrganizationsListResponse {
  total: number;
  items: AdminOrganization[];
}

export type AdminUserCreatePayload = {
  username: string;
  password: string;
  first_name?: string;
  last_name?: string;
  email?: string;
  phone?: string;
  organization_id?: string;
  function?: string;
  role_id?: string;
  status?: string;
};

export type AdminUserUpdatePayload = {
  first_name?: string;
  last_name?: string;
  email?: string;
  phone?: string;
  organization_id?: string | null;
  function?: string;
  role_id?: string | null;
  status?: string;
};

export function listAdminUsers() {
  return fetchJSON<AdminUsersListResponse>("/admin/users");
}

export function createAdminUser(payload: AdminUserCreatePayload) {
  return fetchJSON<AdminUser>("/admin/users", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateAdminUser(userId: string, payload: AdminUserUpdatePayload) {
  return fetchJSON<AdminUser>(`/admin/users/${userId}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export function deleteAdminUser(userId: string) {
  return fetchJSON<void>(`/admin/users/${userId}`, { method: "DELETE" });
}

export function disableAdminUser(userId: string) {
  return fetchJSON<AdminUser>(`/admin/users/${userId}/disable`, { method: "PATCH" });
}

export function enableAdminUser(userId: string) {
  return fetchJSON<AdminUser>(`/admin/users/${userId}/enable`, { method: "PATCH" });
}

export function resetAdminUserPassword(userId: string, password: string) {
  return fetchJSON<AdminUser>(`/admin/users/${userId}/reset-password`, {
    method: "PATCH",
    body: JSON.stringify({ password }),
  });
}

export function listAdminRoles() {
  return fetchJSON<AdminRolesListResponse>("/admin/roles");
}

export function listAdminOrganizations() {
  return fetchJSON<AdminOrganizationsListResponse>("/admin/organizations");
}
