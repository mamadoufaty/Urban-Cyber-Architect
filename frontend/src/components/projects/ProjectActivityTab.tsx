import { useCallback, useEffect, useState } from "react";
import { listProjectActivity, type ProjectActivity } from "../../api";
import { activityActionLabel } from "../../projects/constants";
import { formatDateTime } from "../../projects/format";

type Props = {
  projectId: string;
};

export default function ProjectActivityTab({ projectId }: Props) {
  const [items, setItems] = useState<ProjectActivity[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setItems(await listProjectActivity(projectId));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erreur de chargement");
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    load();
  }, [load]);

  if (loading) {
    return <div className="card">Chargement de l'activité…</div>;
  }

  return (
    <div className="project-tab-panel">
      {error && (
        <div className="card project-error" role="alert">
          {error}
        </div>
      )}
      <div className="projects-table-wrapper card">
        <table className="projects-table">
          <thead>
            <tr>
              <th>Date</th>
              <th>Action</th>
              <th>Détails</th>
            </tr>
          </thead>
          <tbody>
            {items.length === 0 ? (
              <tr>
                <td colSpan={3} style={{ color: "var(--muted)" }}>
                  Aucune activité enregistrée.
                </td>
              </tr>
            ) : (
              items.map((item) => (
                <tr key={item.id}>
                  <td>{formatDateTime(item.created_at)}</td>
                  <td>
                    <span className="status-badge">{activityActionLabel(item.action)}</span>
                  </td>
                  <td>
                    <code className="activity-details">
                      {Object.keys(item.details).length > 0
                        ? JSON.stringify(item.details)
                        : "—"}
                    </code>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
