import { useEffect, useState } from "react";
import type { AdminOrganization, AdminRole, AdminUser } from "../../api";

export type UserFormValues = {
  last_name: string;
  first_name: string;
  username: string;
  email: string;
  phone: string;
  organization_id: string;
  function: string;
  role_id: string;
  password: string;
  password_confirm: string;
  status: string;
};

type UserFormModalProps = {
  open: boolean;
  mode: "create" | "edit";
  user: AdminUser | null;
  roles: AdminRole[];
  organizations: AdminOrganization[];
  saving: boolean;
  error: string | null;
  onClose: () => void;
  onSubmit: (values: UserFormValues) => void;
};

const EMPTY_FORM: UserFormValues = {
  last_name: "",
  first_name: "",
  username: "",
  email: "",
  phone: "",
  organization_id: "",
  function: "",
  role_id: "",
  password: "",
  password_confirm: "",
  status: "active",
};

function userToForm(user: AdminUser): UserFormValues {
  return {
    last_name: user.last_name ?? "",
    first_name: user.first_name ?? "",
    username: user.username,
    email: user.email ?? "",
    phone: user.phone ?? "",
    organization_id: user.organization_id ?? "",
    function: user.function ?? "",
    role_id: user.role_id ?? "",
    password: "",
    password_confirm: "",
    status: user.status,
  };
}

export default function UserFormModal({
  open,
  mode,
  user,
  roles,
  organizations,
  saving,
  error,
  onClose,
  onSubmit,
}: UserFormModalProps) {
  const [form, setForm] = useState<UserFormValues>(EMPTY_FORM);
  const [localError, setLocalError] = useState<string | null>(null);

  useEffect(() => {
    if (!open) return;
    setLocalError(null);
    setForm(mode === "edit" && user ? userToForm(user) : EMPTY_FORM);
  }, [open, mode, user]);

  if (!open) return null;

  function updateField<K extends keyof UserFormValues>(key: K, value: UserFormValues[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLocalError(null);
    if (!form.username.trim()) {
      setLocalError("Le nom d'utilisateur est obligatoire.");
      return;
    }
    if (mode === "create") {
      if (!form.password || form.password.length < 6) {
        setLocalError("Le mot de passe doit contenir au moins 6 caractères.");
        return;
      }
      if (form.password !== form.password_confirm) {
        setLocalError("Les mots de passe ne correspondent pas.");
        return;
      }
    }
    onSubmit(form);
  }

  const displayError = localError ?? error;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-card modal-card-wide" onClick={(e) => e.stopPropagation()}>
        <h3>{mode === "create" ? "Nouvel utilisateur" : "Modifier l'utilisateur"}</h3>
        <p className="admin-modal-subtitle">
          {mode === "create"
            ? "Créez un compte avec rôle et organisation."
            : `Compte : ${user?.username ?? ""}`}
        </p>
        {displayError && (
          <div className="admin-users-error" role="alert">
            {displayError}
          </div>
        )}
        <form onSubmit={handleSubmit}>
          <div className="admin-user-form-grid">
            <div className="form-group">
              <label htmlFor="user-last-name">Nom</label>
              <input
                id="user-last-name"
                value={form.last_name}
                onChange={(e) => updateField("last_name", e.target.value)}
              />
            </div>
            <div className="form-group">
              <label htmlFor="user-first-name">Prénom</label>
              <input
                id="user-first-name"
                value={form.first_name}
                onChange={(e) => updateField("first_name", e.target.value)}
              />
            </div>
            <div className="form-group">
              <label htmlFor="user-username">Nom d'utilisateur *</label>
              <input
                id="user-username"
                value={form.username}
                onChange={(e) => updateField("username", e.target.value)}
                disabled={mode === "edit"}
                required
              />
            </div>
            <div className="form-group">
              <label htmlFor="user-email">Email</label>
              <input
                id="user-email"
                type="email"
                value={form.email}
                onChange={(e) => updateField("email", e.target.value)}
              />
            </div>
            <div className="form-group">
              <label htmlFor="user-phone">Téléphone</label>
              <input
                id="user-phone"
                value={form.phone}
                onChange={(e) => updateField("phone", e.target.value)}
              />
            </div>
            <div className="form-group">
              <label htmlFor="user-organization">Organisation</label>
              <select
                id="user-organization"
                value={form.organization_id}
                onChange={(e) => updateField("organization_id", e.target.value)}
              >
                <option value="">— Aucune —</option>
                {organizations.map((org) => (
                  <option key={org.id} value={org.id}>
                    {org.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="form-group">
              <label htmlFor="user-function">Fonction</label>
              <input
                id="user-function"
                value={form.function}
                onChange={(e) => updateField("function", e.target.value)}
              />
            </div>
            <div className="form-group">
              <label htmlFor="user-role">Rôle</label>
              <select
                id="user-role"
                value={form.role_id}
                onChange={(e) => updateField("role_id", e.target.value)}
              >
                <option value="">— Aucun —</option>
                {roles.map((role) => (
                  <option key={role.id} value={role.id}>
                    {role.name} ({role.code})
                  </option>
                ))}
              </select>
            </div>
            <div className="form-group">
              <label htmlFor="user-status">Statut</label>
              <select
                id="user-status"
                value={form.status}
                onChange={(e) => updateField("status", e.target.value)}
              >
                <option value="active">Actif</option>
                <option value="disabled">Désactivé</option>
              </select>
            </div>
            {mode === "create" && (
              <>
                <div className="form-group">
                  <label htmlFor="user-password">Mot de passe *</label>
                  <input
                    id="user-password"
                    type="password"
                    value={form.password}
                    onChange={(e) => updateField("password", e.target.value)}
                    autoComplete="new-password"
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="user-password-confirm">Confirmation *</label>
                  <input
                    id="user-password-confirm"
                    type="password"
                    value={form.password_confirm}
                    onChange={(e) => updateField("password_confirm", e.target.value)}
                    autoComplete="new-password"
                  />
                </div>
              </>
            )}
          </div>
          <div className="modal-actions">
            <button type="button" className="btn btn-secondary" onClick={onClose} disabled={saving}>
              Annuler
            </button>
            <button type="submit" className="btn btn-primary" disabled={saving}>
              {saving ? "Enregistrement…" : mode === "create" ? "Créer" : "Enregistrer"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
