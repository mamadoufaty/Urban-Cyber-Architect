import type { PtrActionRow } from "./types";

type Props = {
  rows: PtrActionRow[];
  editable: boolean;
  savingId: string | null;
  onPatch: (actionId: string, patch: { status?: string; progress_percent?: number }) => void;
};

const STATUS_OPTIONS = ["Planifié", "En cours", "Bloqué", "Terminé"];

function priorityClass(priority: string): string {
  const map: Record<string, string> = {
    Critique: "ptr-priority-critical",
    Élevée: "ptr-priority-high",
    Moyenne: "ptr-priority-medium",
    Faible: "ptr-priority-low",
  };
  return map[priority] ?? "ptr-priority-medium";
}

function statusClass(status: string): string {
  const map: Record<string, string> = {
    Planifié: "ptr-status-planned",
    "En cours": "ptr-status-progress",
    Bloqué: "ptr-status-blocked",
    Terminé: "ptr-status-done",
    "En retard": "ptr-status-overdue",
  };
  return map[status] ?? "ptr-status-planned";
}

function formatBudget(value: number | null): string {
  if (value === null || value === undefined) return "—";
  return `${value.toLocaleString("fr-FR")} €`;
}

export default function PtrTable({ rows, editable, savingId, onPatch }: Props) {
  if (!rows.length) {
    return <div className="ptr-empty">Aucune action PTR ne correspond aux filtres.</div>;
  }

  return (
    <div className="ptr-table-wrap">
      <table className="ptr-table">
        <thead>
          <tr>
            <th>ID PTR</th>
            <th>Mesure</th>
            <th>Responsable</th>
            <th>Organisation</th>
            <th>Priorité</th>
            <th>Budget</th>
            <th>Échéance</th>
            <th>Statut</th>
            <th>Progression</th>
            <th>Décision</th>
            <th>Risque résiduel</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr
              key={row.action_id}
              className={row.overdue ? "ptr-row-overdue" : row.due_soon ? "ptr-row-due-soon" : ""}
            >
              <td className="ptr-cell-id" title={row.associated_risk}>
                {row.ptr_id.slice(0, 8)}
              </td>
              <td>{row.security_measure}</td>
              <td>{row.responsible || "—"}</td>
              <td>{row.organization || "—"}</td>
              <td>
                <span className={`ptr-badge ${priorityClass(row.priority)}`}>{row.priority}</span>
              </td>
              <td>{formatBudget(row.budget)}</td>
              <td>{row.due_date || "—"}</td>
              <td>
                {editable ? (
                  <select
                    className={`ptr-inline-select ${statusClass(row.status)}`}
                    value={row.status === "En retard" ? "Planifié" : row.status}
                    disabled={savingId === row.action_id}
                    onChange={(e) => onPatch(row.action_id, { status: e.target.value })}
                  >
                    {STATUS_OPTIONS.map((s) => (
                      <option key={s} value={s}>{s}</option>
                    ))}
                  </select>
                ) : (
                  <span className={`ptr-badge ${statusClass(row.status)}`}>{row.status}</span>
                )}
              </td>
              <td>
                {editable ? (
                  <input
                    type="number"
                    className="ptr-inline-progress"
                    min={0}
                    max={100}
                    value={row.progress_percent}
                    disabled={savingId === row.action_id}
                    onChange={(e) =>
                      onPatch(row.action_id, { progress_percent: Number(e.target.value) })
                    }
                  />
                ) : (
                  <div className="ptr-progress-bar" aria-label={`${row.progress_percent}%`}>
                    <div className="ptr-progress-fill" style={{ width: `${row.progress_percent}%` }} />
                    <span>{row.progress_percent}%</span>
                  </div>
                )}
              </td>
              <td>{row.treatment_decision || "—"}</td>
              <td>{row.residual_risk || "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
