import type { Project } from "../../api";

type Props = {
  projects: Project[];
  selectedProjectId: string;
  onProjectChange: (id: string) => void;
  assessmentTitle: string;
  overallProgress: number;
};

export default function EbiosRibbon({
  projects,
  selectedProjectId,
  onProjectChange,
  assessmentTitle,
  overallProgress,
}: Props) {
  return (
    <div className="eb-ribbon">
      <div className="eb-ribbon-row">
        <label className="eb-ribbon-project">
          <span>Projet</span>
          <select
            className="eb-select"
            value={selectedProjectId}
            onChange={(e) => onProjectChange(e.target.value)}
          >
            {projects.map((p) => (
              <option key={p.id} value={p.id}>{p.name}</option>
            ))}
          </select>
        </label>
        <div className="eb-ribbon-meta">
          <span className="eb-ribbon-title">{assessmentTitle}</span>
          <span className="eb-ribbon-progress">{overallProgress}%</span>
        </div>
        <span className="eb-ribbon-badge">EBIOS RM Beta</span>
      </div>
    </div>
  );
}
