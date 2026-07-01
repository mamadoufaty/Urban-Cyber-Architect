export const ACTIVE_PROJECT_STORAGE_KEY = "uca.active.project";

export type ActiveProjectSummary = {
  id: string;
  name: string;
  code?: string | null;
};

export function getStoredActiveProject(): ActiveProjectSummary | null {
  try {
    const raw = localStorage.getItem(ACTIVE_PROJECT_STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as ActiveProjectSummary;
    if (!parsed?.id || !parsed?.name) {
      localStorage.removeItem(ACTIVE_PROJECT_STORAGE_KEY);
      return null;
    }
    return parsed;
  } catch {
    localStorage.removeItem(ACTIVE_PROJECT_STORAGE_KEY);
    return null;
  }
}

export function setStoredActiveProject(project: ActiveProjectSummary): void {
  localStorage.setItem(ACTIVE_PROJECT_STORAGE_KEY, JSON.stringify(project));
}

export function clearStoredActiveProject(): void {
  localStorage.removeItem(ACTIVE_PROJECT_STORAGE_KEY);
}
