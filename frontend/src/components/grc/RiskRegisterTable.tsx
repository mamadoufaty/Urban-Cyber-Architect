import { useMemo } from "react";
import type { RiskRegisterRow, RiskRegisterSortField } from "./types";

interface Props {
  rows: RiskRegisterRow[];
  sortBy: RiskRegisterSortField;
  sortDir: "asc" | "desc";
  onSort: (field: RiskRegisterSortField) => void;
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString("fr-FR", {
    dateStyle: "short",
    timeStyle: "short",
  });
}

function criticalityClass(value: string): string {
  const map: Record<string, string> = {
    Critique: "grc-badge grc-badge-critical",
    Élevée: "grc-badge grc-badge-high",
    Modérée: "grc-badge grc-badge-medium",
    Faible: "grc-badge grc-badge-low",
  };
  return map[value] ?? "grc-badge";
}

export default function RiskRegisterTable({ rows, sortBy, sortDir, onSort }: Props) {
  const sortIndicator = useMemo(
    () => (field: RiskRegisterSortField) => {
      if (sortBy !== field) return "";
      return sortDir === "asc" ? " ▲" : " ▼";
    },
    [sortBy, sortDir]
  );

  if (!rows.length) {
    return (
      <div className="grc-empty">
        <p>Aucun risque consolidé pour ce projet.</p>
        <p className="grc-empty-hint">
          Complétez les ateliers EBIOS RM (atelier 5) pour alimenter automatiquement le registre.
        </p>
      </div>
    );
  }

  return (
    <div className="grc-table-wrap">
      <table className="grc-table">
        <thead>
          <tr>
            {[
              ["risk_id", "Identifiant"],
              ["organization", "Organisation"],
              ["supporting_asset", "Bien support"],
              ["risk_source", "Source de risque"],
              ["strategic_scenario", "Scénario strat."],
              ["operational_scenario", "Scénario op."],
              ["owner_actor", "Propriétaire"],
              ["decision_maker", "Décideur"],
              ["severity", "Gravité"],
              ["likelihood", "Probabilité"],
              ["criticality", "Criticité"],
              ["treatment_decision", "Décision"],
              ["retained_measures", "Mesures"],
              ["residual_risk", "Résiduel"],
              ["status", "Statut"],
              ["updated_at", "Mise à jour"],
            ].map(([key, label]) => {
              const field = key as RiskRegisterSortField | "retained_measures" | "residual_risk";
              const sortable = field !== "retained_measures" && field !== "residual_risk";
              return (
                <th key={key}>
                  {sortable ? (
                    <button
                      type="button"
                      className="grc-sort-btn"
                      onClick={() => onSort(field as RiskRegisterSortField)}
                    >
                      {label}
                      {sortIndicator(field as RiskRegisterSortField)}
                    </button>
                  ) : (
                    label
                  )}
                </th>
              );
            })}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.evaluation_id}>
              <td className="grc-mono" title={row.risk_id}>
                {row.risk_id.slice(0, 8)}…
              </td>
              <td>{row.organization || "—"}</td>
              <td>{row.supporting_asset || "—"}</td>
              <td>{row.risk_source || "—"}</td>
              <td>{row.strategic_scenario || "—"}</td>
              <td title={row.operational_scenario}>{row.operational_scenario || "—"}</td>
              <td>{row.owner_actor || "—"}</td>
              <td>{row.decision_maker || "—"}</td>
              <td>{row.severity || "—"}</td>
              <td>{row.likelihood || "—"}</td>
              <td>
                <span className={criticalityClass(row.criticality)}>{row.criticality || "—"}</span>
              </td>
              <td>{row.treatment_decision || "—"}</td>
              <td className="grc-measures" title={row.retained_measures.join(", ")}>
                {row.retained_measures.length
                  ? `${row.retained_measure_count} — ${row.retained_measures.slice(0, 2).join(", ")}${
                      row.retained_measures.length > 2 ? "…" : ""
                    }`
                  : "—"}
              </td>
              <td>
                <span className={criticalityClass(row.residual_risk)}>{row.residual_risk}</span>
              </td>
              <td>
                <span className={`grc-status grc-status-${row.status.toLowerCase().replace(/\s+/g, "-")}`}>
                  {row.status}
                </span>
              </td>
              <td>{formatDate(row.updated_at)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
