import { describe, expect, it } from "vitest";
import type { Referential } from "../api";
import {
  isDuplicateReferentialCode,
  sortReferentials,
  upsertReferential,
  validateQuickAddReferential,
  withReferentialPreselected,
} from "./referentialSelect";

function ref(partial: Partial<Referential> & { id: string; label: string; code: string }): Referential {
  return {
    category: null,
    description: null,
    status: "active",
    sort_order: 0,
    created_at: "2025-01-01T00:00:00",
    updated_at: "2025-01-01T00:00:00",
    ...partial,
  };
}

const REFS: Referential[] = [
  ref({ id: "1", label: "RGPD", code: "rgpd", sort_order: 0 }),
  ref({ id: "2", label: "NIS2", code: "nis2", sort_order: 1 }),
  ref({ id: "3", label: "ISO 27001", code: "iso-27001", sort_order: 3 }),
];

describe("referentialSelect helpers", () => {
  it("sorts by sort_order then label", () => {
    const shuffled = [REFS[2], REFS[0], REFS[1]];
    expect(sortReferentials(shuffled).map((r) => r.code)).toEqual(["rgpd", "nis2", "iso-27001"]);
  });

  it("upserts a created referential so it appears immediately, sorted", () => {
    const created = ref({ id: "9", label: "DORA", code: "dora", sort_order: 2 });
    const next = upsertReferential(REFS, created);
    expect(next).toHaveLength(4);
    expect(next.map((r) => r.code)).toEqual(["rgpd", "nis2", "dora", "iso-27001"]);

    // Un upsert du même id remplace au lieu de dupliquer.
    const renamed = ref({ id: "9", label: "DORA (v2)", code: "dora", sort_order: 2 });
    const replaced = upsertReferential(next, renamed);
    expect(replaced).toHaveLength(4);
    expect(replaced.find((r) => r.id === "9")?.label).toBe("DORA (v2)");
  });

  it("detects duplicate codes case-insensitively", () => {
    expect(isDuplicateReferentialCode(REFS, "RGPD")).toBe(true);
    expect(isDuplicateReferentialCode(REFS, "rgpd")).toBe(true);
    expect(isDuplicateReferentialCode(REFS, "  Nis2  ")).toBe(true);
    expect(isDuplicateReferentialCode(REFS, "dora")).toBe(false);
    expect(isDuplicateReferentialCode(REFS, "")).toBe(false);
  });

  it("preselects a newly created referential exactly once", () => {
    expect(withReferentialPreselected(["RGPD"], "DORA")).toEqual(["RGPD", "DORA"]);
    expect(withReferentialPreselected(["RGPD", "DORA"], "DORA")).toEqual(["RGPD", "DORA"]);
    expect(withReferentialPreselected([], "DORA")).toEqual(["DORA"]);
  });

  describe("validateQuickAddReferential", () => {
    const base = { label: "DORA", code: "dora", description: "", status: "active" };

    it("requires a name", () => {
      expect(validateQuickAddReferential({ ...base, label: "" }, REFS)).toMatch(/nom/i);
      expect(validateQuickAddReferential({ ...base, label: "   " }, REFS)).toMatch(/nom/i);
    });

    it("requires a code", () => {
      expect(validateQuickAddReferential({ ...base, code: "" }, REFS)).toMatch(/code/i);
      expect(validateQuickAddReferential({ ...base, code: "   " }, REFS)).toMatch(/code/i);
    });

    it("rejects duplicate codes with a clear message", () => {
      const message = validateQuickAddReferential({ ...base, code: "RGPD" }, REFS);
      expect(message).toMatch(/existe déjà/i);
      expect(message).toContain("RGPD");
    });

    it("passes for a valid, non-duplicate submission", () => {
      expect(validateQuickAddReferential(base, REFS)).toBeNull();
    });
  });
});
