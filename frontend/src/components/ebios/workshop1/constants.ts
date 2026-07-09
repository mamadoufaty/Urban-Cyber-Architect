export const STAKEHOLDER_ROLES = [
  "Sponsor",
  "Direction générale",
  "RSSI",
  "DSI",
  "Responsable métier",
  "Responsable application",
  "Responsable technique",
  "Responsable exploitation",
  "Responsable urbanisme SI",
  "Responsable SOC",
  "Responsable OT",
  "Responsable infrastructure",
  "DPO",
  "Auditeur",
  "Prestataire",
  "Autre",
] as const;

export const BASELINE_STATUSES = ["En place", "Partiel", "Non appliqué", "À vérifier"] as const;

export const MATURITY_LEVELS = [
  { value: "1", label: "1 — Initial" },
  { value: "2", label: "2 — Répétable" },
  { value: "3", label: "3 — Défini" },
  { value: "4", label: "4 — Maîtrisé" },
  { value: "5", label: "5 — Optimisé" },
] as const;

export const DOCUMENT_TYPES = [
  "PSSI",
  "PCA",
  "PRA",
  "Politique de sécurité",
  "Procédure",
  "Norme ISO",
  "Contrat",
  "Exigence réglementaire",
  "Autre",
] as const;

export type ScopeFormData = {
  label: string;
  description: string;
  business_objectives: string;
  activities: string;
  applications: string;
  sites: string;
  regulatory_constraints: string;
};

export type StakeholderFormData = {
  label: string;
  role: string;
  organization: string;
  responsibility: string;
  contact: string;
  involvement_level: string;
};

export type BaselineFormData = {
  label: string;
  domain: string;
  description: string;
  status: string;
  maturity_level: string;
  iso27002_ref: string;
};

export type DocumentFormData = {
  label: string;
  doc_type: string;
  version: string;
  date: string;
  owner: string;
  link: string;
  comment: string;
};

export const EMPTY_SCOPE: ScopeFormData = {
  label: "",
  description: "",
  business_objectives: "",
  activities: "",
  applications: "",
  sites: "",
  regulatory_constraints: "",
};

export const EMPTY_STAKEHOLDER: StakeholderFormData = {
  label: "",
  role: "RSSI",
  organization: "",
  responsibility: "",
  contact: "",
  involvement_level: "",
};

export const EMPTY_BASELINE: BaselineFormData = {
  label: "",
  domain: "",
  description: "",
  status: "En place",
  maturity_level: "1",
  iso27002_ref: "",
};

export const EMPTY_DOCUMENT: DocumentFormData = {
  label: "",
  doc_type: "PSSI",
  version: "",
  date: "",
  owner: "",
  link: "",
  comment: "",
};

export function scopeFromRecord(record: import("../types").EbiosRecord): ScopeFormData {
  const p = record.properties ?? {};
  return {
    label: record.label,
    description: record.description ?? "",
    business_objectives: String(p.business_objectives ?? ""),
    activities: String(p.activities ?? ""),
    applications: String(p.applications ?? ""),
    sites: String(p.sites ?? ""),
    regulatory_constraints: String(p.regulatory_constraints ?? ""),
  };
}

export function stakeholderFromRecord(record: import("../types").EbiosRecord): StakeholderFormData {
  const p = record.properties ?? {};
  return {
    label: record.label,
    role: String(p.role ?? "RSSI"),
    organization: String(p.organization ?? ""),
    responsibility: String(p.responsibility ?? ""),
    contact: String(p.contact ?? ""),
    involvement_level: String(p.involvement_level ?? ""),
  };
}

export function baselineFromRecord(record: import("../types").EbiosRecord): BaselineFormData {
  const p = record.properties ?? {};
  return {
    label: record.label,
    domain: String(p.domain ?? ""),
    description: record.description ?? "",
    status: String(p.status ?? "En place"),
    maturity_level: String(p.maturity_level ?? "1"),
    iso27002_ref: String(p.iso27002_ref ?? ""),
  };
}

export function documentFromRecord(record: import("../types").EbiosRecord): DocumentFormData {
  const p = record.properties ?? {};
  return {
    label: record.label,
    doc_type: String(p.doc_type ?? "PSSI"),
    version: String(p.version ?? ""),
    date: String(p.date ?? ""),
    owner: String(p.owner ?? ""),
    link: String(p.link ?? ""),
    comment: String(p.comment ?? ""),
  };
}
