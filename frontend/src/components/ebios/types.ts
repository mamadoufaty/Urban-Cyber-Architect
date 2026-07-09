export type EbiosWorkshopSpec = {
  number: number;
  code: string;
  label: string;
  short_label: string;
  description: string;
  record_types: string[];
};

export type EbiosMetamodel = {
  workshops: EbiosWorkshopSpec[];
  record_type_labels: Record<string, string>;
  extension_modules: EbiosExtensionModule[];
  integration_hooks: EbiosIntegrationHook[];
  version: string;
};

export type EbiosExtensionModule = {
  id: string;
  label: string;
  status: "planned" | "available" | "beta";
  description: string;
};

export type EbiosIntegrationHook = {
  id: string;
  label: string;
  status: "planned" | "available" | "beta";
  description: string;
};

export type EbiosAssessment = {
  id: string;
  project_id: string;
  cartography_id: string | null;
  title: string;
  description: string | null;
  status: string;
  current_workshop: number;
  version: string;
  metadata: Record<string, unknown>;
  extension_flags: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export type EbiosWorkshop = {
  id: string;
  assessment_id: string;
  workshop_number: number;
  code: string;
  status: string;
  progress_percent: number;
  summary: Record<string, unknown>;
  content: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export type EbiosRecord = {
  id: string;
  assessment_id: string;
  workshop_number: number;
  record_type: string;
  label: string;
  description: string | null;
  properties: Record<string, unknown>;
  status: string;
  sort_order: number;
  created_at: string;
  updated_at: string;
};

export type EbiosOverview = {
  assessment: EbiosAssessment;
  workshops: EbiosWorkshop[];
  record_counts_by_workshop: Record<string, number>;
  link_count: number;
  overall_progress_percent: number;
};

export type EbiosExtensionRegistry = {
  metamodel: EbiosMetamodel;
  future_modules: EbiosExtensionModule[];
  integrations: EbiosIntegrationHook[];
};
