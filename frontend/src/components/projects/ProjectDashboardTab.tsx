import { useCallback, useEffect, useState } from "react";
import type { Project } from "../../api";
import { fetchProjectDashboardSnapshot } from "../../projects/fetchProjectDashboard";
import type { ProjectDashboardSnapshot } from "../../projects/fetchProjectDashboard";
import ProjectExecutiveSummary from "./ProjectExecutiveSummary";
import ProjectKpiCards from "./ProjectKpiCards";
import ProjectModuleProgress from "./ProjectModuleProgress";
import ProjectNextActions from "./ProjectNextActions";
import ProjectOverviewCard from "./ProjectOverviewCard";
import ProjectTimeline from "./ProjectTimeline";

type Props = {
  project: Project;
  organizationName: string;
  ownerName: string;
};

export default function ProjectDashboardTab({
  project,
  organizationName,
  ownerName,
}: Props) {
  const [snapshot, setSnapshot] = useState<ProjectDashboardSnapshot | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchProjectDashboardSnapshot(project, organizationName, ownerName);
      setSnapshot(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Impossible de charger le dashboard");
    } finally {
      setLoading(false);
    }
  }, [project, organizationName, ownerName]);

  useEffect(() => {
    load();
  }, [load]);

  if (loading) {
    return <div className="card">Chargement de la vue 360°…</div>;
  }

  if (error || !snapshot) {
    return (
      <div className="card project-error">
        <p>{error ?? "Dashboard indisponible"}</p>
        <button type="button" className="btn btn-secondary" onClick={() => load()}>
          Réessayer
        </button>
      </div>
    );
  }

  return (
    <div className="project-tab-panel project-dashboard-360">
      <ProjectOverviewCard
        project={project}
        organizationName={organizationName}
        ownerName={ownerName}
      />
      <ProjectKpiCards kpis={snapshot.kpis} />
      <div className="project-dashboard-columns">
        <ProjectModuleProgress modules={snapshot.modules} />
        <div className="project-dashboard-side">
          <ProjectTimeline items={snapshot.timeline} />
          <ProjectNextActions actions={snapshot.nextActions} />
        </div>
      </div>
      <ProjectExecutiveSummary summary={snapshot.executiveSummary} />
    </div>
  );
}
