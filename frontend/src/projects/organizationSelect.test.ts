import { describe, expect, it } from "vitest";
import type { AdminOrganization } from "../api";
import {
  activeOrganizations,
  filterOrganizations,
  organizationLabelById,
  sortOrganizations,
  upsertOrganization,
} from "./organizationSelect";

function org(partial: Partial<AdminOrganization> & { id: string; name: string }): AdminOrganization {
  return {
    code: partial.code ?? partial.id,
    description: null,
    status: "active",
    created_at: "2025-01-01T00:00:00",
    updated_at: "2025-01-01T00:00:00",
    ...partial,
  };
}

const ORGS: AdminOrganization[] = [
  org({ id: "1", name: "Métropolis Test", code: "metropolis-test" }),
  org({ id: "2", name: "Agence Nationale", code: "ana" }),
  org({ id: "3", name: "Ville de Lyon", code: "lyon", status: "archived" }),
  org({ id: "4", name: "Éolienne SA", code: "eol" }),
];

describe("organizationSelect helpers", () => {
  it("sorts organizations alphabetically (FR, accent-insensitive)", () => {
    const names = sortOrganizations(ORGS).map((o) => o.name);
    expect(names).toEqual([
      "Agence Nationale",
      "Éolienne SA",
      "Métropolis Test",
      "Ville de Lyon",
    ]);
  });

  it("returns only active organizations (dynamic loading), sorted", () => {
    const names = activeOrganizations(ORGS).map((o) => o.name);
    expect(names).toEqual(["Agence Nationale", "Éolienne SA", "Métropolis Test"]);
    expect(names).not.toContain("Ville de Lyon");
  });

  it("filters by name or code, case and accent insensitive (search)", () => {
    expect(filterOrganizations(ORGS, "metropolis").map((o) => o.id)).toEqual(["1"]);
    expect(filterOrganizations(ORGS, "METRO").map((o) => o.id)).toEqual(["1"]);
    expect(filterOrganizations(ORGS, "eolienne").map((o) => o.id)).toEqual(["4"]);
    expect(filterOrganizations(ORGS, "ana").map((o) => o.id)).toEqual(["2"]); // via le code
    expect(filterOrganizations(ORGS, "").map((o) => o.id)).toHaveLength(4);
    expect(filterOrganizations(ORGS, "introuvable")).toHaveLength(0);
  });

  it("upserts a created organization so it appears immediately, sorted", () => {
    const created = org({ id: "9", name: "Aération SARL", code: "aera" });
    const next = upsertOrganization(ORGS, created);
    expect(next.map((o) => o.name)[0]).toBe("Aération SARL");
    expect(next).toHaveLength(5);

    // Un upsert du même id remplace au lieu de dupliquer.
    const renamed = org({ id: "9", name: "Zephyr", code: "aera" });
    const replaced = upsertOrganization(next, renamed);
    expect(replaced).toHaveLength(5);
    expect(replaced.find((o) => o.id === "9")?.name).toBe("Zephyr");
  });

  it("resolves an organization label by id", () => {
    expect(organizationLabelById(ORGS, "2")).toBe("Agence Nationale");
    expect(organizationLabelById(ORGS, "")).toBe("");
    expect(organizationLabelById(ORGS, "does-not-exist")).toBe("");
  });
});
