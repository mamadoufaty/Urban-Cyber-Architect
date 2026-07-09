import { Link } from "react-router-dom";
import type { NextActionItem } from "../../projects/dashboardMetrics";

type Props = {
  actions: NextActionItem[];
};

export default function ProjectNextActions({ actions }: Props) {
  if (actions.length === 0) {
    return (
      <div className="card project-next-actions">
        <h4>Prochaines actions</h4>
        <p className="project-overview-empty">Toutes les actions prioritaires sont en bonne voie.</p>
      </div>
    );
  }

  return (
    <div className="card project-next-actions">
      <h4>Prochaines actions</h4>
      <ul className="project-next-actions-list">
        {actions.map((action) => (
          <li key={action.id} className={`project-next-action priority-${action.priority}`}>
            <div>
              <strong>{action.label}</strong>
              <p>{action.description}</p>
            </div>
            <Link to={action.openUrl} className="btn btn-primary btn-sm">
              Démarrer
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
