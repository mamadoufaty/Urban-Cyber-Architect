import { describe, expect, it } from "vitest";
import { buildUrbanismImportUrl } from "./api";

const EBios_DELIVERABLE_PATHS = {
  report: "report",
  "risk-register": "risk-register",
  "treatment-plan": "treatment-plan",
  "executive-summary": "executive-summary",
} as const;

function buildEbiosDeliverableUrl(
  projectId: string,
  assessmentId: string,
  kind: keyof typeof EBios_DELIVERABLE_PATHS
) {
  return `/api/projects/${projectId}/ebios/assessments/${assessmentId}/deliverables/${EBios_DELIVERABLE_PATHS[kind]}`;
}

describe("buildUrbanismImportUrl", () => {
  const projectId = "11111111-1111-1111-1111-111111111111";

  it("builds the preview URL without duplicating the endpoint", () => {
    expect(buildUrbanismImportUrl(projectId, "preview")).toBe(
      `/api/projects/${projectId}/urbanism/import/preview`
    );
  });

  it("builds the final import URL without appending '/import' twice", () => {
    const url = buildUrbanismImportUrl(projectId, "import");
    expect(url).toBe(`/api/projects/${projectId}/urbanism/import`);
    expect(url).not.toContain("/import/import");
  });

  it("appends cartography_id as a query param only for the import endpoint", () => {
    const cartographyId = "22222222-2222-2222-2222-222222222222";

    const importUrl = buildUrbanismImportUrl(projectId, "import", cartographyId);
    expect(importUrl).toBe(
      `/api/projects/${projectId}/urbanism/import?cartography_id=${cartographyId}`
    );

    const previewUrl = buildUrbanismImportUrl(projectId, "preview", cartographyId);
    expect(previewUrl).toBe(`/api/projects/${projectId}/urbanism/import/preview`);
    expect(previewUrl).not.toContain("cartography_id");
  });

  it("omits the query string entirely when no cartography is selected", () => {
    const url = buildUrbanismImportUrl(projectId, "import");
    expect(url).not.toContain("?");
  });
});

describe("buildEbiosDeliverableUrl", () => {
  const projectId = "11111111-1111-1111-1111-111111111111";
  const assessmentId = "22222222-2222-2222-2222-222222222222";

  it("builds URLs for all four EBIOS deliverable endpoints", () => {
    expect(buildEbiosDeliverableUrl(projectId, assessmentId, "report")).toBe(
      `/api/projects/${projectId}/ebios/assessments/${assessmentId}/deliverables/report`
    );
    expect(buildEbiosDeliverableUrl(projectId, assessmentId, "risk-register")).toContain(
      "/deliverables/risk-register"
    );
    expect(buildEbiosDeliverableUrl(projectId, assessmentId, "treatment-plan")).toContain(
      "/deliverables/treatment-plan"
    );
    expect(buildEbiosDeliverableUrl(projectId, assessmentId, "executive-summary")).toContain(
      "/deliverables/executive-summary"
    );
  });
});
