export default function Dashboard() {
  const views = [
    { role: "RSSI", desc: "Vue risques, conformité, incidents et feuille de route SSI" },
    { role: "Architecte", desc: "Vue couches urbanisme, architecture cible et composants" },
    { role: "Direction", desc: "Vue exécutive, ROI sécurité et alignement stratégique" },
    { role: "Consultant", desc: "Vue livrables, EBIOS et recommandations détaillées" },
  ];

  return (
    <>
      <div className="page-header">
        <h2>Dashboard</h2>
        <p>Plateforme d'aide à la décision — architecture d'entreprise & cybersécurité</p>
      </div>

      <div className="card">
        <h3>Pipeline IA</h3>
        <div className="pipeline" style={{ marginTop: "1rem" }}>
          <span className="step">Context Builder</span>
          <span className="arrow">→</span>
          <span className="step">Knowledge Base</span>
          <span className="arrow">→</span>
          <span className="step">AI Orchestrator</span>
          <span className="arrow">→</span>
          <span className="step">Multi-LLM</span>
          <span className="arrow">→</span>
          <span className="step">Judge Engine</span>
          <span className="arrow">→</span>
          <span className="step">Validation Humaine</span>
          <span className="arrow">→</span>
          <span className="step">Knowledge Graph</span>
        </div>
      </div>

      <div className="grid-2">
        {views.map((v) => (
          <div key={v.role} className="card">
            <h3>Vue {v.role}</h3>
            <p style={{ color: "var(--muted)", fontSize: "0.875rem" }}>{v.desc}</p>
            <span className="status-badge" style={{ marginTop: "0.75rem" }}>V1 — à venir</span>
          </div>
        ))}
      </div>
    </>
  );
}
