import { useEffect, useState } from "react";
import { listSectors } from "../api";

export default function KnowledgeBase() {
  const [sectors, setSectors] = useState<Array<{ id: string; name: string; domains: string[] }>>([]);

  useEffect(() => {
    listSectors().then(setSectors).catch(console.error);
  }, []);

  return (
    <>
      <div className="page-header">
        <h2>Knowledge Base</h2>
        <p>Bibliothèque de connaissances métier par secteur</p>
      </div>

      <div className="grid-2">
        {sectors.map((s) => (
          <div key={s.id} className="card">
            <h3>{s.name}</h3>
            <div style={{ display: "flex", flexWrap: "wrap", gap: "0.4rem", marginTop: "0.75rem" }}>
              {s.domains.map((d) => (
                <span key={d} className="status-badge">{d}</span>
              ))}
            </div>
          </div>
        ))}
      </div>
    </>
  );
}
