import { useState } from "react";
import type { EbiosRecord } from "../types";
import {
  EMPTY_STAKEHOLDER,
  STAKEHOLDER_ROLES,
  stakeholderFromRecord,
  type StakeholderFormData,
} from "./constants";
import ProposalActions, { proposalStatusClass, proposalStatusLabel } from "./ProposalStatus";
import RecordFormModal, { FormField, FormInput, FormSelect, FormTextarea } from "./RecordFormModal";

type Props = {
  records: EbiosRecord[];
  onSave: (data: StakeholderFormData, existingId?: string) => Promise<void>;
  onDelete: (id: string) => Promise<void>;
  onValidate: (id: string) => Promise<void>;
  onReject: (id: string) => Promise<void>;
  onRestore: (id: string) => Promise<void>;
};

export default function StakeholderCard({
  records,
  onSave,
  onDelete,
  onValidate,
  onReject,
  onRestore,
}: Props) {
  const items = records.filter((r) => r.record_type === "stakeholder");
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [editId, setEditId] = useState<string | undefined>();
  const [form, setForm] = useState<StakeholderFormData>(EMPTY_STAKEHOLDER);

  const openCreate = () => {
    setEditId(undefined);
    setForm(EMPTY_STAKEHOLDER);
    setOpen(true);
  };

  const openEdit = (record: EbiosRecord) => {
    setEditId(record.id);
    setForm(stakeholderFromRecord(record));
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

  return (
    <section className="eb-card">
      <header className="eb-card-header">
        <div>
          <h3>Parties prenantes</h3>
          <p>Identifier les acteurs impliqués dans l&apos;analyse.</p>
        </div>
        <button type="button" className="eb-btn eb-btn-primary" onClick={openCreate}>
          Ajouter
        </button>
      </header>

      {items.length === 0 ? (
        <div className="eb-card-empty">
          <p>Aucune partie prenante. Ajoutez au moins un interlocuteur clé.</p>
        </div>
      ) : (
        <ul className="eb-card-list">
          {items.map((item) => (
            <li key={item.id}>
              <div className="eb-card-item-main">
                <strong>{item.label}</strong>
                {proposalStatusLabel(item.status) && (
                  <span className={`eb-status-badge ${proposalStatusClass(item.status)}`}>
                    {proposalStatusLabel(item.status)}
                  </span>
                )}
                <div className="eb-card-meta">
                  {item.properties.role ? <span>{String(item.properties.role)}</span> : null}
                  {item.properties.organization ? (
                    <span>{String(item.properties.organization)}</span>
                  ) : null}
                  {item.properties.involvement_level ? (
                    <span>Implication : {String(item.properties.involvement_level)}</span>
                  ) : null}
                </div>
              </div>
              <div className="eb-card-item-actions">
                <ProposalActions
                  status={item.status}
                  onValidate={() => onValidate(item.id)}
                  onReject={() => onReject(item.id)}
                  onRestore={() => onRestore(item.id)}
                />
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
        title={editId ? "Modifier la partie prenante" : "Ajouter une partie prenante"}
        onClose={() => setOpen(false)}
        onSubmit={handleSubmit}
        submitLabel={editId ? "Enregistrer" : "Ajouter"}
        busy={busy}
      >
        <FormField label="Nom" required>
          <FormInput
            value={form.label}
            onChange={(e) => setForm({ ...form, label: e.target.value })}
          />
        </FormField>
        <FormField label="Rôle">
          <FormSelect value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })}>
            {STAKEHOLDER_ROLES.map((role) => (
              <option key={role} value={role}>
                {role}
              </option>
            ))}
          </FormSelect>
        </FormField>
        <FormField label="Organisation">
          <FormInput
            value={form.organization}
            onChange={(e) => setForm({ ...form, organization: e.target.value })}
          />
        </FormField>
        <FormField label="Responsabilité">
          <FormTextarea
            value={form.responsibility}
            onChange={(e) => setForm({ ...form, responsibility: e.target.value })}
          />
        </FormField>
        <FormField label="Contact">
          <FormInput
            value={form.contact}
            onChange={(e) => setForm({ ...form, contact: e.target.value })}
            placeholder="email@organisation.fr"
          />
        </FormField>
        <FormField label="Niveau d'implication">
          <FormInput
            value={form.involvement_level}
            onChange={(e) => setForm({ ...form, involvement_level: e.target.value })}
            placeholder="Ex. Élevé, Moyen, Faible"
          />
        </FormField>
      </RecordFormModal>
    </section>
  );
}
