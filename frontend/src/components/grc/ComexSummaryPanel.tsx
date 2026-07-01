import type { ComexSummary } from "./dashboardTypes";

interface Props {
  comex: ComexSummary;
  projectName: string;
  exportEndpoints?: {
    dashboard_pdf: string;
    comex_summary: string;
    rssi_report: string;
    implemented: boolean;
  };
}

function levelClass(level: string): string {
  const map: Record<string, string> = {
    Critique: "grc-dash-badge-critical",
    Élevée: "grc-dash-badge-high",
    Modérée: "grc-dash-badge-medium",
    Faible: "grc-dash-badge-low",
  };
  return map[level] ?? "";
}

export default function ComexSummaryPanel({ comex, projectName, exportEndpoints }: Props) {
  return (
    <section className="grc-dash-panel grc-dash-comex">
      <header className="grc-dash-panel-header">
        <h2>Vue COMEX</h2>
        <span className="grc-dash-panel-hint">{projectName}</span>
      </header>
      <div className="grc-dash-comex-grid">
        <div className="grc-dash-comex-metric">
          <span>Risque global</span>
          <strong className={`grc-dash-badge ${levelClass(comex.global_risk_level)}`}>
            {comex.global_risk_level}
          </strong>
        </div>
        <div className="grc-dash-comex-metric">
          <span>Risque résiduel</span>
          <strong className={`grc-dash-badge ${levelClass(comex.residual_risk_level)}`}>
            {comex.residual_risk_level}
          </strong>
        </div>
        <div className="grc-dash-comex-metric">
          <span>Décisions à arbitrer</span>
          <strong>{comex.decisions_to_arbitrate}</strong>
        </div>
        <div className="grc-dash-comex-metric">
          <span>Budget estimé</span>
          <strong>
            {comex.estimated_budget_total > 0
              ? `${comex.estimated_budget_total.toLocaleString("fr-FR")} €`
              : "—"}
          </strong>
        </div>
      </div>
      <blockquote className="grc-dash-comex-message">{comex.executive_message}</blockquote>
      {exportEndpoints && !exportEndpoints.implemented && (
        <footer className="grc-dash-export-hint">
          Exports prévus : Dashboard PDF · Synthèse COMEX · Rapport RSSI
        </footer>
      )}
    </section>
  );
}
