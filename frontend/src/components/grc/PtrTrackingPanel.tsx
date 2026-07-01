import type { PtrTracking } from "./dashboardTypes";

interface Props {
  tracking: PtrTracking;
}

export default function PtrTrackingPanel({ tracking }: Props) {
  const stats = [
    { label: "Ouvertes", value: tracking.open_count, cls: "open" },
    { label: "Planifiées", value: tracking.planned_count, cls: "planned" },
    { label: "En cours", value: tracking.in_progress_count, cls: "progress" },
    { label: "Terminées", value: tracking.completed_count, cls: "done" },
    { label: "En retard", value: tracking.overdue_count, cls: "overdue" },
  ];

  return (
    <section className="grc-dash-panel">
      <header className="grc-dash-panel-header">
        <h2>Suivi PTR</h2>
      </header>
      <div className="grc-dash-ptr-stats">
        {stats.map((s) => (
          <div key={s.label} className={`grc-dash-ptr-stat grc-dash-ptr-${s.cls}`}>
            <span>{s.label}</span>
            <strong>{s.value}</strong>
          </div>
        ))}
      </div>
      {tracking.actions.length > 0 && (
        <div className="grc-dash-table-wrap grc-dash-ptr-table">
          <table className="grc-dash-table">
            <thead>
              <tr>
                <th>Action</th>
                <th>Statut</th>
                <th>Priorité</th>
                <th>Échéance</th>
              </tr>
            </thead>
            <tbody>
              {tracking.actions.slice(0, 8).map((action) => (
                <tr key={action.action_id} className={action.overdue ? "grc-dash-row-overdue" : ""}>
                  <td>{action.label}</td>
                  <td>{action.status}</td>
                  <td>{action.priority || "—"}</td>
                  <td>
                    {action.due_date || "—"}
                    {action.overdue && <span className="grc-dash-overdue-tag">Retard</span>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
