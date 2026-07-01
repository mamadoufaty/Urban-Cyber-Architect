import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  getWazuhAlerts,
  getWazuhStatus,
  type WazuhAlertItem,
  type WazuhStatus,
} from "../../api";
import "../../styles/wazuh.css";

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
  if (level >= 12) return "wazuh-level-critical";
  if (level >= 8) return "wazuh-level-high";
  if (level >= 5) return "wazuh-level-medium";
  return "wazuh-level-low";
}

export default function WazuhDashboard() {
  const [status, setStatus] = useState<WazuhStatus | null>(null);
  const [alerts, setAlerts] = useState<WazuhAlertItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [statusRes, alertsRes] = await Promise.all([
        getWazuhStatus(),
        getWazuhAlerts({ limit: 20 }),
      ]);
      setStatus(statusRes);
      setAlerts(alertsRes.alerts);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erreur de chargement Wazuh");
      setStatus(null);
      setAlerts([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <div className="wazuh-page">
      <header className="wazuh-header">
        <div>
          <p className="wazuh-eyebrow">SOC</p>
          <h1>Wazuh</h1>
        </div>
        <div className="wazuh-header-actions">
          <Link to="/parametres/connecteurs/wazuh" className="wazuh-btn wazuh-btn-ghost">
            Paramètres
          </Link>
          <button type="button" className="wazuh-btn" onClick={load} disabled={loading}>
            {loading ? "Actualisation…" : "Actualiser"}
          </button>
        </div>
      </header>

      {error && <div className="wazuh-error">{error}</div>}

      {!status?.configured && !loading && (
        <div className="wazuh-banner wazuh-banner-warn">
          Connecteur non configuré.{" "}
          <Link to="/parametres/connecteurs/wazuh">Configurer Wazuh</Link>
        </div>
      )}

      <section className="wazuh-kpi-grid" aria-label="État Wazuh">
        <div className={`wazuh-kpi-card ${status?.connected ? "wazuh-kpi-ok" : "wazuh-kpi-ko"}`}>
          <span className="wazuh-kpi-label">État connexion</span>
          <span className="wazuh-kpi-value">
            {status?.connected ? "Connecté" : status?.configured ? "Déconnecté" : "Non configuré"}
          </span>
        </div>
        <div className="wazuh-kpi-card">
          <span className="wazuh-kpi-label">Version Wazuh</span>
          <span className="wazuh-kpi-value">{status?.wazuh_version || "—"}</span>
        </div>
        <div className="wazuh-kpi-card">
          <span className="wazuh-kpi-label">Agents (total)</span>
          <span className="wazuh-kpi-value">{status?.agents_total ?? "—"}</span>
        </div>
        <div className="wazuh-kpi-card">
          <span className="wazuh-kpi-label">Agents connectés</span>
          <span className="wazuh-kpi-value wazuh-kpi-active">{status?.agents_active ?? "—"}</span>
        </div>
        <div className="wazuh-kpi-card wazuh-kpi-wide">
          <span className="wazuh-kpi-label">Dernière synchronisation</span>
          <span className="wazuh-kpi-value">{formatDate(status?.last_sync_at)}</span>
        </div>
      </section>

      {status?.error && (
        <div className="wazuh-banner wazuh-banner-error">{status.error}</div>
      )}

      <section className="wazuh-alerts-section">
        <h2>Dernières alertes</h2>
        {loading && !alerts.length && <div className="wazuh-loading">Chargement des alertes…</div>}
        {!loading && !alerts.length && (
          <div className="wazuh-empty">
            {status?.connected
              ? "Aucune alerte récente ou indexer inaccessible."
              : "Configurez et activez le connecteur pour afficher les alertes."}
          </div>
        )}
        {alerts.length > 0 && (
          <div className="wazuh-table-wrap">
            <table className="wazuh-table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Niveau</th>
                  <th>Règle</th>
                  <th>Agent</th>
                  <th>Description</th>
                </tr>
              </thead>
              <tbody>
                {alerts.map((alert) => (
                  <tr key={alert.id}>
                    <td>{formatDate(alert.timestamp)}</td>
                    <td>
                      <span className={`wazuh-level-badge ${levelClass(alert.rule_level)}`}>
                        {alert.rule_level}
                      </span>
                    </td>
                    <td>{alert.rule_id}</td>
                    <td>{alert.agent_name || alert.agent_id || "—"}</td>
                    <td className="wazuh-cell-desc">{alert.rule_description || alert.full_log}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        <p className="wazuh-footnote">
          Lecture seule — API Wazuh Manager + Indexer. Aucune corrélation Urbanisme/GRC.
        </p>
      </section>
    </div>
  );
}
