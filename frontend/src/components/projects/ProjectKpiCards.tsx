import type { DashboardKpis } from "../../projects/dashboardMetrics";

type Props = {
  kpis: DashboardKpis;
};

const KPI_ITEMS: Array<{
  key: keyof DashboardKpis;
  label: string;
  suffix?: string;
}> = [
  { key: "globalProgress", label: "Progression globale", suffix: "%" },
  { key: "memberCount", label: "Membres équipe" },
  { key: "activityCount", label: "Activités" },
  { key: "activeModulesCount", label: "Modules actifs" },
  { key: "deliverableCount", label: "Livrables générés" },
  { key: "riskCount", label: "Risques identifiés" },
  { key: "maturityLevel", label: "Maturité estimée" },
];

export default function ProjectKpiCards({ kpis }: Props) {
  return (
    <div className="project-kpi-cards">
      {KPI_ITEMS.map((item) => {
        const value = kpis[item.key];
        const display =
          typeof value === "number"
            ? `${value}${item.suffix ?? ""}`
            : String(value);
        return (
          <div key={item.key} className="card project-kpi-card">
            <span className="project-kpi-label">{item.label}</span>
            <strong className="project-kpi-value">{display}</strong>
          </div>
        );
      })}
    </div>
  );
}
