import type { UrbanismProgress } from "./metamodel";

const STATUS_ICON: Record<string, string> = {
  done: "✔",
  partial: "⏳",
  pending: "○",
};

interface Props {
  progress: UrbanismProgress | null;
  loading?: boolean;
}

export default function UrbanismProgressBar({ progress, loading }: Props) {
  if (loading && !progress) {
    return <div className="card urbanism-progress-bar">Chargement de la progression…</div>;
  }
  if (!progress) return null;

  return (
    <div className="card urbanism-progress-bar ua-panel">
      <div className="urbanism-progress-header">
        <strong>Progression urbanisme</strong>
        <span className="urbanism-progress-percent">{progress.overall_percent}%</span>
      </div>
      <div className="urbanism-progress-track">
        <div className="urbanism-progress-fill" style={{ width: `${progress.overall_percent}%` }} />
      </div>
      <ul className="urbanism-progress-steps">
        {progress.groups.map((g) => (
          <li key={g.id} className={`urbanism-progress-step status-${g.status}`}>
            <span className="step-icon">{STATUS_ICON[g.status] ?? "○"}</span>
            <span className="step-label">{g.label}</span>
            {g.count > 0 && <span className="step-count">{g.count}</span>}
          </li>
        ))}
      </ul>
    </div>
  );
}
