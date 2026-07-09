import { useEffect, useState } from "react";
import { CARTOGRAPHY_TYPES } from "../../api";
import { type CartographyCreateInput, validateCartographyCreateInput } from "./cartographySelect";

type CreateCartographyModalProps = {
  open: boolean;
  saving: boolean;
  error: string | null;
  onClose: () => void;
  onSubmit: (values: CartographyCreateInput) => void;
};

const EMPTY: CartographyCreateInput = { name: "", type: "libre", description: "" };

export default function CreateCartographyModal({
  open,
  saving,
  error,
  onClose,
  onSubmit,
}: CreateCartographyModalProps) {
  const [form, setForm] = useState<CartographyCreateInput>(EMPTY);
  const [localError, setLocalError] = useState<string | null>(null);

  useEffect(() => {
    if (!open) return;
    setForm(EMPTY);
    setLocalError(null);
  }, [open]);

  if (!open) return null;

  function updateField<K extends keyof CartographyCreateInput>(key: K, value: CartographyCreateInput[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
    setLocalError(null);
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const validationError = validateCartographyCreateInput(form);
    if (validationError) {
      setLocalError(validationError);
      return;
    }
    onSubmit(form);
  }

  const displayError = localError ?? error;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-card" onClick={(e) => e.stopPropagation()}>
        <h3>Nouvelle cartographie</h3>
        {displayError && (
          <div className="admin-users-error" role="alert">
            {displayError}
          </div>
        )}
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="cc-name">Nom *</label>
            <input
              id="cc-name"
              value={form.name}
              onChange={(e) => updateField("name", e.target.value)}
              placeholder="Urbanisme Technique"
              required
              autoFocus
            />
          </div>
          <div className="form-group">
            <label htmlFor="cc-type">Type</label>
            <select id="cc-type" value={form.type} onChange={(e) => updateField("type", e.target.value)}>
              {CARTOGRAPHY_TYPES.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.label}
                </option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label htmlFor="cc-description">Description</label>
            <textarea
              id="cc-description"
              value={form.description}
              onChange={(e) => updateField("description", e.target.value)}
              rows={2}
            />
          </div>
          <div className="form-group">
            <label>Version initiale</label>
            <input value="1.0" disabled />
          </div>
          <div className="modal-actions">
            <button type="button" className="btn btn-secondary" onClick={onClose} disabled={saving}>
              Annuler
            </button>
            <button type="submit" className="btn btn-primary" disabled={saving}>
              {saving ? "Création…" : "Créer"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
