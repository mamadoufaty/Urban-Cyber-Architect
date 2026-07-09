import { useEffect, useState } from "react";
import { validateDuplicateName } from "./cartographySelect";

type NameCartographyModalProps = {
  open: boolean;
  mode: "duplicate" | "save-as";
  sourceName: string;
  existingNames: string[];
  saving: boolean;
  error: string | null;
  onClose: () => void;
  onSubmit: (name: string) => void;
};

export default function NameCartographyModal({
  open,
  mode,
  sourceName,
  existingNames,
  saving,
  error,
  onClose,
  onSubmit,
}: NameCartographyModalProps) {
  const [name, setName] = useState("");
  const [localError, setLocalError] = useState<string | null>(null);

  useEffect(() => {
    if (!open) return;
    setName(`${sourceName} (copie)`);
    setLocalError(null);
  }, [open, sourceName]);

  if (!open) return null;

  const title = mode === "save-as" ? "Enregistrer sous…" : "Dupliquer la cartographie";
  const submitLabel = mode === "save-as" ? "Enregistrer" : "Dupliquer";

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const validationError = validateDuplicateName(name, existingNames);
    if (validationError) {
      setLocalError(validationError);
      return;
    }
    onSubmit(name.trim());
  }

  const displayError = localError ?? error;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-card" onClick={(e) => e.stopPropagation()}>
        <h3>{title}</h3>
        <p className="cartography-modal-hint">
          Le nouveau graphe sera une copie complète et totalement indépendante de « {sourceName} ».
        </p>
        {displayError && (
          <div className="admin-users-error" role="alert">
            {displayError}
          </div>
        )}
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="nc-name">Nom *</label>
            <input
              id="nc-name"
              value={name}
              onChange={(e) => {
                setName(e.target.value);
                setLocalError(null);
              }}
              required
              autoFocus
            />
          </div>
          <div className="modal-actions">
            <button type="button" className="btn btn-secondary" onClick={onClose} disabled={saving}>
              Annuler
            </button>
            <button type="submit" className="btn btn-primary" disabled={saving}>
              {saving ? "Enregistrement…" : submitLabel}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
