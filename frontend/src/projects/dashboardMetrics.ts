import type { Project, ProjectActivity } from "../api";
import { activityActionLabel } from "./constants";

export type ModuleStatus = "not_started" | "in_progress" | "completed" | "planned";

export type ModuleProgressItem = {
  id: string;
  label: string;
  status: ModuleStatus;
  percent: number;
  lastActivity: string | null;
  openUrl: string;
};

export type TimelineItem = {
  id: string;
  action: string;
  label: string;
  date: string;
  details?: string;
  kind: "past" | "future";
};

export type NextActionItem = {
  id: string;
  label: string;
  description: string;
  openUrl: string;
  priority: "high" | "medium" | "low";
};

export type DashboardKpis = {
  globalProgress: number;
  memberCount: number;
  activityCount: number;
  activeModulesCount: number;
  deliverableCount: number;
  riskCount: number;
  maturityLevel: string;
};

export function countUrbanismObjects(project: Project): number {
  const club = (project.urbanism?.club_urba ?? {}) as Record<string, Record<string, string[]>>;
  let count = 0;
  for (const couche of Object.values(club)) {
    if (typeof couche !== "object") continue;
    for (const items of Object.values(couche)) {
      if (Array.isArray(items)) count += items.length;
    }
  }
  return count;
}

export function deriveModuleStatus(percent: number, planned = false): ModuleStatus {
  if (planned) return "planned";
  if (percent >= 100) return "completed";
  if (percent > 0) return "in_progress";
  return "not_started";
}

export function moduleStatusLabel(status: ModuleStatus): string {
  switch (status) {
    case "completed":
      return "Terminé";
    case "in_progress":
      return "En cours";
    case "planned":
      return "Planifié";
    default:
      return "Non démarré";
  }
}

export function computeMaturityLevel(globalProgress: number): string {
  if (globalProgress >= 76) return "Avancé";
  if (globalProgress >= 51) return "En maturation";
  if (globalProgress >= 26) return "En structuration";
  return "Initial";
}

export function computeGlobalProgress(modules: ModuleProgressItem[]): number {
  if (modules.length === 0) return 0;
  const total = modules.reduce((sum, mod) => sum + mod.percent, 0);
  return Math.round(total / modules.length);
}

export function countActiveModules(modules: ModuleProgressItem[]): number {
  return modules.filter((mod) => mod.status === "in_progress" || mod.status === "completed").length;
}

export function grcProgressFromRiskCount(riskCount: number): number {
  if (riskCount <= 0) return 0;
  return Math.min(100, 25 + riskCount * 8);
}

export function socProgressFromIncidents(incidentCount: number, urbanismEntities: number): number {
  if (incidentCount > 0) return Math.min(100, 35 + incidentCount * 10);
  if (urbanismEntities > 0) return 15;
  return 0;
}

export function deliverablesProgress(count: number): number {
  if (count <= 0) return 0;
  return Math.min(100, count * 30);
}

export function aiProgressFromSignals(objectivesCount: number, graphNodeCount: number): number {
  if (graphNodeCount > 0) return Math.min(100, 40 + graphNodeCount * 5);
  if (objectivesCount > 0) return 20;
  return 0;
}

export function findLastActivityDate(
  activities: ProjectActivity[],
  predicate: (action: string) => boolean,
): string | null {
  const match = activities.find((item) => predicate(item.action));
  return match?.created_at ?? null;
}

export function mapActivitiesToTimeline(activities: ProjectActivity[]): TimelineItem[] {
  return [...activities]
    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
    .map((item) => ({
      id: item.id,
      action: item.action,
      label: activityActionLabel(item.action),
      date: item.created_at,
      details: formatTimelineDetails(item),
      kind: "past" as const,
    }));
}

function formatTimelineDetails(item: ProjectActivity): string | undefined {
  const details = item.details ?? {};
  if (typeof details.name === "string") return details.name as string;
  if (Array.isArray(details.fields)) return `Champs : ${(details.fields as string[]).join(", ")}`;
  if (typeof details.project_role === "string") return details.project_role as string;
  if (typeof details.new_name === "string") return details.new_name as string;
  return undefined;
}

