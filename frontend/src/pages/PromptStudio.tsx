import { useEffect, useState } from "react";
import { fetchJSON, listPrompts } from "../api";

export default function PromptStudio() {
  const [prompts, setPrompts] = useState<Array<{ name: string; version: string; description: string }>>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [detail, setDetail] = useState<Record<string, string> | null>(null);

  useEffect(() => {
    listPrompts().then(setPrompts);
  }, []);

  async function loadPrompt(name: string) {
    setSelected(name);
    const data = await fetchJSON<Record<string, string>>(`/prompts/${name}`);
    setDetail(data);
  }

  return (
    <>
      <div className="page-header">
        <h2>Prompt Studio</h2>
        <p>Visualiser, modifier et versionner les prompts</p>
      </div>

      <div className="grid-2">
        {prompts.map((p) => (
          <div
            key={p.name}
            className="card"
            style={{ cursor: "pointer", outline: selected === p.name ? "1px solid var(--accent)" : undefined }}
            onClick={() => loadPrompt(p.name)}
          >
            <h3>{p.name}</h3>
            <p style={{ color: "var(--muted)", fontSize: "0.8rem" }}>{p.description}</p>
            <span className="status-badge" style={{ marginTop: "0.5rem" }}>v{p.version}</span>
          </div>
        ))}
      </div>

      {detail && (
        <div className="card" style={{ marginTop: "1.5rem" }}>
          <h3>{detail.name} — v{detail.version}</h3>
          <pre className="json" style={{ marginTop: "1rem" }}>{detail.template}</pre>
        </div>
      )}
    </>
  );
}
