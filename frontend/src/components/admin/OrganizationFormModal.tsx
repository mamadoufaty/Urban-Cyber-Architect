import { useEffect, useState } from "react";
import type { AdminOrganization } from "../../api";

export type OrganizationFormValues = {
  name: string;
  code: string;
  description: string;
  status: string;
};

type OrganizationFormModalProps = {
  open: boolean;
  mode: "create" | "edit";
  organization: AdminOrganization | null;
  saving: boolean;
  error: string | null;
  onClose: () => void;
  onSubmit: (values: OrganizationFormValues) => void;
};

const EMPTY_FORM: OrganizationFormValues = {
  name: "",
  code: "",
  description: "",
  status: "active",
};

function orgToForm(org: AdminOrganization): OrganizationFormValues {
  return {
    name: org.name,
    code: org.code,
    description: org.description ?? "",
    status: org.status,
  };
}

export default function OrganizationFormModal({
  open,
  mode,
  organization,
  saving,
  error,
  onClose,
  onSubmit,
}: OrganizationFormModalProps) {
  const [form, setForm] = useState<OrganizationFormValues>(EMPTY_FORM);
  const [localError, setLocalError] = useState<string | null>(null);

  useEffect(() => {
    if (!open) return;
    setLocalError(null);
    setForm(mode === "edit" && organization ? orgToForm(organization) : EMPTY_FORM);
  }, [open, mode, organization]);

  if (!open) return null;

  function updateField<K extends keyof OrganizationFormValues>(
    key: K,
    value: OrganizationFormValues[K]
  ) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLocalError(null);
    if (!form.name.trim()) {
      setLocalError("Le nom est obligatoire.");
      return;
    }
    if (!form.code.trim()) {
      setLocalError("Le code est obligatoire.");
      return;
    }
    onSubmit(form);
  }

  const displayError = localError ?? error;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-card modal-card-wide" onClick={(e) => e.stopPropagation()}>
        <h3>{mode === "create" ? "Nouvelle organisation" : "Modifier l'organisation"}</h3>
        {displayError && (
          <div className="admin-users-error" role="alert">
            {displayError}
          </div>
        )}
        <form onSubmit={handleSubmit}>
          <div className="admin-user-form-grid">
            <div className="form-group">
              <label htmlFor="org-name">Nom *</label>
              <input
                id="org-name"
                value={form.name}
                onChange={(e) => updateField("name", e.target.value)}
                required
              />
            </div>
            <div className="form-group">
              <label htmlFor="org-code">Code *</label>
              <input
                id="org-code"
                value={form.code}
                onChange={(e) => updateField("code", e.target.value)}
                disabled={mode === "edit"}
                required
              />
            </div>
            <div className="form-group full-width">
              <label htmlFor="org-description">Description</label>
              <textarea
                id="org-description"
                value={form.description}
                onChange={(e) => updateField("description", e.target.value)}
                rows={3}
              />
            </div>
            <div className="form-group">
              <label htmlFor="org-status">Statut</label>
              <select
                id="org-status"
                value={form.status}
                onChange={(e) => updateField("status", e.target.value)}
              >
                <option value="active">Actif</option>
                <option value="archived">Archivé</option>
              </select>
            </div>
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
