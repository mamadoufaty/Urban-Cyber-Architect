import { FormEvent, useEffect, useState } from "react";
import type { DeliverableGenerateRequest, DeliverableTypeOption } from "../../api";

const DATA_SOURCE_LABELS: Record<string, string> = {
  urbanism: "Urbanisme",
  ebios: "EBIOS RM",
  grc: "GRC",
  soc: "SOC",
  wazuh: "Wazuh",
  ai: "IA",
};

type Props = {
  open: boolean;
  types: DeliverableTypeOption[];
  onClose: () => void;
  onSubmit: (payload: DeliverableGenerateRequest, action: "generate" | "preview") => Promise<void>;
  busy: boolean;
};

export default function CreateDeliverableModal({ open, types, onClose, onSubmit, busy }: Props) {
  const [title, setTitle] = useState("");
  const [deliverableType, setDeliverableType] = useState("project_management_plan");
  const [userNeed, setUserNeed] = useState("");
  const [exportFormat, setExportFormat] = useState<"pdf" | "docx" | "markdown">("pdf");
  const [sources, setSources] = useState<Record<string, boolean>>({
    urbanism: true,
    ebios: true,
    grc: true,
    soc: false,
    wazuh: false,
    ai: false,
  });

  useEffect(() => {
    if (!open) return;
    setTitle("");
    setDeliverableType("project_management_plan");
    setUserNeed("");
    setExportFormat("pdf");
    setSources({
      urbanism: true,
      ebios: true,
      grc: true,
      soc: false,
      wazuh: false,
      ai: false,
    });
  }, [open]);

  if (!open) return null;

  const buildPayload = (): DeliverableGenerateRequest => ({
    title: title.trim(),
    deliverable_type: deliverableType,
    user_need: userNeed,
    data_sources: Object.entries(sources)
      .filter(([, checked]) => checked)
      .map(([key]) => key),
    export_format: exportFormat,
  });

  const handleSubmit = async (event: FormEvent, action: "generate" | "preview") => {
    event.preventDefault();
    await onSubmit({ ...buildPayload(), preview: action === "preview" }, action);
  };

  return (
    <div className="livrables-modal-backdrop" role="presentation" onClick={onClose}>
      <div
        className="livrables-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="livrables-modal-title"
        onClick={(e) => e.stopPropagation()}
      >
        <header className="livrables-modal-header">
          <h2 id="livrables-modal-title">Nouveau livrable</h2>
          <button type="button" className="livrables-modal-close" onClick={onClose} aria-label="Fermer">
            ×
          </button>
        </header>

        <form className="livrables-modal-form">
          <label className="livrables-field">
            <span>Titre du livrable</span>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Plan de management de projet Métropolis"
              required
            />
          </label>

          <label className="livrables-field">
            <span>Type de livrable</span>
            <select value={deliverableType} onChange={(e) => setDeliverableType(e.target.value)}>
              {types.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.label}
                </option>
              ))}
            </select>
          </label>

          <label className="livrables-field">
            <span>Besoin utilisateur</span>
            <textarea
              value={userNeed}
              onChange={(e) => setUserNeed(e.target.value)}
              rows={6}
              placeholder="Décrivez librement le livrable attendu…"
            />
          </label>

          <fieldset className="livrables-fieldset">
            <legend>Données à utiliser</legend>
            <div className="livrables-checkboxes">
              {Object.entries(DATA_SOURCE_LABELS).map(([key, label]) => (
                <label key={key} className="livrables-checkbox">
                  <input
                    type="checkbox"
                    checked={Boolean(sources[key])}
                    onChange={(e) => setSources((prev) => ({ ...prev, [key]: e.target.checked }))}
                  />
                  <span>{label}</span>
                </label>
              ))}
            </div>
          </fieldset>

          <fieldset className="livrables-fieldset">
            <legend>Format</legend>
            <div className="livrables-format-row">
              {(["pdf", "docx", "markdown"] as const).map((fmt) => (
                <label key={fmt} className="livrables-radio">
                  <input
                    type="radio"
                    name="export_format"
                    value={fmt}
                    checked={exportFormat === fmt}
                    onChange={() => setExportFormat(fmt)}
                  />
                  <span>{fmt.toUpperCase()}</span>
                </label>
              ))}
            </div>
          </fieldset>

          <div className="livrables-modal-actions">
            <button
              type="button"
              className="livrables-btn livrables-btn-secondary"
              disabled={busy || !title.trim()}
              onClick={(e) => handleSubmit(e, "preview")}
            >
              Prévisualiser
            </button>
            <button
              type="button"
              className="livrables-btn"
              disabled={busy || !title.trim()}
              onClick={(e) => handleSubmit(e, "generate")}
            >
              {busy ? "Génération…" : "Générer"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
