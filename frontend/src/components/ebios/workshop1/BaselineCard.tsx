import { useState } from "react";
import type { EbiosRecord } from "../types";
import {
  BASELINE_STATUSES,
  EMPTY_BASELINE,
  MATURITY_LEVELS,
  baselineFromRecord,
  type BaselineFormData,
} from "./constants";
import RecordFormModal, { FormField, FormInput, FormSelect, FormTextarea } from "./RecordFormModal";

type Props = {
  records: EbiosRecord[];
  onSave: (data: BaselineFormData, existingId?: string) => Promise<void>;
  onDelete: (id: string) => Promise<void>;
};

export default function BaselineCard({ records, onSave, onDelete }: Props) {
  const items = records.filter((r) => r.record_type === "security_baseline");
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [editId, setEditId] = useState<string | undefined>();
  const [form, setForm] = useState<BaselineFormData>(EMPTY_BASELINE);

  const openCreate = () => {
    setEditId(undefined);
    setForm(EMPTY_BASELINE);
    setOpen(true);
  };

  const openEdit = (record: EbiosRecord) => {
    setEditId(record.id);
    setForm(baselineFromRecord(record));
    setOpen(true);
  };

  const handleSubmit = async () => {
    if (!form.label.trim()) return;
    setBusy(true);
    try {
      await onSave(form, editId);
      setOpen(false);
    } finally {
      setBusy(false);
    }
  };

  const maturityLabel = (value: unknown) =>
    MATURITY_LEVELS.find((m) => m.value === String(value))?.label ?? String(value ?? "");

  return (
    <section className="eb-card">
      <header className="eb-card-header">
        <div>
          <h3>Socle de sécurité</h3>
          <p>Recenser les mesures de sécurité déjà en place.</p>
        </div>
        <button type="button" className="eb-btn eb-btn-primary" onClick={openCreate}>
          Ajouter
        </button>
      </header>

      {items.length === 0 ? (
        <div className="eb-card-empty">
          <p>Aucune mesure recensée. Documentez le socle de sécurité existant.</p>
        </div>
      ) : (
        <ul className="eb-card-list">
          {items.map((item) => (
            <li key={item.id}>
              <div className="eb-card-item-main">
                <strong>{item.label}</strong>
                {item.description && <p>{item.description}</p>}
                <div className="eb-card-meta">
                  {item.properties.domain ? <span>{String(item.properties.domain)}</span> : null}
                  {item.properties.status ? <span>{String(item.properties.status)}</span> : null}
                  {item.properties.maturity_level ? (
                    <span>{maturityLabel(item.properties.maturity_level)}</span>
                  ) : null}
                </div>
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
          ))}
        </ul>
      )}

      <RecordFormModal
        open={open}
        title={editId ? "Modifier la mesure" : "Ajouter une mesure de socle"}
        onClose={() => setOpen(false)}
        onSubmit={handleSubmit}
        submitLabel={editId ? "Enregistrer" : "Ajouter"}
        busy={busy}
      >
        <FormField label="Nom de la mesure" required>
          <FormInput
            value={form.label}
            onChange={(e) => setForm({ ...form, label: e.target.value })}
          />
        </FormField>
        <FormField label="Domaine">
          <FormInput
            value={form.domain}
            onChange={(e) => setForm({ ...form, domain: e.target.value })}
            placeholder="Ex. Réseau, IAM, SIEM"
          />
        </FormField>
        <FormField label="Description">
          <FormTextarea
            value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
          />
        </FormField>
        <FormField label="Statut">
          <FormSelect value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })}>
            {BASELINE_STATUSES.map((status) => (
              <option key={status} value={status}>
                {status}
              </option>
            ))}
          </FormSelect>
        </FormField>
        <FormField label="Niveau de maturité">
          <FormSelect
            value={form.maturity_level}
            onChange={(e) => setForm({ ...form, maturity_level: e.target.value })}
          >
            {MATURITY_LEVELS.map((level) => (
              <option key={level.value} value={level.value}>
                {level.label}
              </option>
            ))}
          </FormSelect>
        </FormField>
        <FormField label="Référence ISO 27002">
          <FormInput
            value={form.iso27002_ref}
            onChange={(e) => setForm({ ...form, iso27002_ref: e.target.value })}
            placeholder="Ex. 8.20 — Sécurité des réseaux"
          />
        </FormField>
      </RecordFormModal>
    </section>
  );
}
