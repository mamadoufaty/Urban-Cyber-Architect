import { Link } from "react-router-dom";
import {
  moduleStatusLabel,
  type ModuleProgressItem,
} from "../../projects/dashboardMetrics";
import { formatDateTime } from "../../projects/format";

type Props = {
  modules: ModuleProgressItem[];
};

export default function ProjectModuleProgress({ modules }: Props) {
  return (
    <div className="card project-module-progress">
      <h4>Progression par module</h4>
      <div className="project-module-list">
        {modules.map((mod) => (
          <div key={mod.id} className="project-module-row">
            <div className="project-module-row-header">
              <strong>{mod.label}</strong>
              <span className={`module-status module-status-${mod.status}`}>
                {moduleStatusLabel(mod.status)}
              </span>
            </div>
            <div className="project-module-progress-bar-wrap">
              <div
                className="project-module-progress-bar"
                style={{ width: `${mod.percent}%` }}
                role="progressbar"
                aria-valuenow={mod.percent}
                aria-valuemin={0}
                aria-valuemax={100}
              />
            </div>
            <div className="project-module-row-meta">
              <span>{mod.percent} %</span>
              <span>Dernière activité : {formatDateTime(mod.lastActivity)}</span>
              <Link to={mod.openUrl} className="btn btn-secondary btn-sm">
                Ouvrir
              </Link>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
