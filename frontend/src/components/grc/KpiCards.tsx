import type { DashboardKpi } from "./dashboardTypes";

const KPI_ITEMS: {
  key: keyof DashboardKpi;
  label: string;
  accent?: string;
  suffix?: string;
}[] = [
  { key: "total_risks", label: "Risques totaux" },
  { key: "critical_risks", label: "Critiques", accent: "critical" },
  { key: "high_risks", label: "Élevés", accent: "high" },
  { key: "moderate_risks", label: "Modérés", accent: "medium" },
  { key: "low_risks", label: "Faibles", accent: "low" },
  { key: "critical_residual_risks", label: "Résiduels critiques", accent: "critical" },
  { key: "ptr_open_actions", label: "PTR ouvertes" },
  { key: "ptr_completed_actions", label: "PTR terminées" },
  { key: "treatment_rate_percent", label: "Taux de traitement", suffix: "%" },
  { key: "iso27002_coverage_percent", label: "Couverture ISO 27002", suffix: "%" },
];

interface Props {
  kpis: DashboardKpi;
}

export default function KpiCards({ kpis }: Props) {
  return (
    <div className="grc-dash-kpi-grid">
      {KPI_ITEMS.map(({ key, label, accent, suffix }) => (
        <article key={key} className={`grc-dash-kpi-card${accent ? ` grc-dash-kpi-${accent}` : ""}`}>
          <span className="grc-dash-kpi-label">{label}</span>
          <strong className="grc-dash-kpi-value">
            {kpis[key]}
            {suffix ?? ""}
          </strong>
        </article>
      ))}
    </div>
  );
}
