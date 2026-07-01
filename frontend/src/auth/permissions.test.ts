import { describe, expect, it } from "vitest";
import {
  canAccessPath,
  hasPermission,
  ROLE_PERMISSIONS,
} from "../auth/permissions";

describe("ROLE_PERMISSIONS", () => {
  it("admin has all modules", () => {
    expect(ROLE_PERMISSIONS.admin).toHaveLength(8);
    expect(hasPermission("admin", "grc")).toBe(true);
    expect(hasPermission("admin", "urbanism")).toBe(true);
    expect(hasPermission("admin", "administration")).toBe(true);
  });

  it("soc cannot access grc or urbanism modules", () => {
    expect(hasPermission("soc", "soc")).toBe(true);
    expect(hasPermission("soc", "settings")).toBe(true);
    expect(hasPermission("soc", "grc")).toBe(false);
    expect(hasPermission("soc", "urbanism")).toBe(false);
    expect(hasPermission("soc", "ai")).toBe(false);
  });

  it("metier only accesses dashboard and urbanism", () => {
    expect(hasPermission("metier", "dashboard")).toBe(true);
    expect(hasPermission("metier", "urbanism")).toBe(true);
    expect(hasPermission("metier", "projects")).toBe(false);
    expect(hasPermission("metier", "soc")).toBe(false);
  });

  it("consultant accesses urbanism and grc but not soc or settings", () => {
    expect(hasPermission("consultant", "urbanism")).toBe(true);
    expect(hasPermission("consultant", "grc")).toBe(true);
    expect(hasPermission("consultant", "soc")).toBe(false);
    expect(hasPermission("consultant", "settings")).toBe(false);
  });

  it("rssi accesses grc, soc and urbanism", () => {
    expect(hasPermission("rssi", "grc")).toBe(true);
    expect(hasPermission("rssi", "soc")).toBe(true);
    expect(hasPermission("rssi", "urbanism")).toBe(true);
    expect(hasPermission("rssi", "administration")).toBe(false);
  });
});

describe("canAccessPath", () => {
  it("blocks soc role from direct URL access to grc and urbanism routes", () => {
    expect(canAccessPath("soc", "/ebios")).toBe(false);
    expect(canAccessPath("soc", "/schema-urbanisme")).toBe(false);
    expect(canAccessPath("soc", "/registre-risques")).toBe(false);
    expect(canAccessPath("soc", "/dashboard-rssi")).toBe(false);
    expect(canAccessPath("soc", "/soc/wazuh")).toBe(true);
  });

  it("allows admin on all mapped paths", () => {
    expect(canAccessPath("admin", "/ebios")).toBe(true);
    expect(canAccessPath("admin", "/soc/correlations")).toBe(true);
    expect(canAccessPath("admin", "/schema-urbanisme")).toBe(true);
    expect(canAccessPath("admin", "/administration/users")).toBe(true);
  });

  it("blocks non-admin from administration", () => {
    expect(canAccessPath("rssi", "/administration/users")).toBe(false);
    expect(canAccessPath("soc", "/administration/users")).toBe(false);
    expect(canAccessPath("rssi", "/administration/organizations")).toBe(false);
  });

  it("allows admin on administration organizations path", () => {
    expect(canAccessPath("admin", "/administration/organizations")).toBe(true);
  });
});
