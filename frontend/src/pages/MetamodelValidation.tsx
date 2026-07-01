import { useCallback, useEffect, useState } from "react";
import { getMetamodelValidation } from "../api";
import type { MetamodelValidationReport, RelationRule } from "../components/urbanism/metamodel";

function entityLabel(id: string, report: MetamodelValidationReport | null) {
  const found = report?.expected_entities.find((e) => e.id === id);
  return found?.label ?? id;
}

function relationRow(r: RelationRule) {
  return (
    <tr key={r.id ?? `${r.source}-${r.type}-${r.target}`}>
      <td><code>{r.id ?? "—"}</code></td>
      <td>{r.source}</td>
      <td><em>{r.type}</em></td>
      <td>{r.target}</td>
      <td>{r.category}</td>
    </tr>
  );
}

export default function MetamodelValidation() {
  const [report, setReport] = useState<MetamodelValidationReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getMetamodelValidation();
      setReport(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erreur de chargement");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const ok = report?.status === "ok";

  return (
    <>
      <div className="page-header">
        <div>
          <h2>Validation du métamodèle</h2>
          <p>
            Comparaison du moteur d&apos;urbanisme avec le schéma Club Urba officiel (R01–R30) —
            Projet Fil Rouge ISRC10 Métropolis
          </p>
        </div>
        <button type="button" className="btn btn-secondary" onClick={load} disabled={loading}>
          Actualiser
        </button>
      </div>

      {loading && <div className="card">Analyse du métamodèle…</div>}

      {error && (
        <div className="card project-error" role="alert">
          <p style={{ margin: "0 0 1rem" }}>{error}</p>
          <button type="button" className="btn btn-primary" onClick={load}>
            Réessayer
          </button>
        </div>
      )}

      {!loading && !error && report && (
        <>
          <div className={`card metamodel-status-banner ${ok ? "status-ok" : "status-ko"}`}>
            <strong>{ok ? "✓ Métamodèle conforme au schéma Club Urba" : "✗ Écarts détectés"}</strong>
            <div className="metamodel-summary-grid">
              <span>Entités attendues : {report.summary.entities_expected}</span>
              <span>Entités implémentées : {report.summary.entities_implemented}</span>
              <span>Relations attendues : {report.summary.relations_expected}</span>
              <span>Relations implémentées : {report.summary.relations_implemented}</span>
              <span>Relations manquantes : {report.summary.relations_missing_count}</span>
              <span>Relations invalides : {report.summary.relations_invalid_count}</span>
            </div>
          </div>

          {report.missing_entities.length > 0 && (
            <div className="card project-error">
              <h3>Entités manquantes</h3>
              <ul>
                {report.missing_entities.map((id) => (
                  <li key={id}>{id}</li>
                ))}
              </ul>
            </div>
          )}

          {report.extra_entities.length > 0 && (
            <div className="card">
              <h3>Entités supplémentaires (hors liste minimale)</h3>
              <ul>
                {report.extra_entities.map((id) => (
                  <li key={id}>{entityLabel(id, report)} ({id})</li>
                ))}
              </ul>
            </div>
          )}

          <div className="card">
            <h3>Entités attendues</h3>
            <div className="metamodel-entity-grid">
              {report.expected_entities.map((e) => (
                <div key={e.id} className="metamodel-entity-chip">
                  <strong>{e.label}</strong>
                  <span>{e.couche}</span>
                  {e.note && <small>{e.note}</small>}
                </div>
              ))}
            </div>
          </div>

          <div className="card">
            <h3>Relations attendues (R01–R30)</h3>
            <div className="projects-table-wrapper">
              <table className="projects-table metamodel-table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Source</th>
                    <th>Relation</th>
                    <th>Cible</th>
                    <th>Catégorie</th>
                  </tr>
                </thead>
                <tbody>
                  {report.expected_relations.map(relationRow)}
                </tbody>
              </table>
            </div>
          </div>

          <div className="card">
            <h3>Relations implémentées</h3>
            <div className="projects-table-wrapper">
              <table className="projects-table metamodel-table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Source</th>
                    <th>Relation</th>
                    <th>Cible</th>
                    <th>Catégorie</th>
                  </tr>
                </thead>
                <tbody>
                  {report.implemented_relations.map(relationRow)}
                </tbody>
              </table>
            </div>
          </div>

          {report.missing_relations.length > 0 && (
            <div className="card project-error">
              <h3>Relations manquantes</h3>
              <div className="projects-table-wrapper">
                <table className="projects-table metamodel-table">
                  <thead>
                    <tr>
                      <th>ID</th>
                      <th>Source</th>
                      <th>Relation</th>
                      <th>Cible</th>
                    </tr>
                  </thead>
                  <tbody>
                    {report.missing_relations.map(relationRow)}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {report.invalid_relations.length > 0 && (
            <div className="card project-error">
              <h3>Relations invalides (non présentes sur le schéma)</h3>
              <div className="projects-table-wrapper">
                <table className="projects-table metamodel-table">
                  <thead>
                    <tr>
                      <th>ID</th>
                      <th>Source</th>
                      <th>Relation</th>
                      <th>Cible</th>
                    </tr>
                  </thead>
                  <tbody>
                    {report.invalid_relations.map(relationRow)}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}
    </>
  );
}
