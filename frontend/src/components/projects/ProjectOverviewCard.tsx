import type { Project } from "../../api";
import { projectPriorityLabel, projectStatusLabel } from "../../projects/constants";
import { formatDateOnly } from "../../projects/format";

type Props = {
  project: Project;
  organizationName: string;
  ownerName: string;
};

export default function ProjectOverviewCard({ project, organizationName, ownerName }: Props) {
  return (
    <div className="card project-overview-card">
      <div className="project-overview-header">
        <div>
          <h3 className="project-overview-title">{project.name}</h3>
          {project.code && <span className="project-code-badge">{project.code}</span>}
        </div>
        <div className="project-overview-badges">
          <span className={`status-badge status-${project.status}`}>
            {projectStatusLabel(project.status)}
          </span>
          <span className={`priority-badge priority-${project.priority ?? "medium"}`}>
            {projectPriorityLabel(project.priority ?? "medium")}
          </span>
        </div>
      </div>

      <div className="project-overview-grid">
        <div>
          <span className="project-overview-label">Client</span>
          <strong>{project.client ?? "—"}</strong>
        </div>
        <div>
          <span className="project-overview-label">Organisation</span>
          <strong>{organizationName}</strong>
        </div>
        <div>
          <span className="project-overview-label">Responsable</span>
          <strong>{ownerName}</strong>
        </div>
        <div>
          <span className="project-overview-label">Période</span>
          <strong>
            {formatDateOnly(project.start_date)} → {formatDateOnly(project.end_date)}
          </strong>
        </div>
      </div>

      {project.description && (
        <p className="project-overview-description">{project.description}</p>
      )}

      <div className="project-overview-section">
        <span className="project-overview-label">Référentiels</span>
        {(project.referentials?.length ?? 0) > 0 ? (
          <div className="project-tags">
            {project.referentials!.map((ref) => (
              <span key={ref} className="project-tag project-tag-referential">
                {ref}
              </span>
            ))}
          </div>
        ) : (
          <span className="project-overview-empty">Aucun référentiel</span>
        )}
      </div>

      <div className="project-overview-section">
        <span className="project-overview-label">Tags</span>
        {(project.tags?.length ?? 0) > 0 ? (
          <div className="project-tags">
            {project.tags!.map((tag) => (
              <span key={tag} className="project-tag">
                {tag}
              </span>
            ))}
          </div>
        ) : (
          <span className="project-overview-empty">Aucun tag</span>
        )}
      </div>
    </div>
  );
}
