import { useEffect, useState } from "react";
import type { Referential } from "../../api";
import {
  type QuickAddReferentialValues,
  validateQuickAddReferential,
} from "../../projects/referentialSelect";

type QuickAddReferentialModalProps = {
  open: boolean;
  saving: boolean;
  error: string | null;
  /** Référentiels existants — utilisés pour un contrôle immédiat des doublons de code. */
  existing: Referential[];
  onClose: () => void;
  onSubmit: (values: QuickAddReferentialValues) => void;
};

const EMPTY_FORM: QuickAddReferentialValues = {
  label: "",
  code: "",
  description: "",
  status: "active",
};

export default function QuickAddReferentialModal({
  open,
  saving,
  error,
  existing,
  onClose,
  onSubmit,
}: QuickAddReferentialModalProps) {
  const [form, setForm] = useState<QuickAddReferentialValues>(EMPTY_FORM);
  const [localError, setLocalError] = useState<string | null>(null);

  useEffect(() => {
    if (!open) return;
    setForm(EMPTY_FORM);
    setLocalError(null);
  }, [open]);

  if (!open) return null;

  function updateField<K extends keyof QuickAddReferentialValues>(
    key: K,
    value: QuickAddReferentialValues[K],
  ) {
    setForm((prev) => ({ ...prev, [key]: value }));
    setLocalError(null);
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const validationError = validateQuickAddReferential(form, existing);
    if (validationError) {
      setLocalError(validationError);
      return;
    }
    setLocalError(null);
    onSubmit(form);
  }

  const displayError = localError ?? error;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div
        className="modal-card quick-add-referential-modal"
        onClick={(e) => e.stopPropagation()}
      >
        <h3>Ajouter un référentiel</h3>
        {displayError && (
          <div className="admin-users-error" role="alert">
            {displayError}
          </div>
        )}
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="qar-label">Nom *</label>
            <input
              id="qar-label"
              value={form.label}
              onChange={(e) => updateField("label", e.target.value)}
              placeholder="ISO 42001"
              required
              autoFocus
            />
          </div>
          <div className="form-group">
            <label htmlFor="qar-code">Code *</label>
            <input
              id="qar-code"
              value={form.code}
              onChange={(e) => updateField("code", e.target.value)}
              placeholder="iso-42001"
              required
            />
          </div>
          <div className="form-group">
            <label htmlFor="qar-description">Description</label>
            <textarea
              id="qar-description"
              value={form.description}
              onChange={(e) => updateField("description", e.target.value)}
              rows={2}
            />
          </div>
          <div className="form-group">
            <label htmlFor="qar-status">Statut</label>
            <select
              id="qar-status"
              value={form.status}
              onChange={(e) => updateField("status", e.target.value)}
            >
              <option value="active">Actif</option>
              <option value="archived">Inactif</option>
            </select>
          </div>
          <div className="modal-actions">
            <button type="button" className="btn btn-secondary" onClick={onClose} disabled={saving}>
              Annuler
            </button>
            <button type="submit" className="btn btn-primary" disabled={saving}>
              {saving ? "Enregistrement…" : "Ajouter"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
