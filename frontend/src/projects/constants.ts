export const PROJECT_ROLES = [
  { value: "sponsor", label: "Sponsor" },
  { value: "chef_projet", label: "Chef de projet" },
  { value: "ceo_direction_generale", label: "CEO / Direction générale" },
  { value: "dsi", label: "DSI" },
  { value: "rssi", label: "RSSI" },
  { value: "architecte_si", label: "Architecte SI" },
  { value: "architecte_cyber", label: "Architecte cyber" },
  { value: "consultant_cybersecurite", label: "Consultant cybersécurité" },
  { value: "responsable_metier", label: "Responsable métier" },
  { value: "responsable_infrastructure", label: "Responsable infrastructure" },
  { value: "responsable_reseau", label: "Responsable réseau" },
  { value: "responsable_cloud", label: "Responsable cloud" },
  { value: "soc_manager", label: "SOC Manager" },
  { value: "analyste_soc", label: "Analyste SOC" },
  { value: "dpo", label: "DPO" },
  { value: "responsable_conformite", label: "Responsable conformité" },
  { value: "auditeur", label: "Auditeur" },
] as const;

export type ProjectRoleValue = (typeof PROJECT_ROLES)[number]["value"];

export const PROJECT_STATUS_OPTIONS = [
  { value: "draft", label: "Brouillon" },
  { value: "active", label: "Actif" },
  { value: "in_progress", label: "En cours" },
  { value: "on_hold", label: "En pause" },
  { value: "completed", label: "Terminé" },
  { value: "archived", label: "Archivé" },
] as const;

export const PROJECT_PRIORITY_OPTIONS = [
  { value: "low", label: "Basse" },
  { value: "medium", label: "Moyenne" },
  { value: "high", label: "Haute" },
  { value: "critical", label: "Critique" },
] as const;

export const REFERENTIAL_OPTIONS = [
  "RGPD",
  "NIS2",
  "EBIOS RM",
  "ISO 27001",
  "ISO 27002",
  "ISO 27005",
  "IEC 62443",
  "ANSSI",
  "DORA",
  "HDS",
  "PCI DSS",
  "SOC 2",
] as const;

export const PROJECT_ACTIVITY_LABELS: Record<string, string> = {
  "project.created": "Projet créé",
  "project.updated": "Projet modifié",
  "project.duplicated": "Projet dupliqué",
  "project.archived": "Projet archivé",
  "project.deleted": "Projet supprimé",
  "member.added": "Membre ajouté",
  "member.removed": "Membre retiré",
};

export function projectRoleLabel(role: string): string {
  return PROJECT_ROLES.find((r) => r.value === role)?.label ?? role;
}

export function projectStatusLabel(status: string): string {
  return PROJECT_STATUS_OPTIONS.find((s) => s.value === status)?.label ?? status;
}

export function projectPriorityLabel(priority: string): string {
  return PROJECT_PRIORITY_OPTIONS.find((p) => p.value === priority)?.label ?? priority;
}

export function activityActionLabel(action: string): string {
  return PROJECT_ACTIVITY_LABELS[action] ?? action;
}
