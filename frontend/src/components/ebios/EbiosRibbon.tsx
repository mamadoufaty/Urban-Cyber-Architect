import type { Cartography, Project } from "../../api";

type Props = {
  projects: Project[];
  selectedProjectId: string;
  onProjectChange: (id: string) => void;
  cartographies: Cartography[];
  selectedCartographyId: string | null;
  onCartographyChange: (id: string) => void;
  assessmentTitle: string;
  overallProgress: number;
};

export default function EbiosRibbon({
  projects,
  selectedProjectId,
  onProjectChange,
  cartographies,
  selectedCartographyId,
  onCartographyChange,
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
        <label className="eb-ribbon-project">
          <span>Cartographie</span>
          <select
            className="eb-select"
            value={selectedCartographyId ?? ""}
            onChange={(e) => onCartographyChange(e.target.value)}
            disabled={!cartographies.length}
          >
            {cartographies.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
                {c.is_archived ? " (archivée)" : ""}
              </option>
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
