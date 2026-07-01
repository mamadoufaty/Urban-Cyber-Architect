export interface EntityTypeDef {
  id: string;
  label: string;
  couche: string;
  color: string;
}

export interface RelationRule {
  id?: string;
  source: string;
  type: string;
  target: string;
  category: string;
}

export interface CreationGuideItem {
  direction: "incoming" | "outgoing";
  relation_id: string;
  label: string;
  relation_type: string;
  peer_type: string;
}

export interface Metamodel {
  entity_types: EntityTypeDef[];
  relation_rules: RelationRule[];
  relation_categories: Record<string, string>;
  couches: Array<{ id: string; label: string; color: string }>;
  creation_guides: Record<string, CreationGuideItem[]>;
  reference_relation_ids: string[];
  entity_profiles?: Record<string, { creation_order: number; progress_group: string; field_count: number }>;
}

export interface AssistedFieldOption {
  entity_id: string;
  label: string;
  entity_type: string;
}

export interface AssistedFormField {
  field_id: string;
  rule_id: string;
  label: string;
  relation_type: string;
  peer_type: string;
  direction: "incoming" | "outgoing";
  required: boolean;
  cardinality: { min: number; max: number | null };
  widget: "select" | "multi-select";
  options: AssistedFieldOption[];
  selected: string[];
  visible: boolean;
}

export interface AssistedFormSchema {
  entity_type: string;
  entity_label: string;
  label_field: { placeholder: string; required: boolean };
  fields: AssistedFormField[];
  required_field_ids: string[];
  hints: string[];
  creation_order: number;
}

export interface UrbanismAnalysis {
  orphans: Array<{ id: string; label: string; entity_type: string; couche: string }>;
  orphan_count: number;
  critical_relations: Array<Record<string, unknown>>;
  critical_count: number;
  inconsistencies: Array<Record<string, string>>;
  inconsistency_count: number;
  isolated_couches: string[];
}

export interface UrbanismProgress {
  groups: Array<{ id: string; label: string; status: "pending" | "partial" | "done"; count: number }>;
  overall_percent: number;
  total_entities: number;
  total_relations: number;
}

export interface AssistedCreateResponse {
  entity: UrbanismEntity;
  relations_created: UrbanismRelation[];
  analysis: UrbanismAnalysis;
  bindings_applied: number;
  reused?: boolean;
}

export interface DeduplicateResponse {
  merged_groups: number;
  entities_removed: number;
  relations_relocated: number;
  analysis: UrbanismAnalysis;
}

export interface AssistedLinkResponse {
  action: string;
  relation: UrbanismRelation | null;
  analysis: UrbanismAnalysis;
}

export interface MetamodelValidationReport {
  status: "ok" | "ko";
  expected_entities: Array<EntityTypeDef & { required?: boolean; note?: string }>;
  missing_entities: string[];
  extra_entities: string[];
  expected_relations: RelationRule[];
  implemented_relations: RelationRule[];
  missing_relations: RelationRule[];
  invalid_relations: RelationRule[];
  summary: {
    entities_expected: number;
    entities_implemented: number;
    relations_expected: number;
    relations_implemented: number;
    relations_missing_count: number;
    relations_invalid_count: number;
  };
}

export interface UrbanismEntity {
  id: string;
  project_id: string;
  entity_type: string;
  couche: string;
  label: string;
  description: string | null;
  properties: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface UrbanismRelation {
  id: string;
  project_id: string;
  source_id: string;
  target_id: string;
  relation_type: string;
  category: string;
  commentaire: string | null;
  criticite: string | null;
  properties: Record<string, unknown>;
  created_at: string;
}

export interface UrbanismGraph {
  project_id: string;
  project_name: string;
  organization: Record<string, string>;
  author: string;
  generated_at: string;
  model: string;
  nodes: Array<{
    id: string;
    type: string;
    entity_type: string;
    entity_type_label: string;
    couche: string;
    couche_label: string;
    couche_color: string;
    label: string;
    position: { x: number; y: number };
    layout?: import("./nodeLayoutTypes").NodeLayoutOverride | { mode: "auto"; locked: false; x?: number; y?: number };
  }>;
  edges: Array<{
    id: string;
    source: string;
    target: string;
    relation_type: string;
    category: string;
    criticite: string | null;
    commentaire: string | null;
    derived?: boolean;
    layout?: import("./edgeLayoutTypes").EdgeLayoutOverride | null;
  }>;
  meta_layers: Array<{ id: string; label: string; color: string; object_count: number }>;
  stats: {
    total_objects: number;
    total_relations: number;
    visible_objects: number;
    visible_relations: number;
    by_couche: Record<string, number>;
    by_relation_type: Record<string, number>;
  };
  analysis: {
    orphans: Array<{ id: string; label: string; entity_type: string; couche: string }>;
    orphan_count: number;
    critical_relations: Array<Record<string, unknown>>;
    critical_count: number;
    inconsistencies: Array<Record<string, string>>;
    inconsistency_count: number;
    isolated_couches: string[];
  };
  relation_categories: Record<string, string>;
  relation_type_legend: string[];
}

export const RELATION_FILTER_OPTIONS = [
  { id: "metier", label: "Relations métier" },
  { id: "organisation", label: "Relations organisationnelles" },
  { id: "fonctionnel", label: "Dépendances fonctionnelles" },
  { id: "applicatif", label: "Dépendances applicatives" },
  { id: "technique", label: "Dépendances techniques" },
  { id: "transverse", label: "Relations transverses" },
] as const;

export type RelationCategory = (typeof RELATION_FILTER_OPTIONS)[number]["id"];
