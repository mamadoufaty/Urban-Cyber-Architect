import { useEffect, useState } from "react";
import { fetchJSON, getGovernance } from "../api";

export default function AIGovernance() {
  const [config, setConfig] = useState<Record<string, unknown> | null>(null);
  const [models, setModels] = useState<Array<{ model_id: string; provider: string; available: boolean }>>([]);

  useEffect(() => {
    getGovernance().then(setConfig);
    fetchJSON<{ models: Array<{ model_id: string; provider: string; available: boolean }> }>("/models").then(
      (d) => setModels(d.models)
    );
  }, []);

  const weights = [
    { key: "urbanisme_weight", label: "Urbanisme", default: 20 },
    { key: "conformite_weight", label: "Conformité", default: 25 },
    { key: "ebios_weight", label: "EBIOS", default: 30 },
    { key: "architecture_weight", label: "Architecture", default: 25 },
  ];

  return (
    <>
      <div className="page-header">
        <h2>AI Governance</h2>
        <p>Configuration des modèles, du juge et des critères de scoring</p>
      </div>

      <div className="card">
        <h3>Modèles LLM</h3>
        <div className="grid-2" style={{ marginTop: "1rem" }}>
          {models.map((m) => (
            <div key={m.model_id} style={{ padding: "0.75rem", background: "var(--surface2)", borderRadius: 8 }}>
              <strong>{m.model_id}</strong>
              <span style={{ display: "block", fontSize: "0.75rem", color: "var(--muted)", fontFamily: "var(--mono)" }}>
                {m.provider} — {m.available ? "disponible" : "non configuré"}
              </span>
            </div>
          ))}
        </div>
      </div>

      <div className="card">
        <h3>Pondération des critères Judge</h3>
        {weights.map((w) => {
          const val = ((config?.[w.key] as number) ?? w.default / 100) * 100;
          return (
            <div key={w.key} style={{ marginBottom: "1rem" }}>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.875rem" }}>
                <span>{w.label}</span>
                <span style={{ fontFamily: "var(--mono)", color: "var(--accent)" }}>{val.toFixed(0)}%</span>
              </div>
              <div className="score-bar">
                <div className="score-bar-fill" style={{ width: `${val}%` }} />
              </div>
            </div>
          );
        })}
      </div>

      <div className="card">
        <h3>Juge actif</h3>
        <span className="status-badge">{config?.judge_id as string ?? "mock-judge"}</span>
      </div>
    </>
  );
}