export function appendFutureTimelineItems(items: TimelineItem[]): TimelineItem[] {
  return [
    ...items,
    {
      id: "future-modules",
      action: "future.modules",
      label: "Enrichissement des modules",
      date: "",
      details: "Urbanisme, EBIOS, GRC, SOC et livrables",
      kind: "future",
    },
    {
      id: "future-deliverables",
      action: "future.deliverables",
      label: "Génération de livrables",
      date: "",
      details: "Exports PDF et documents de gouvernance",
      kind: "future",
    },
  ];
}

export function buildNextActions(
  projectId: string,
  modules: ModuleProgressItem[],
): NextActionItem[] {
  const byId = new Map(modules.map((mod) => [mod.id, mod]));
  const actions: NextActionItem[] = [];

  const urbanism = byId.get("urbanism");
  if (urbanism && urbanism.percent < 50) {
    actions.push({
      id: "complete-urbanism",
      label: "Compléter l'urbanisme SI",
      description: "Enrichir la cartographie Club Urba et les relations entre entités.",
      openUrl: `/schema-urbanisme?project=${projectId}`,
      priority: "high",
    });
  }

  const ebios = byId.get("ebios");
  if (ebios && ebios.percent < 30) {
    actions.push({
      id: "start-ebios",
      label: "Lancer EBIOS RM",
      description: "Initialiser les ateliers et structurer l'analyse de risques.",
      openUrl: `/ebios?project=${projectId}`,
      priority: "high",
    });
  }

  const grc = byId.get("grc");
  if (grc && grc.percent < 40) {
    actions.push({
      id: "fill-grc",
      label: "Renseigner la GRC",
      description: "Alimenter le registre des risques et le pilotage RSSI.",
      openUrl: `/registre-risques?project=${projectId}`,
      priority: "medium",
    });
  }

  const siem = byId.get("siem");
  if (siem && siem.status === "planned") {
    actions.push({
      id: "connect-siem",
      label: "Connecter SIEM / SOAR",
      description: "Préparer l'intégration des remontées sécurité et playbooks.",
      openUrl: `/parametres/connecteurs/wazuh?project=${projectId}`,
      priority: "medium",
    });
  }

  const deliverables = byId.get("deliverables");
  if (deliverables && deliverables.percent < 50) {
    actions.push({
      id: "generate-deliverables",
      label: "Générer des livrables",
      description: "Produire les documents de gouvernance et d'architecture.",
      openUrl: `/livrables?project=${projectId}`,
      priority: "low",
    });
  }

  return actions;
}

export function buildExecutiveSummary(params: {
  project: Project;
  organizationName: string;
  ownerName: string;
  kpis: DashboardKpis;
  modules: ModuleProgressItem[];
}): string {
  const { project, organizationName, ownerName, kpis, modules } = params;
  const referentials = (project.referentials ?? []).join(", ") || "aucun référentiel renseigné";
  const activeLabels = modules
    .filter((mod) => mod.status === "in_progress" || mod.status === "completed")
    .map((mod) => mod.label)
    .join(", ");

  const lines = [
    `Le projet « ${project.name} »${project.code ? ` (${project.code})` : ""} est porté par ${ownerName} au sein de ${organizationName}.`,
    `Statut ${project.status}, priorité ${project.priority ?? "medium"} — maturité estimée : ${kpis.maturityLevel} (${kpis.globalProgress} % de progression globale).`,
    `Référentiels ciblés : ${referentials}. L'équipe compte ${kpis.memberCount} membre(s) ; ${kpis.activityCount} action(s) tracée(s) dans le journal projet.`,
    kpis.riskCount > 0
      ? `${kpis.riskCount} risque(s) identifié(s) dans la GRC ; ${kpis.deliverableCount} livrable(s) généré(s).`
      : `La GRC reste à alimenter ; ${kpis.deliverableCount} livrable(s) disponible(s).`,
    activeLabels
      ? `Modules actifs ou avancés : ${activeLabels}.`
      : "Aucun module n'a encore été activé — démarrer par l'urbanisme SI et EBIOS RM.",
  ];

  return lines.join(" ");
}
