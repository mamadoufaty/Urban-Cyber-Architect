import type { Project } from "../api";
import {
  getDeliverables,
  getEbiosAssessment,
  getEbiosOverview,
  getRiskRegister,
  getSocCorrelations,
  getUrbanismProgress,
  listProjectActivity,
  listProjectMembers,
  type ProjectActivity,
} from "../api";
import {
  aiProgressFromSignals,
  appendFutureTimelineItems,
  buildExecutiveSummary,
  buildNextActions,
  computeGlobalProgress,
  computeMaturityLevel,
  countActiveModules,
  deliverablesProgress,
  deriveModuleStatus,
  findLastActivityDate,
  grcProgressFromRiskCount,
  mapActivitiesToTimeline,
  socProgressFromIncidents,
  type DashboardKpis,
  type ModuleProgressItem,
  type NextActionItem,
  type TimelineItem,
} from "./dashboardMetrics";

export type ProjectDashboardSnapshot = {
  kpis: DashboardKpis;
  modules: ModuleProgressItem[];
  timeline: TimelineItem[];
  nextActions: NextActionItem[];
  executiveSummary: string;
};

export async function fetchProjectDashboardSnapshot(
  project: Project,
  organizationName: string,
  ownerName: string,
): Promise<ProjectDashboardSnapshot> {
  const projectId = project.id;

  const [members, activities, urbanismProgress, deliverablesRes, riskRegister, ebiosAssessment, socRes] =
    await Promise.all([
      listProjectMembers(projectId).catch(() => []),
      listProjectActivity(projectId).catch(() => [] as ProjectActivity[]),
      getUrbanismProgress(projectId).catch(() => null),
      getDeliverables(projectId).catch(() => ({ deliverables: [], total: 0 })),
      getRiskRegister(projectId, { page: 1, page_size: 1 }).catch(() => null),
      getEbiosAssessment(projectId).catch(() => null),
      getSocCorrelations(projectId, { limit: 1 }).catch(() => null),
    ]);

  let ebiosPercent = 0;
  if (ebiosAssessment?.id) {
    try {
      const overview = await getEbiosOverview(projectId, ebiosAssessment.id);
      ebiosPercent = overview.overall_progress_percent ?? 0;
    } catch {
      ebiosPercent = 0;
    }
  }

  const urbanismPercent = urbanismProgress?.overall_percent ?? 0;
  const riskCount = riskRegister?.metadata?.total_risks ?? riskRegister?.total ?? 0;
  const deliverableCount = deliverablesRes.total ?? deliverablesRes.deliverables.length;
  const socTotal = socRes?.total ?? 0;
  const socUrbanism = socRes?.metadata?.urbanism_entities ?? 0;

  const modules: ModuleProgressItem[] = [
    {
      id: "urbanism",
      label: "Urbanisme SI",
      percent: urbanismPercent,
      status: deriveModuleStatus(urbanismPercent),
      lastActivity:
        findLastActivityDate(activities, (a) => a.includes("urban") || a === "project.updated") ??
        project.updated_at ??
        null,
      openUrl: `/schema-urbanisme?project=${projectId}`,
    },
    {
      id: "ebios",
      label: "EBIOS RM",
      percent: ebiosPercent,
      status: deriveModuleStatus(ebiosPercent),
      lastActivity: ebiosAssessment?.updated_at ?? null,
      openUrl: `/ebios?project=${projectId}`,
    },
    {
      id: "grc",
      label: "GRC",
      percent: grcProgressFromRiskCount(riskCount),
      status: deriveModuleStatus(grcProgressFromRiskCount(riskCount)),
      lastActivity: riskRegister?.metadata?.generated_at ?? null,
      openUrl: `/registre-risques?project=${projectId}`,
    },
    {
      id: "soc",
      label: "SOC",
      percent: socProgressFromIncidents(socTotal, socUrbanism),
      status: deriveModuleStatus(socProgressFromIncidents(socTotal, socUrbanism)),
      lastActivity: socRes?.incidents?.[0]?.alert?.timestamp ?? null,
      openUrl: `/soc/correlations?project=${projectId}`,
    },
    {
      id: "siem",
      label: "SIEM / SOAR",
      percent: 0,
      status: "planned",
      lastActivity: null,
      openUrl: `/parametres/connecteurs/wazuh?project=${projectId}`,
    },
    {
      id: "ai",
      label: "IA",
      percent: aiProgressFromSignals(project.objectives?.length ?? 0, 0),
      status: deriveModuleStatus(aiProgressFromSignals(project.objectives?.length ?? 0, 0)),
      lastActivity: findLastActivityDate(activities, (a) => a.includes("project")) ?? null,
      openUrl: `/ai-governance?project=${projectId}`,
    },
    {
      id: "deliverables",
      label: "Livrables",
      percent: deliverablesProgress(deliverableCount),
      status: deriveModuleStatus(deliverablesProgress(deliverableCount)),
      lastActivity: deliverablesRes.deliverables[0]?.updated_at ?? null,
      openUrl: `/livrables?project=${projectId}`,
    },
  ];

  const globalProgress = computeGlobalProgress(modules);
  const kpis: DashboardKpis = {
    globalProgress,
    memberCount: members.length,
    activityCount: activities.length,
    activeModulesCount: countActiveModules(modules),
    deliverableCount,
    riskCount,
    maturityLevel: computeMaturityLevel(globalProgress),
  };

  const timeline = appendFutureTimelineItems(mapActivitiesToTimeline(activities));
  const nextActions = buildNextActions(projectId, modules);
  const executiveSummary = buildExecutiveSummary({
    project,
    organizationName,
    ownerName,
    kpis,
    modules,
  });

  return { kpis, modules, timeline, nextActions, executiveSummary };
}
