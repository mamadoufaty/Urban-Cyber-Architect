import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  getWazuhConfig,
  saveWazuhConfig,
  testWazuhConnection,
  type WazuhConfig,
  type WazuhTestResult,
} from "../../api";
import "../../styles/wazuh.css";

export default function WazuhConnectorSettings() {
  const [baseUrl, setBaseUrl] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [verifySsl, setVerifySsl] = useState(true);
  const [enabled, setEnabled] = useState(false);
  const [indexerUrl, setIndexerUrl] = useState("");
  const [indexerUsername, setIndexerUsername] = useState("");
  const [indexerPassword, setIndexerPassword] = useState("");
  const [passwordConfigured, setPasswordConfigured] = useState(false);
  const [indexerPasswordConfigured, setIndexerPasswordConfigured] = useState(false);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<WazuhTestResult | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setError(null);
    try {
      const config: WazuhConfig = await getWazuhConfig();
      setBaseUrl(config.base_url);
      setUsername(config.username);
      setVerifySsl(config.verify_ssl);
      setEnabled(config.enabled);
      setIndexerUrl(config.indexer_url || "");
      setIndexerUsername(config.indexer_username || "");
      setPasswordConfigured(config.password_configured);
      setIndexerPasswordConfigured(config.indexer_password_configured);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erreur de chargement");
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const handleSave = async () => {
    setSaving(true);
    setMessage(null);
    setError(null);
    try {
      const payload: Record<string, unknown> = {
        base_url: baseUrl,
        username,
        verify_ssl: verifySsl,
        enabled,
        indexer_url: indexerUrl,
        indexer_username: indexerUsername,
      };
      if (password) payload.password = password;
      if (indexerPassword) payload.indexer_password = indexerPassword;
      await saveWazuhConfig(payload);
      setMessage("Configuration enregistrée.");
      setPassword("");
      setIndexerPassword("");
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erreur d'enregistrement");
    } finally {
      setSaving(false);
    }
  };

  const handleTest = async () => {
    setTesting(true);
    setTestResult(null);
    setError(null);
    try {
      if (password || baseUrl !== "" || username !== "") {
        await saveWazuhConfig({
          base_url: baseUrl,
          username,
          verify_ssl: verifySsl,
          enabled,
          indexer_url: indexerUrl,
          indexer_username: indexerUsername,
          ...(password ? { password } : {}),
          ...(indexerPassword ? { indexer_password: indexerPassword } : {}),
        });
      }
      const result = await testWazuhConnection();
      setTestResult(result);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Test de connexion échoué");
    } finally {
      setTesting(false);
    }
  };

  return (
    <div className="wazuh-page wazuh-settings">
      <header className="wazuh-header">
        <div>
          <p className="wazuh-eyebrow">Paramètres → Connecteurs</p>
          <h1>Wazuh</h1>
        </div>
        <Link to="/soc/wazuh" className="wazuh-btn wazuh-btn-ghost">
          Retour au tableau de bord
        </Link>
      </header>

      {error && <div className="wazuh-error">{error}</div>}
      {message && <div className="wazuh-banner wazuh-banner-ok">{message}</div>}

      <form
        className="wazuh-settings-form"
        onSubmit={(e) => {
          e.preventDefault();
          handleSave();
        }}
      >
        <label className="wazuh-field">
          <span>URL API Wazuh</span>
          <input
            type="url"
            placeholder="https://wazuh.example.com:55000"
            value={baseUrl}
            onChange={(e) => setBaseUrl(e.target.value)}
            required
          />
          <small>API Manager Wazuh (port 55000). Les alertes utilisent l&apos;indexer (port 9200).</small>
        </label>

        <label className="wazuh-field">
          <span>URL Indexer (optionnel)</span>
          <input
            type="url"
            placeholder="https://localhost:9200"
            value={indexerUrl}
            onChange={(e) => setIndexerUrl(e.target.value)}
          />
          <small>Dérivée automatiquement du port 55000 si vide.</small>
        </label>

        <label className="wazuh-field">
          <span>Utilisateur API Manager</span>
          <input
            type="text"
            autoComplete="username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
          />
        </label>

        <label className="wazuh-field">
          <span>Mot de passe API Manager</span>
          <input
            type="password"
            autoComplete="current-password"
            placeholder={passwordConfigured ? "•••••••• (inchangé si vide)" : ""}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </label>

        <label className="wazuh-field">
          <span>Utilisateur Indexer (optionnel)</span>
          <input
            type="text"
            autoComplete="off"
            placeholder="admin"
            value={indexerUsername}
            onChange={(e) => setIndexerUsername(e.target.value)}
          />
          <small>
            Identifiants dashboard/indexer pour les alertes (souvent admin), distincts de wazuh-wui.
          </small>
        </label>

        <label className="wazuh-field">
          <span>Mot de passe Indexer (optionnel)</span>
          <input
            type="password"
            autoComplete="new-password"
            placeholder={indexerPasswordConfigured ? "•••••••• (inchangé si vide)" : ""}
            value={indexerPassword}
            onChange={(e) => setIndexerPassword(e.target.value)}
          />
        </label>

        <label className="wazuh-field wazuh-field-checkbox">
          <input
            type="checkbox"
            checked={verifySsl}
            onChange={(e) => setVerifySsl(e.target.checked)}
          />
          <span>Vérification SSL</span>
        </label>

        <label className="wazuh-field wazuh-field-checkbox">
          <input
            type="checkbox"
            checked={enabled}
            onChange={(e) => setEnabled(e.target.checked)}
          />
          <span>Activer le connecteur</span>
        </label>

        <div className="wazuh-settings-actions">
          <button type="submit" className="wazuh-btn" disabled={saving}>
            {saving ? "Enregistrement…" : "Enregistrer"}
          </button>
          <button
            type="button"
            className="wazuh-btn wazuh-btn-secondary"
            disabled={testing}
            onClick={handleTest}
          >
            {testing ? "Test en cours…" : "Tester la connexion"}
          </button>
        </div>
      </form>

      {testResult && (
        <div
          className={`wazuh-test-result ${testResult.success ? "wazuh-test-ok" : "wazuh-test-ko"}`}
        >
          {testResult.success ? (
            <>
              <strong>Connexion réussie</strong>
              <ul>
                {testResult.wazuh_version && <li>Version Wazuh : {testResult.wazuh_version}</li>}
                {testResult.api_version && <li>Version API : {testResult.api_version}</li>}
                {testResult.manager && <li>Manager : {testResult.manager}</li>}
                {testResult.agents_total != null && (
                  <li>Agents détectés : {testResult.agents_total}</li>
                )}
              </ul>
            </>
          ) : (
            <>
              <strong>Échec de connexion</strong>
              <p>{testResult.error}</p>
            </>
          )}
        </div>
      )}
    </div>
  );
}
