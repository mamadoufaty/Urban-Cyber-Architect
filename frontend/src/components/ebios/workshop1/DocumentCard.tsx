import { useState } from "react";
import type { EbiosRecord } from "../types";
import {
  DOCUMENT_TYPES,
  EMPTY_DOCUMENT,
  documentFromRecord,
  type DocumentFormData,
} from "./constants";
import ProposalActions, { proposalStatusClass, proposalStatusLabel } from "./ProposalStatus";
import RecordFormModal, { FormField, FormInput, FormSelect, FormTextarea } from "./RecordFormModal";

type Props = {
  records: EbiosRecord[];
  onSave: (data: DocumentFormData, existingId?: string) => Promise<void>;
  onDelete: (id: string) => Promise<void>;
  onValidate: (id: string) => Promise<void>;
  onReject: (id: string) => Promise<void>;
  onRestore: (id: string) => Promise<void>;
};

export default function DocumentCard({
  records,
  onSave,
  onDelete,
  onValidate,
  onReject,
  onRestore,
}: Props) {
  const items = records.filter((r) => r.record_type === "reference_document");
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [editId, setEditId] = useState<string | undefined>();
  const [form, setForm] = useState<DocumentFormData>(EMPTY_DOCUMENT);

  const openCreate = () => {
    setEditId(undefined);
    setForm(EMPTY_DOCUMENT);
    setOpen(true);
  };

  const openEdit = (record: EbiosRecord) => {
    setEditId(record.id);
    setForm(documentFromRecord(record));
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
          <h3>Documents de référence</h3>
          <p>Référencer les documents utilisés pour le cadrage.</p>
        </div>
        <button type="button" className="eb-btn eb-btn-primary" onClick={openCreate}>
          Ajouter
        </button>
      </header>

      {items.length === 0 ? (
        <div className="eb-card-empty">
          <p>Aucun document référencé. Ajoutez PSSI, PCA, normes ou contrats.</p>
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
                  {item.properties.doc_type ? <span>{String(item.properties.doc_type)}</span> : null}
                  {item.properties.version ? <span>v{String(item.properties.version)}</span> : null}
                  {item.properties.owner ? <span>{String(item.properties.owner)}</span> : null}
                </div>
                {item.properties.link ? (
                  <p className="eb-card-link">{String(item.properties.link)}</p>
                ) : null}
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
        title={editId ? "Modifier le document" : "Ajouter un document de référence"}
        onClose={() => setOpen(false)}
        onSubmit={handleSubmit}
        submitLabel={editId ? "Enregistrer" : "Ajouter"}
        busy={busy}
      >
        <FormField label="Nom du document" required>
          <FormInput
            value={form.label}
            onChange={(e) => setForm({ ...form, label: e.target.value })}
          />
        </FormField>
        <FormField label="Type">
          <FormSelect value={form.doc_type} onChange={(e) => setForm({ ...form, doc_type: e.target.value })}>
            {DOCUMENT_TYPES.map((type) => (
              <option key={type} value={type}>
                {type}
              </option>
            ))}
          </FormSelect>
        </FormField>
        <FormField label="Version">
          <FormInput
            value={form.version}
            onChange={(e) => setForm({ ...form, version: e.target.value })}
          />
        </FormField>
        <FormField label="Date">
          <FormInput
            type="date"
            value={form.date}
            onChange={(e) => setForm({ ...form, date: e.target.value })}
          />
        </FormField>
        <FormField label="Propriétaire">
          <FormInput
            value={form.owner}
            onChange={(e) => setForm({ ...form, owner: e.target.value })}
          />
        </FormField>
        <FormField label="Lien ou chemin">
          <FormInput
            value={form.link}
            onChange={(e) => setForm({ ...form, link: e.target.value })}
            placeholder="URL ou chemin documentaire"
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
