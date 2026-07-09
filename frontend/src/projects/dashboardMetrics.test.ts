import { describe, expect, it } from "vitest";
import type { Project } from "../api";
import {
  appendFutureTimelineItems,
  buildExecutiveSummary,
  buildNextActions,
  computeGlobalProgress,
  computeMaturityLevel,
  countUrbanismObjects,
  deriveModuleStatus,
  grcProgressFromRiskCount,
  mapActivitiesToTimeline,
  moduleStatusLabel,
  type ModuleProgressItem,
} from "./dashboardMetrics";

const baseProject: Project = {
  id: "p1",
  name: "Projet Test",
  code: "projet-test",
  description: "Description test",
  client: "Acme",
  organization: { name: "Org", sector: "generic", size: "PME", country: "France" },
  referentials: ["ISO 27001", "EBIOS RM"],
  objectives: ["Sécuriser le SI"],
  urbanism: { club_urba: { organisation: { acteurs: ["RSSI", "DSI"] } } },
  status: "active",
  priority: "high",
  tags: ["cyber"],
};

describe("dashboardMetrics", () => {
  it("counts urbanism objects from club_urba", () => {
    expect(countUrbanismObjects(baseProject)).toBe(2);
  });

  it("derives module status from percent", () => {
    expect(deriveModuleStatus(0)).toBe("not_started");
    expect(deriveModuleStatus(45)).toBe("in_progress");
    expect(deriveModuleStatus(100)).toBe("completed");
    expect(deriveModuleStatus(0, true)).toBe("planned");
    expect(moduleStatusLabel("in_progress")).toBe("En cours");
  });

  it("computes global progress and maturity", () => {
    const modules: ModuleProgressItem[] = [
      {
        id: "urbanism",
        label: "Urbanisme SI",
        percent: 50,
        status: "in_progress",
        lastActivity: null,
        openUrl: "/u",
      },
      {
        id: "ebios",
        label: "EBIOS RM",
        percent: 100,
        status: "completed",
        lastActivity: null,
        openUrl: "/e",
      },
    ];
    expect(computeGlobalProgress(modules)).toBe(75);
    expect(computeMaturityLevel(75)).toBe("En maturation");
  });

  it("maps activities to timeline and appends future items", () => {
    const timeline = mapActivitiesToTimeline([
      {
        id: "a1",
        project_id: "p1",
        user_id: null,
        action: "project.created",
        details: { name: "Projet Test" },
        created_at: "2025-01-01T10:00:00",
      },
    ]);
    const withFuture = appendFutureTimelineItems(timeline);
    expect(timeline[0].label).toBe("Projet créé");
    expect(withFuture.some((item) => item.kind === "future")).toBe(true);
  });

  it("builds next actions from low module progress", () => {
    const modules: ModuleProgressItem[] = [
      {
        id: "urbanism",
        label: "Urbanisme SI",
        percent: 10,
        status: "in_progress",
        lastActivity: null,
        openUrl: "/schema",
      },
      {
        id: "ebios",
        label: "EBIOS RM",
        percent: 0,
        status: "not_started",
        lastActivity: null,
        openUrl: "/ebios",
      },
      {
        id: "grc",
        label: "GRC",
        percent: 0,
        status: "not_started",
        lastActivity: null,
        openUrl: "/grc",
      },
      {
        id: "siem",
        label: "SIEM / SOAR",
        percent: 0,
        status: "planned",
        lastActivity: null,
        openUrl: "/siem",
      },
      {
        id: "deliverables",
        label: "Livrables",
        percent: 0,
        status: "not_started",
        lastActivity: null,
        openUrl: "/liv",
      },
    ];
    const actions = buildNextActions("p1", modules);
    expect(actions.some((a) => a.label.includes("urbanisme"))).toBe(true);
    expect(actions.some((a) => a.label.includes("EBIOS"))).toBe(true);
    expect(actions.some((a) => a.label.includes("SIEM"))).toBe(true);
  });

  it("builds executive summary from project data", () => {
    const modules: ModuleProgressItem[] = [
      {
        id: "urbanism",
        label: "Urbanisme SI",
        percent: 40,
        status: "in_progress",
        lastActivity: null,
        openUrl: "/u",
      },
    ];
    const summary = buildExecutiveSummary({
      project: baseProject,
      organizationName: "Org Test",
      ownerName: "Alice",
      kpis: {
        globalProgress: 40,
        memberCount: 2,
        activityCount: 5,
        activeModulesCount: 1,
        deliverableCount: 0,
        riskCount: 3,
        maturityLevel: "En structuration",
      },
      modules,
    });
    expect(summary).toContain("Projet Test");
    expect(summary).toContain("Alice");
    expect(summary).toContain("3 risque");
  });

  it("computes GRC progress from risk count", () => {
    expect(grcProgressFromRiskCount(0)).toBe(0);
    expect(grcProgressFromRiskCount(5)).toBeGreaterThan(0);
  });
});
