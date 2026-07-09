import { useEffect, useState } from "react";
import type { Referential } from "../../api";

export type ReferentialFormValues = {
  label: string;
  category: string;
  description: string;
  status: string;
};

type ReferentialFormModalProps = {
  open: boolean;
  mode: "create" | "edit";
  referential: Referential | null;
  saving: boolean;
  error: string | null;
  onClose: () => void;
  onSubmit: (values: ReferentialFormValues) => void;
};

const EMPTY_FORM: ReferentialFormValues = {
  label: "",
  category: "",
  description: "",
  status: "active",
};

function toForm(ref: Referential): ReferentialFormValues {
  return {
    label: ref.label,
    category: ref.category ?? "",
    description: ref.description ?? "",
    status: ref.status,
  };
}

export default function ReferentialFormModal({
  open,
  mode,
  referential,
  saving,
  error,
  onClose,
  onSubmit,
}: ReferentialFormModalProps) {
  const [form, setForm] = useState<ReferentialFormValues>(EMPTY_FORM);
  const [localError, setLocalError] = useState<string | null>(null);

  useEffect(() => {
    if (!open) return;
    setLocalError(null);
    setForm(mode === "edit" && referential ? toForm(referential) : EMPTY_FORM);
  }, [open, mode, referential]);

  if (!open) return null;

  function updateField<K extends keyof ReferentialFormValues>(
    key: K,
    value: ReferentialFormValues[K],
  ) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLocalError(null);
    if (!form.label.trim()) {
      setLocalError("Le libellé est obligatoire.");
      return;
    }
    onSubmit(form);
  }

  const displayError = localError ?? error;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-card modal-card-wide" onClick={(e) => e.stopPropagation()}>
        <h3>{mode === "create" ? "Nouveau référentiel" : "Modifier le référentiel"}</h3>
        {displayError && (
          <div className="admin-users-error" role="alert">
            {displayError}
          </div>
        )}
        <form onSubmit={handleSubmit}>
          <div className="admin-user-form-grid">
            <div className="form-group">
              <label htmlFor="ref-label">Libellé *</label>
              <input
                id="ref-label"
                value={form.label}
                onChange={(e) => updateField("label", e.target.value)}
                placeholder="ISO 27001"
                required
              />
            </div>
            <div className="form-group">
              <label htmlFor="ref-category">Catégorie</label>
              <input
                id="ref-category"
                value={form.category}
                onChange={(e) => updateField("category", e.target.value)}
                placeholder="Système de management"
              />
            </div>
            <div className="form-group full-width">
              <label htmlFor="ref-description">Description</label>
              <textarea
                id="ref-description"
                value={form.description}
                onChange={(e) => updateField("description", e.target.value)}
                rows={3}
              />
            </div>
            <div className="form-group">
              <label htmlFor="ref-status">Statut</label>
              <select
                id="ref-status"
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
