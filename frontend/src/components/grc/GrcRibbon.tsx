import type { Project } from "../../api";

type Props = {
  projects: Project[];
  selectedProjectId: string;
  onProjectChange: (id: string) => void;
  moduleLabel?: string;
};

export default function GrcRibbon({
  projects,
  selectedProjectId,
  onProjectChange,
  moduleLabel = "GRC — Cybersécurité",
}: Props) {
  return (
    <div className="grc-ribbon">
      <div className="grc-ribbon-row">
        <label className="grc-ribbon-project">
          <span>Projet</span>
          <select
            className="grc-ribbon-select"
            value={selectedProjectId}
            onChange={(e) => onProjectChange(e.target.value)}
          >
            {projects.length === 0 && <option value="">Aucun projet</option>}
            {projects.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
        </label>
        <span className="grc-ribbon-badge">{moduleLabel}</span>
      </div>
    </div>
  );
}
