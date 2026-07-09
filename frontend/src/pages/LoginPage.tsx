import { FormEvent, useEffect, useState } from "react";
import { Navigate, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { bootstrapAdmin, fetchBootstrapStatus, type BootstrapStatus } from "../auth/authService";

export default function LoginPage() {
  const { isAuthenticated, isLoading, login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [bootstrapStatus, setBootstrapStatus] = useState<BootstrapStatus | null>(null);
  const [showBootstrap, setShowBootstrap] = useState(false);
  const [bootstrapForm, setBootstrapForm] = useState({
    first_name: "",
    last_name: "",
    email: "",
    username: "admin",
    password: "",
    confirm: "",
  });
  const [bootstrapError, setBootstrapError] = useState<string | null>(null);
  const [bootstrapSuccess, setBootstrapSuccess] = useState<string | null>(null);

  const redirectTo =
    (location.state as { from?: string } | null)?.from && (location.state as { from?: string }).from !== "/login"
      ? (location.state as { from: string }).from
      : "/";

  useEffect(() => {
    fetchBootstrapStatus().then(setBootstrapStatus).catch(() => null);
  }, []);

  const recoveryAvailable =
    bootstrapStatus?.needs_bootstrap === true && bootstrapStatus.bootstrap_enabled === true;

  useEffect(() => {
    if (recoveryAvailable) setShowBootstrap(true);
  }, [recoveryAvailable]);

  if (!isLoading && isAuthenticated) {
    return <Navigate to={redirectTo} replace />;
  }

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login(username, password);
      navigate(redirectTo, { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Connexion impossible.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleBootstrap = async (event: FormEvent) => {
    event.preventDefault();
    setBootstrapError(null);
    setBootstrapSuccess(null);
    if (bootstrapForm.password !== bootstrapForm.confirm) {
      setBootstrapError("Les mots de passe ne correspondent pas.");
      return;
    }
    setSubmitting(true);
    try {
      await bootstrapAdmin({
        username: bootstrapForm.username.trim(),
        password: bootstrapForm.password,
        first_name: bootstrapForm.first_name || undefined,
        last_name: bootstrapForm.last_name || undefined,
        email: bootstrapForm.email || undefined,
      });
      setBootstrapSuccess("Administrateur créé. Vous pouvez vous connecter.");
      setShowBootstrap(false);
      setUsername(bootstrapForm.username.trim());
      setPassword("");
      const status = await fetchBootstrapStatus();
      setBootstrapStatus(status);
    } catch (err) {
      setBootstrapError(err instanceof Error ? err.message : "Création impossible.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-card">
        <header className="login-header">
          <h1>Urban Cyber Architect</h1>
          <p>Connexion à la plateforme</p>
        </header>

        {recoveryAvailable && (
          <div className="login-bootstrap-alert" role="alert">
            <strong>{bootstrapStatus?.message ?? "Aucun administrateur détecté."}</strong>
            {!showBootstrap && (
              <button
                type="button"
                className="login-bootstrap-toggle"
                onClick={() => setShowBootstrap(true)}
              >
                Créer un administrateur
              </button>
            )}
          </div>
        )}

        {bootstrapSuccess && (
          <div className="login-bootstrap-success" role="status">
            {bootstrapSuccess}
          </div>
        )}

        {showBootstrap && recoveryAvailable ? (
          <form className="login-form" onSubmit={handleBootstrap}>
            <h2 className="login-bootstrap-title">Créer un administrateur</h2>
            {bootstrapError && (
              <div className="login-error" role="alert">
                {bootstrapError}
              </div>
            )}
            <label className="login-field">
              <span>Prénom</span>
              <input
                value={bootstrapForm.first_name}
                onChange={(e) => setBootstrapForm((f) => ({ ...f, first_name: e.target.value }))}
              />
            </label>
            <label className="login-field">
              <span>Nom</span>
              <input
                value={bootstrapForm.last_name}
                onChange={(e) => setBootstrapForm((f) => ({ ...f, last_name: e.target.value }))}
              />
            </label>
            <label className="login-field">
              <span>Email</span>
              <input
                type="email"
                value={bootstrapForm.email}
                onChange={(e) => setBootstrapForm((f) => ({ ...f, email: e.target.value }))}
              />
            </label>
            <label className="login-field">
              <span>Login</span>
              <input
                required
                value={bootstrapForm.username}
                onChange={(e) => setBootstrapForm((f) => ({ ...f, username: e.target.value }))}
              />
            </label>
            <label className="login-field">
              <span>Mot de passe</span>
              <input
                type="password"
                required
                value={bootstrapForm.password}
                onChange={(e) => setBootstrapForm((f) => ({ ...f, password: e.target.value }))}
              />
            </label>
            <label className="login-field">
              <span>Confirmer le mot de passe</span>
              <input
                type="password"
                required
                value={bootstrapForm.confirm}
                onChange={(e) => setBootstrapForm((f) => ({ ...f, confirm: e.target.value }))}
              />
            </label>
            <button type="submit" className="login-submit" disabled={submitting}>
              {submitting ? "Création…" : "Créer l'administrateur"}
            </button>
          </form>
        ) : (
          <form className="login-form" onSubmit={handleSubmit}>
            {error && (
              <div className="login-error" role="alert">
                {error}
              </div>
            )}

            <label className="login-field">
              <span>Identifiant</span>
              <input
                type="text"
                autoComplete="username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
              />
            </label>

            <label className="login-field">
              <span>Mot de passe</span>
              <input
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </label>

            <button type="submit" className="login-submit" disabled={submitting}>
              {submitting ? "Connexion…" : "Se connecter"}
            </button>
          </form>
        )}

        <footer className="login-hint">
          <p>Utilisez un compte créé dans Administration ou les comptes initiaux (admin, admin1, …).</p>
        </footer>
      </div>
    </div>
  );
}
