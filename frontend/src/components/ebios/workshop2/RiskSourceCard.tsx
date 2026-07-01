import { useState } from "react";
import type { EbiosRecord } from "../types";
import RecordFormModal, {
  FormField,
  FormInput,
  FormSelect,
  FormTextarea,
} from "../workshop1/RecordFormModal";
import {
  EMPTY_RISK_SOURCE,
  SEVERITY_CLASS,
  SEVERITY_LEVELS,
  isRiskSourceComplete,
  riskSourceFromRecord,
  type RiskSourceFormData,
} from "./constants";

type Props = {
  records: EbiosRecord[];
  stakeholders: EbiosRecord[];
  supportingAssets: EbiosRecord[];
  onSave: (data: RiskSourceFormData, existingId?: string) => Promise<void>;
  onDelete: (id: string) => Promise<void>;
};

function MultiSelect({
  options,
  selected,
  onChange,
  emptyLabel,
}: {
  options: { id: string; label: string; hint?: string }[];
  selected: string[];
  onChange: (ids: string[]) => void;
  emptyLabel: string;
}) {
  if (!options.length) {
    return <p className="eb-form-hint">{emptyLabel}</p>;
  }
  const toggle = (id: string) => {
    if (selected.includes(id)) onChange(selected.filter((x) => x !== id));
    else onChange([...selected, id]);
  };
  return (
    <div className="eb-multi-select">
      {options.map((opt) => (
        <label key={opt.id} className="eb-multi-select-item">
          <input
            type="checkbox"
            checked={selected.includes(opt.id)}
            onChange={() => toggle(opt.id)}
          />
          <span>
            <strong>{opt.label}</strong>
            {opt.hint ? <small>{opt.hint}</small> : null}
          </span>
        </label>
      ))}
    </div>
  );
}

export default function RiskSourceCard({
  records,
  stakeholders,
  supportingAssets,
  onSave,
  onDelete,
}: Props) {
  const items = records.filter((r) => r.record_type === "risk_source");
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [editId, setEditId] = useState<string | undefined>();
  const [form, setForm] = useState<RiskSourceFormData>(EMPTY_RISK_SOURCE);

  const stakeholderOptions = stakeholders.map((s) => ({
    id: s.id,
    label: s.label,
    hint: s.properties.role ? String(s.properties.role) : undefined,
  }));

  const assetOptions = supportingAssets.map((a) => ({
    id: a.id,
    label: a.label,
    hint: a.properties.entity_type ? String(a.properties.entity_type) : undefined,
  }));

  const openCreate = () => {
    setEditId(undefined);
    setForm(EMPTY_RISK_SOURCE);
    setOpen(true);
  };

  const openEdit = (record: EbiosRecord) => {
    setEditId(record.id);
    setForm(riskSourceFromRecord(record));
    setOpen(true);
  };

  const handleSubmit = async () => {
    if (!form.label.trim() || !form.feared_event.trim()) return;
    setBusy(true);
    try {
      await onSave(form, editId);
      setOpen(false);
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="eb-card eb-card-wide">
      <header className="eb-card-header">
        <div>
          <h3>Sources de risque</h3>
          <p>
            Identifier les sources de risque selon la méthode EBIOS RM (ANSSI) : objectif visé,
            événement redouté, parties prenantes et biens supports.
          </p>
        </div>
        <button type="button" className="eb-btn eb-btn-primary" onClick={openCreate}>
          Ajouter
        </button>
      </header>

      {items.length === 0 ? (
        <div className="eb-card-empty">
          <p>
            Aucune source de risque identifiée. Créez au moins une source complète pour avancer
            (objectif, événement redouté, gravité, parties prenantes et biens supports).
          </p>
        </div>
      ) : (
        <ul className="eb-card-list eb-risk-source-list">
          {items.map((item) => {
            const data = riskSourceFromRecord(item);
            const complete = isRiskSourceComplete(item);
            return (
              <li key={item.id}>
                <div className="eb-card-item-main">
                  <div className="eb-risk-source-title">
                    <strong>{item.label}</strong>
                    <span className={`eb-severity-badge ${SEVERITY_CLASS[data.severity] ?? ""}`}>
                      {data.severity}
                    </span>
                    {!complete ? <span className="eb-incomplete-badge">Incomplet</span> : null}
                  </div>
                  {data.target_objective ? (
                    <p>
                      <span className="eb-field-label">Objectif visé :</span> {data.target_objective}
                    </p>
                  ) : null}
                  {data.feared_event ? (
                    <p>
                      <span className="eb-field-label">Événement redouté :</span> {data.feared_event}
                    </p>
                  ) : null}
                  <div className="eb-card-meta">
                    <span>{data.stakeholder_ids.length} partie(s) prenante(s)</span>
                    <span>{data.supporting_asset_ids.length} bien(s) support</span>
                  </div>
                  {data.comment ? <p className="eb-risk-comment">{data.comment}</p> : null}
                </div>
                <div className="eb-card-item-actions">
                  <button type="button" className="eb-btn eb-btn-ghost" onClick={() => openEdit(item)}>
                    Modifier
                  </button>
                  <button type="button" className="eb-btn eb-btn-danger" onClick={() => onDelete(item.id)}>
                    Supprimer
                  </button>
                </div>
              </li>
            );
          })}
        </ul>
      )}

      <RecordFormModal
        open={open}
        title={editId ? "Modifier la source de risque" : "Ajouter une source de risque"}
        onClose={() => setOpen(false)}
        onSubmit={handleSubmit}
        submitLabel={editId ? "Enregistrer" : "Ajouter"}
        busy={busy}
      >
        <FormField label="Source de risque" required>
          <FormInput
            value={form.label}
            onChange={(e) => setForm({ ...form, label: e.target.value })}
            placeholder="Ex. Cybercriminels, erreur humaine, défaillance fournisseur"
          />
        </FormField>
        <FormField label="Objectif visé" required>
          <FormTextarea
            value={form.target_objective}
            onChange={(e) => setForm({ ...form, target_objective: e.target.value })}
            placeholder="Objectif poursuivi par la source de risque"
          />
        </FormField>
        <FormField label="Événement redouté" required>
          <FormTextarea
            value={form.feared_event}
            onChange={(e) => setForm({ ...form, feared_event: e.target.value })}
            placeholder="Conséquence redoutée pour l'organisation"
          />
        </FormField>
        <FormField label="Gravité" required>
          <FormSelect
            value={form.severity}
            onChange={(e) => setForm({ ...form, severity: e.target.value })}
          >
            {SEVERITY_LEVELS.map((level) => (
              <option key={level} value={level}>
                {level}
              </option>
            ))}
          </FormSelect>
        </FormField>
        <FormField label="Parties prenantes (Atelier 1)" required>
          <MultiSelect
            options={stakeholderOptions}
            selected={form.stakeholder_ids}
            onChange={(ids) => setForm({ ...form, stakeholder_ids: ids })}
            emptyLabel="Aucune partie prenante — complétez l'Atelier 1."
          />
        </FormField>
        <FormField label="Biens supports" required>
          <MultiSelect
            options={assetOptions}
            selected={form.supporting_asset_ids}
            onChange={(ids) => setForm({ ...form, supporting_asset_ids: ids })}
            emptyLabel="Aucun bien support — synchronisez la cartographie urbanisme."
          />
        </FormField>
        <FormField label="Commentaire">
          <FormTextarea
            value={form.comment}
            onChange={(e) => setForm({ ...form, comment: e.target.value })}
          />
        </FormField>
      </RecordFormModal>
    </section>
  );
}
