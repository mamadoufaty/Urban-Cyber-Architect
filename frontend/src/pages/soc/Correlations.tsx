import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { getSocCorrelations, listProjects, type Project, type SocCorrelationsResponse } from "../../api";
import GrcRibbon from "../../components/grc/GrcRibbon";
import "../../styles/soc-correlations.css";
import "../../styles/grc.css";

function formatDate(iso: string | null | undefined): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleString("fr-FR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function levelClass(level: number): string {
  if (level >= 12) return "soc-level-critical";
  if (level >= 8) return "soc-level-high";
  if (level >= 5) return "soc-level-medium";
  return "soc-level-low";
}

export default function SocCorrelations() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedId, setSelectedId] = useState(searchParams.get("project") ?? "");
  const [data, setData] = useState<SocCorrelationsResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const projectName = useMemo(
    () => projects.find((p) => p.id === selectedId)?.name ?? "—",
    [projects, selectedId]
  );

  const load = useCallback(async () => {
    if (!selectedId) return;
    setLoading(true);
    setError(null);
    try {
      const response = await getSocCorrelations(selectedId);
      setData(response);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erreur de chargement des corrélations");
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [selectedId]);

  useEffect(() => {
    listProjects().then((list) => {
      setProjects(list);
      const fromUrl = searchParams.get("project");
      if (fromUrl && list.some((p) => p.id === fromUrl)) setSelectedId(fromUrl);
      else if (!selectedId && list.length) setSelectedId(list[0].id);
    });
  }, [searchParams]);

  useEffect(() => {
    if (!selectedId) return;
    setSearchParams({ project: selectedId });
    load();
  }, [selectedId, load, setSearchParams]);

  const handleProjectChange = (id: string) => {
    setSelectedId(id);
    setSearchParams(id ? { project: id } : {});
  };

  return (
    <div className="grc-workspace soc-corr-workspace">
      <GrcRibbon
        projects={projects}
        selectedProjectId={selectedId}
        onProjectChange={handleProjectChange}
        moduleLabel="SOC — Corrélations"
      />

      <div className="soc-corr-page">
        <header className="soc-corr-header">
          <div>
            <p className="soc-corr-eyebrow">SOC</p>
            <h1>Corrélations Wazuh ↔ Urbanisme ↔ EBIOS ↔ GRC</h1>
          </div>
          <button type="button" className="soc-corr-btn" onClick={load} disabled={!selectedId || loading}>
            {loading ? "Actualisation…" : "Actualiser"}
          </button>
        </header>

        <p className="soc-corr-banner">
          Lecture seule — incidents dérivés des alertes Wazuh et des référentiels existants (projet : {projectName}).
        </p>

        {error && <div className="soc-corr-error">{error}</div>}
        {data?.metadata.wazuh_error && (
          <div className="soc-corr-warn">{data.metadata.wazuh_error}</div>
        )}

        {data && (
          <section className="soc-corr-kpi-grid" aria-label="Résumé corrélations">
            <div className="soc-corr-kpi">
              <span className="soc-corr-kpi-label">Alertes</span>
              <span className="soc-corr-kpi-value">{data.summary.alerts_total}</span>
            </div>
            <div className="soc-corr-kpi">
              <span className="soc-corr-kpi-label">Incidents</span>
              <span className="soc-corr-kpi-value">{data.summary.incidents_count}</span>
            </div>
            <div className="soc-corr-kpi">
              <span className="soc-corr-kpi-label">Biens matchés</span>
              <span className="soc-corr-kpi-value">{data.summary.assets_matched}</span>
            </div>
            <div className="soc-corr-kpi">
              <span className="soc-corr-kpi-label">Risques GRC liés</span>
              <span className="soc-corr-kpi-value">{data.summary.correlated_risks}</span>
            </div>
          </section>
        )}

        <div className="soc-corr-table-section">
          {loading && !data && <div className="soc-corr-loading">Chargement…</div>}
          {data && data.incidents.length === 0 && (
            <div className="soc-corr-empty">
              Aucune corrélation disponible. Vérifiez le connecteur{" "}
              <Link to="/parametres/connecteurs/wazuh">Wazuh</Link> et les ateliers EBIOS.
            </div>
          )}
          {data && data.incidents.length > 0 && (
            <div className="soc-corr-table-wrap">
              <table className="soc-corr-table">
                <thead>
                  <tr>
                    <th>Alerte</th>
                    <th>Agent</th>
                    <th>Bien support</th>
                    <th>Organisation</th>
                    <th>Processus</th>
                    <th>Scénario op.</th>
                    <th>Scénario strat.</th>
                    <th>Source risque</th>
                    <th>Risque GRC</th>
                    <th>Responsable</th>
                  </tr>
                </thead>
                <tbody>
                  {data.incidents.map((inc) => (
                    <tr key={inc.incident_id}>
                      <td>
                        <div className="soc-corr-alert-cell">
                          <span className={`soc-level-badge ${levelClass(inc.alert.rule_level)}`}>
                            {inc.alert.rule_level}
                          </span>
                          <span>{formatDate(inc.alert.timestamp)}</span>
                          <small>{inc.alert.rule_description}</small>
                        </div>
                      </td>
                      <td>
                        <strong>{inc.agent.name || "—"}</strong>
                        <small>{inc.agent.ip || inc.agent.id}</small>
                      </td>
                      <td>{inc.supporting_asset || inc.urbanism_entity_label || "—"}</td>
                      <td>{inc.organization || "—"}</td>
                      <td>{inc.processus || "—"}</td>
                      <td>{inc.operational_scenario || "—"}</td>
                      <td>{inc.strategic_scenario || "—"}</td>
                      <td>{inc.risk_source || "—"}</td>
                      <td>
                        {inc.grc_risk.risk_id ? (
                          <>
                            <Link to={`/registre-risques?project=${selectedId}`}>
                              {inc.grc_risk.criticality || inc.grc_risk.risk_id.slice(0, 8)}
                            </Link>
                            <small>{inc.grc_risk.residual_risk}</small>
                          </>
                        ) : (
                          "—"
                        )}
                      </td>
                      <td>{inc.business_owner || "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          {!selectedId && (
            <div className="soc-corr-empty">
              Sélectionnez un projet — ou <Link to="/projects">créez-en un</Link>.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
