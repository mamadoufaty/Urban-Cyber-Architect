import { describe, expect, it } from "vitest";
import {
  PROJECT_ROLES,
  REFERENTIAL_OPTIONS,
  activityActionLabel,
  projectRoleLabel,
  projectStatusLabel,
} from "./constants";
import {
  formatDateOnly,
  parseTagsInput,
  tagsToInput,
  toDateInputValue,
  validateProjectDateRange,
} from "./format";

describe("project constants", () => {
  it("includes backend project roles", () => {
    const values = PROJECT_ROLES.map((r) => r.value);
    expect(values).toContain("chef_projet");
    expect(values).toContain("rssi");
    expect(values).toHaveLength(17);
  });

  it("labels known status and actions", () => {
    expect(projectStatusLabel("draft")).toBe("Brouillon");
    expect(projectRoleLabel("chef_projet")).toBe("Chef de projet");
    expect(activityActionLabel("project.created")).toBe("Projet créé");
  });

  it("includes EBIOS RM and ISO 27005 referentials", () => {
    expect(REFERENTIAL_OPTIONS).toContain("EBIOS RM");
    expect(REFERENTIAL_OPTIONS).toContain("ISO 27005");
  });
});

describe("project format helpers", () => {
  it("parses and serializes tags", () => {
    expect(parseTagsInput("cyber, urbanisme , ")).toEqual(["cyber", "urbanisme"]);
    expect(tagsToInput(["a", "b"])).toBe("a, b");
  });

  it("formats ISO dates as DD/MM/YYYY", () => {
    expect(formatDateOnly("2025-06-15")).toBe("15/06/2025");
    expect(formatDateOnly("2025-06-15T00:00:00")).toBe("15/06/2025");
  });

  it("normalizes date input values to YYYY-MM-DD", () => {
    expect(toDateInputValue("2025-03-10")).toBe("2025-03-10");
    expect(toDateInputValue("2025-03-10T12:00:00Z")).toBe("2025-03-10");
    expect(toDateInputValue(null)).toBe("");
  });

  it("rejects end date before start date", () => {
    expect(validateProjectDateRange("2025-06-01", "2025-05-31")).toMatch(/date de fin/i);
    expect(validateProjectDateRange("2025-06-01", "2025-06-01")).toBeNull();
    expect(validateProjectDateRange("2025-06-01", "2025-07-01")).toBeNull();
    expect(validateProjectDateRange("", "2025-07-01")).toBeNull();
  });
});
