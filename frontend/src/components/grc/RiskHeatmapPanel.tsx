import { Fragment } from "react";
import type { RiskHeatmap } from "./dashboardTypes";

interface Props {
  heatmap: RiskHeatmap;
}

function cellColor(criticality: string, intensity: number): string {
  if (intensity === 0) return "var(--surface2)";
  const map: Record<string, string> = {
    Critique: "rgba(239, 68, 68, 0.85)",
    Élevée: "rgba(245, 158, 11, 0.8)",
    Modérée: "rgba(59, 130, 246, 0.65)",
    Faible: "rgba(0, 212, 170, 0.55)",
  };
  return map[criticality] ?? `rgba(0, 212, 170, ${0.25 + intensity * 0.5})`;
}

export default function RiskHeatmapPanel({ heatmap }: Props) {
  const { cells, max_count, likelihood_labels } = heatmap;

  const cellAt = (sev: number, lik: number) =>
    cells.find((c) => c.severity_score === sev && c.likelihood_score === lik);

  return (
    <section className="grc-dash-panel">
      <header className="grc-dash-panel-header">
        <h2>Heatmap des risques</h2>
        <span className="grc-dash-panel-hint">Gravité × Probabilité</span>
      </header>
      <div className="grc-dash-heatmap">
        <div className="grc-dash-heatmap-axis-y">Gravité ↑</div>
        <div className="grc-dash-heatmap-grid">
          <div className="grc-dash-heatmap-corner" />
          {likelihood_labels.map((label) => (
            <div key={label} className="grc-dash-heatmap-col-label">
              {label}
            </div>
          ))}
          {[4, 3, 2, 1].map((sev) => (
            <Fragment key={sev}>
              <div className="grc-dash-heatmap-row-label">
                {heatmap.severity_labels[sev - 1]}
              </div>
              {[1, 2, 3, 4].map((lik) => {
                const cell = cellAt(sev, lik);
                const count = cell?.count ?? 0;
                const intensity = max_count ? count / max_count : 0;
                return (
                  <div
                    key={`${sev}-${lik}`}
                    className="grc-dash-heatmap-cell"
                    style={{
                      background: cellColor(cell?.dominant_criticality ?? "", intensity),
                    }}
                    title={
                      count
                        ? `${count} risque(s) — ${cell?.dominant_criticality}`
                        : "Aucun risque"
                    }
                  >
                    <span className="grc-dash-heatmap-count">{count || ""}</span>
                  </div>
                );
              })}
            </Fragment>
          ))}
        </div>
        <div className="grc-dash-heatmap-axis-x">Probabilité →</div>
      </div>
    </section>
  );
}
