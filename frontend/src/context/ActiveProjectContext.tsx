import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import {
  clearStoredActiveProject,
  getStoredActiveProject,
  setStoredActiveProject,
  type ActiveProjectSummary,
} from "../projects/activeProject";

type ActiveProjectContextValue = {
  activeProject: ActiveProjectSummary | null;
  setActiveProject: (project: ActiveProjectSummary) => void;
  clearActiveProject: () => void;
};

const ActiveProjectContext = createContext<ActiveProjectContextValue | null>(null);

export function ActiveProjectProvider({ children }: { children: ReactNode }) {
  const [activeProject, setActiveProjectState] = useState<ActiveProjectSummary | null>(() =>
    getStoredActiveProject(),
  );

  const setActiveProject = useCallback((project: ActiveProjectSummary) => {
    setStoredActiveProject(project);
    setActiveProjectState(project);
  }, []);

  const clearActiveProject = useCallback(() => {
    clearStoredActiveProject();
    setActiveProjectState(null);
  }, []);

  const value = useMemo(
    () => ({ activeProject, setActiveProject, clearActiveProject }),
    [activeProject, setActiveProject, clearActiveProject],
  );

  return (
    <ActiveProjectContext.Provider value={value}>{children}</ActiveProjectContext.Provider>
  );
}

export function useActiveProject(): ActiveProjectContextValue {
  const ctx = useContext(ActiveProjectContext);
  if (!ctx) {
    throw new Error("useActiveProject must be used within ActiveProjectProvider");
  }
  return ctx;
}
