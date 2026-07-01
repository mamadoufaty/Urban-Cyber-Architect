import type { TopRiskItem } from "./dashboardTypes";

interface Props {
  items: TopRiskItem[];
}

function critClass(value: string): string {
  const map: Record<string, string> = {
    Critique: "grc-dash-badge-critical",
    Élevée: "grc-dash-badge-high",
    Modérée: "grc-dash-badge-medium",
    Faible: "grc-dash-badge-low",
  };
  return map[value] ?? "";
}

export default function TopRisksPanel({ items }: Props) {
  return (
    <section className="grc-dash-panel">
      <header className="grc-dash-panel-header">
        <h2>Top risques</h2>
        <span className="grc-dash-panel-hint">5 risques les plus critiques</span>
      </header>
      {!items.length ? (
        <p className="grc-dash-empty">Aucun risque à afficher.</p>
      ) : (
        <div className="grc-dash-table-wrap">
          <table className="grc-dash-table">
            <thead>
              <tr>
                <th>Identifiant</th>
                <th>Bien support</th>
                <th>Organisation</th>
                <th>Source</th>
                <th>Criticité</th>
                <th>Résiduel</th>
                <th>Décision</th>
              </tr>
            </thead>
            <tbody>
              {items.map((row) => (
                <tr key={row.risk_id}>
                  <td className="grc-dash-mono" title={row.risk_id}>
                    {row.risk_id.slice(0, 8)}…
                  </td>
                  <td>{row.supporting_asset || "—"}</td>
                  <td>{row.organization || "—"}</td>
                  <td>{row.risk_source || "—"}</td>
                  <td>
                    <span className={`grc-dash-badge ${critClass(row.criticality)}`}>
                      {row.criticality}
                    </span>
                  </td>
                  <td>
                    <span className={`grc-dash-badge ${critClass(row.residual_risk)}`}>
                      {row.residual_risk}
                    </span>
                  </td>
                  <td>{row.treatment_decision}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
