import { describe, expect, it } from "vitest";
import {
  deliverableHasTable,
  deliverableTableColumns,
  deliverableTableRows,
  executiveSummaryKpis,
} from "./deliverablePreview";
import type { EbiosDeliverableResponse } from "./types";

const baseDeliverable: EbiosDeliverableResponse = {
  deliverable_type: "risk_register",
  title: "Registre des risques — Test",
  project_id: "p1",
  project_name: "Test",
  assessment_id: "a1",
  generated_at: "2026-07-09T10:00:00Z",
  overall_progress_percent: 50,
  is_complete: false,
  completeness_warning: "Étude incomplète",
  sections: [{ id: "s1", title: "Synthèse", content: "1 risque", bullets: [] }],
  data: {
    columns: [
      { key: "risk_id", label: "Identifiant" },
      { key: "risk_source", label: "Source" },
    ],
    rows: [{ risk_id: "R-1", risk_source: "Cybercriminel" }],
    total: 1,
  },
};

describe("deliverablePreview helpers", () => {
  it("extracts table columns and rows", () => {
    expect(deliverableTableColumns(baseDeliverable)).toHaveLength(2);
    expect(deliverableTableRows(baseDeliverable)[0].risk_source).toBe("Cybercriminel");
    expect(deliverableHasTable(baseDeliverable)).toBe(true);
  });

  it("returns false for narrative-only deliverables", () => {
    const report: EbiosDeliverableResponse = {
      ...baseDeliverable,
      deliverable_type: "ebios_report",
      data: { workshops: [] },
    };
    expect(deliverableHasTable(report)).toBe(false);
  });

  it("extracts COMEX KPIs", () => {
    const comex: EbiosDeliverableResponse = {
      ...baseDeliverable,
      deliverable_type: "executive_summary",
      data: {
        kpis: {
          overall_progress_percent: 100,
          risks_total: 3,
          treatment_actions_total: 5,
        },
      },
    };
    const kpis = executiveSummaryKpis(comex);
    expect(kpis?.overall_progress_percent).toBe(100);
    expect(kpis?.risks_total).toBe(3);
  });
});

describe("DELIVERABLE_BUTTONS", () => {
  it("covers all four EBIOS deliverable kinds", async () => {
    const { DELIVERABLE_BUTTONS } = await import("./types");
    const kinds = DELIVERABLE_BUTTONS.map((b) => b.kind);
    expect(kinds).toEqual([
      "report",
      "risk-register",
      "treatment-plan",
      "executive-summary",
    ]);
  });
});
