import { describe, expect, it } from "vitest";
import type { Cartography, CartographyVersion } from "../../api";
import {
  cartographyStatusLabel,
  formatVersionLabel,
  isCartographyEditable,
  isHistoricalVersionSelected,
  resolveDefaultCartographyId,
  resolveDefaultVersionId,
  sortCartographies,
  validateCartographyCreateInput,
  validateDuplicateName,
} from "./cartographySelect";

function makeCartography(overrides: Partial<Cartography>): Cartography {
  return {
    id: "c1",
    project_id: "p1",
    name: "Cartographie",
    description: null,
    type: "libre",
    status: "draft",
    version: "1.0",
    author: null,
    is_active: false,
    is_archived: false,
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
    validated_at: null,
    validated_by: null,
    ...overrides,
  };
}

function makeVersion(overrides: Partial<CartographyVersion>): CartographyVersion {
  return {
    id: "v1",
    cartography_id: "c1",
    version: "1.0",
    status: "draft",
    is_current: true,
    author: null,
    comment: null,
    created_at: "2026-01-01T00:00:00Z",
    validated_at: null,
    validated_by: null,
    ...overrides,
  };
}

describe("cartographyStatusLabel", () => {
  it("translates known statuses to French labels", () => {
    expect(cartographyStatusLabel("draft")).toBe("Brouillon");
    expect(cartographyStatusLabel("in_validation")).toBe("En validation");
    expect(cartographyStatusLabel("validated")).toBe("Validée");
    expect(cartographyStatusLabel("archived")).toBe("Archivée");
  });

  it("falls back to the raw value for unknown statuses", () => {
    expect(cartographyStatusLabel("mystery")).toBe("mystery");
  });
});

describe("sortCartographies", () => {
  it("sorts alphabetically and relegates archived cartographies to the end", () => {
    const list = [
      makeCartography({ id: "1", name: "Zulu" }),
      makeCartography({ id: "2", name: "Alpha", is_archived: true }),
      makeCartography({ id: "3", name: "Bravo" }),
    ];
    const sorted = sortCartographies(list);
    expect(sorted.map((c) => c.id)).toEqual(["3", "1", "2"]);
  });
});

describe("resolveDefaultCartographyId", () => {
  it("returns null when the list is empty", () => {
    expect(resolveDefaultCartographyId([], "x")).toBeNull();
  });

  it("keeps the previous selection when it still exists", () => {
    const list = [makeCartography({ id: "1" }), makeCartography({ id: "2" })];
    expect(resolveDefaultCartographyId(list, "2")).toBe("2");
  });

  it("falls back to the active cartography when the previous selection is gone", () => {
    const list = [
      makeCartography({ id: "1" }),
      makeCartography({ id: "2", is_active: true }),
    ];
    expect(resolveDefaultCartographyId(list, "deleted")).toBe("2");
  });

  it("falls back to the first non-archived cartography when none is active", () => {
    const list = [
      makeCartography({ id: "1", is_archived: true }),
      makeCartography({ id: "2" }),
    ];
    expect(resolveDefaultCartographyId(list, null)).toBe("2");
  });
});

describe("resolveDefaultVersionId", () => {
  it("returns null when there are no versions", () => {
    expect(resolveDefaultVersionId([], "x")).toBeNull();
  });

  it("keeps the previous version when still present", () => {
    const versions = [makeVersion({ id: "a", is_current: false }), makeVersion({ id: "b", is_current: true })];
    expect(resolveDefaultVersionId(versions, "a")).toBe("a");
  });

  it("defaults to the current version otherwise", () => {
    const versions = [makeVersion({ id: "a", is_current: false }), makeVersion({ id: "b", is_current: true })];
    expect(resolveDefaultVersionId(versions, null)).toBe("b");
    expect(resolveDefaultVersionId(versions, "missing")).toBe("b");
  });
});

describe("formatVersionLabel", () => {
  it("prefixes the version number with v", () => {
    expect(formatVersionLabel({ version: "1.2" })).toBe("v1.2");
  });
});

describe("isHistoricalVersionSelected", () => {
  const versions = [makeVersion({ id: "a", is_current: false }), makeVersion({ id: "b", is_current: true })];

  it("is false when nothing is selected or the current version is selected", () => {
    expect(isHistoricalVersionSelected(versions, null)).toBe(false);
    expect(isHistoricalVersionSelected(versions, "b")).toBe(false);
  });

  it("is true when a non-current version is selected", () => {
    expect(isHistoricalVersionSelected(versions, "a")).toBe(true);
  });
});

describe("isCartographyEditable", () => {
  it("is false for archived cartographies or when null", () => {
    expect(isCartographyEditable(null)).toBe(false);
    expect(isCartographyEditable(makeCartography({ is_archived: true }))).toBe(false);
  });

  it("is true for non-archived cartographies regardless of status", () => {
    expect(isCartographyEditable(makeCartography({ status: "validated", is_archived: false }))).toBe(true);
  });
});

describe("validateCartographyCreateInput", () => {
  it("requires a name and a type", () => {
    expect(validateCartographyCreateInput({ name: "", type: "libre" })).toMatch(/nom/i);
    expect(validateCartographyCreateInput({ name: "Test", type: "" })).toMatch(/type/i);
  });

  it("rejects overly long names", () => {
    expect(validateCartographyCreateInput({ name: "a".repeat(256), type: "libre" })).toMatch(/trop long/i);
  });

  it("accepts a valid input", () => {
    expect(validateCartographyCreateInput({ name: "Urbanisme Technique", type: "urbanisme_technique" })).toBeNull();
  });
});

describe("validateDuplicateName", () => {
  it("requires a non-empty name", () => {
    expect(validateDuplicateName("   ", [])).toMatch(/obligatoire/i);
  });

  it("rejects a name already used in the project (case-insensitive)", () => {
    expect(validateDuplicateName("urbanisme technique", ["Urbanisme Technique"])).toMatch(/déjà/i);
  });

  it("accepts a unique name", () => {
    expect(validateDuplicateName("Architecture 2028", ["Urbanisme Technique"])).toBeNull();
  });
});
