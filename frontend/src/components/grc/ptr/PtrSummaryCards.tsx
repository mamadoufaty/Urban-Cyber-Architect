import type { PtrKpiKey, PtrSummary } from "./types";

type Props = {
  summary: PtrSummary | null;
  activeKpi: PtrKpiKey | null;
  onKpiClick: (key: PtrKpiKey) => void;
};

const CARDS: {
  key: PtrKpiKey;
  label: string;
  getValue: (s: PtrSummary) => string | number;
}[] = [
  { key: "total", label: "Actions totales", getValue: (s) => s.total_actions },
  { key: "open", label: "Ouvertes", getValue: (s) => s.open_actions },
  { key: "in_progress", label: "En cours", getValue: (s) => s.in_progress_actions },
  { key: "completed", label: "Terminées", getValue: (s) => s.completed_actions },
  { key: "overdue", label: "En retard", getValue: (s) => s.overdue_actions },
];

export default function PtrSummaryCards({ summary, activeKpi, onKpiClick }: Props) {
  if (!summary) return null;

  return (
    <div className="ptr-kpi-section">
      <div className="ptr-kpi-grid" role="group" aria-label="Résumé PTR">
        {CARDS.map(({ key, label, getValue }) => (
          <button
            key={key}
            type="button"
            className={`ptr-kpi-card ptr-kpi-${key}${activeKpi === key ? " ptr-kpi-active" : ""}`}
            onClick={() => onKpiClick(key)}
          >
            <span className="ptr-kpi-value">{getValue(summary)}</span>
            <span className="ptr-kpi-label">{label}</span>
          </button>
        ))}
      </div>
      <div className="ptr-budget-row">
        <div className="ptr-budget-card">
          <span className="ptr-kpi-label">Budget total</span>
          <span className="ptr-kpi-value">{summary.total_budget.toLocaleString("fr-FR")} €</span>
        </div>
        <div className="ptr-budget-card">
          <span className="ptr-kpi-label">Budget consommé</span>
          <span className="ptr-kpi-value">{summary.consumed_budget.toLocaleString("fr-FR")} €</span>
        </div>
        <button
          type="button"
          className={`ptr-kpi-card ptr-kpi-coverage${activeKpi === "coverage" ? " ptr-kpi-active" : ""}`}
          onClick={() => onKpiClick("coverage")}
        >
          <span className="ptr-kpi-value">{summary.global_progress_percent} %</span>
          <span className="ptr-kpi-label">Avancement global</span>
        </button>
      </div>
    </div>
  );
}
