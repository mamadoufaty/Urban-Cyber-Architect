import type { SoaKpiKey, SoaSummary } from "./types";

type Props = {
  summary: SoaSummary | null;
  activeKpi: SoaKpiKey | null;
  onKpiClick: (key: SoaKpiKey) => void;
};

const CARDS: { key: SoaKpiKey; label: string; getValue: (s: SoaSummary) => string | number }[] = [
  { key: "total", label: "Contrôles totaux", getValue: (s) => s.total_controls },
  { key: "applicable", label: "Applicables", getValue: (s) => s.applicable_controls },
  { key: "non_applicable", label: "Non applicables", getValue: (s) => s.non_applicable_controls },
  { key: "implemented", label: "Implémentés", getValue: (s) => s.implemented_controls },
  { key: "coverage", label: "Taux de couverture", getValue: (s) => `${s.coverage_rate_percent} %` },
];

export default function SoaSummaryCards({ summary, activeKpi, onKpiClick }: Props) {
  if (!summary) return null;

  return (
    <div className="soa-kpi-grid" role="group" aria-label="Résumé SoA">
      {CARDS.map(({ key, label, getValue }) => (
        <button
          key={key}
          type="button"
          className={`soa-kpi-card soa-kpi-${key}${activeKpi === key ? " soa-kpi-active" : ""}`}
          onClick={() => onKpiClick(key)}
        >
          <span className="soa-kpi-value">{getValue(summary)}</span>
          <span className="soa-kpi-label">{label}</span>
        </button>
      ))}
    </div>
  );
}
