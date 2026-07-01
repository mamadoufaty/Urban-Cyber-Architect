import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  ACTIVE_PROJECT_STORAGE_KEY,
  clearStoredActiveProject,
  getStoredActiveProject,
  setStoredActiveProject,
} from "./activeProject";

function createStorage(): Storage {
  const store = new Map<string, string>();
  return {
    get length() {
      return store.size;
    },
    clear() {
      store.clear();
    },
    getItem(key: string) {
      return store.get(key) ?? null;
    },
    key(index: number) {
      return [...store.keys()][index] ?? null;
    },
    removeItem(key: string) {
      store.delete(key);
    },
    setItem(key: string, value: string) {
      store.set(key, value);
    },
  };
}

describe("activeProject storage", () => {
  beforeEach(() => {
    vi.stubGlobal("localStorage", createStorage());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("stores and retrieves active project", () => {
    setStoredActiveProject({ id: "abc", name: "Projet Test", code: "projet-test" });
    expect(getStoredActiveProject()).toEqual({
      id: "abc",
      name: "Projet Test",
      code: "projet-test",
    });
  });

  it("clears invalid stored data", () => {
    localStorage.setItem(ACTIVE_PROJECT_STORAGE_KEY, "{invalid");
    expect(getStoredActiveProject()).toBeNull();
    expect(localStorage.getItem(ACTIVE_PROJECT_STORAGE_KEY)).toBeNull();
  });

  it("clearStoredActiveProject removes entry", () => {
    setStoredActiveProject({ id: "1", name: "X" });
    clearStoredActiveProject();
    expect(getStoredActiveProject()).toBeNull();
  });
});
