import { useEffect, useState } from "react";
import type { AdminUser } from "../../api";

type ResetPasswordModalProps = {
  open: boolean;
  user: AdminUser | null;
  saving: boolean;
  error: string | null;
  onClose: () => void;
  onSubmit: (password: string) => void;
};

export default function ResetPasswordModal({
  open,
  user,
  saving,
  error,
  onClose,
  onSubmit,
}: ResetPasswordModalProps) {
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [localError, setLocalError] = useState<string | null>(null);

  useEffect(() => {
    if (!open) return;
    setPassword("");
    setConfirm("");
    setLocalError(null);
  }, [open, user?.id]);

  if (!open || !user) return null;

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLocalError(null);
    if (password.length < 6) {
      setLocalError("Le mot de passe doit contenir au moins 6 caractères.");
      return;
    }
    if (password !== confirm) {
      setLocalError("Les mots de passe ne correspondent pas.");
      return;
    }
    onSubmit(password);
  }

  const displayError = localError ?? error;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-card" onClick={(e) => e.stopPropagation()}>
        <h3>Réinitialiser le mot de passe</h3>
        <p className="admin-modal-subtitle">Utilisateur : {user.username}</p>
        {displayError && (
          <div className="admin-users-error" role="alert">
            {displayError}
          </div>
        )}
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="reset-password">Nouveau mot de passe</label>
            <input
              id="reset-password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="new-password"
            />
          </div>
          <div className="form-group">
            <label htmlFor="reset-password-confirm">Confirmation</label>
            <input
              id="reset-password-confirm"
              type="password"
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
              autoComplete="new-password"
            />
          </div>
          <div className="modal-actions">
            <button type="button" className="btn btn-secondary" onClick={onClose} disabled={saving}>
              Annuler
            </button>
            <button type="submit" className="btn btn-primary" disabled={saving}>
              {saving ? "Enregistrement…" : "Réinitialiser"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
