import { useState } from "react";
import type { EbiosRecord } from "../types";
import {
  EMPTY_SCOPE,
  scopeFromRecord,
  type ScopeFormData,
} from "./constants";
import ProposalActions, { proposalStatusClass, proposalStatusLabel } from "./ProposalStatus";
import RecordFormModal, { FormField, FormInput, FormTextarea } from "./RecordFormModal";

type Props = {
  records: EbiosRecord[];
  onSave: (data: ScopeFormData, existingId?: string) => Promise<void>;
  onDelete: (id: string) => Promise<void>;
  onValidate: (id: string) => Promise<void>;
  onReject: (id: string) => Promise<void>;
  onRestore: (id: string) => Promise<void>;
};

export default function ScopeCard({
  records,
  onSave,
  onDelete,
  onValidate,
  onReject,
  onRestore,
}: Props) {
  const scope = records.find((r) => r.record_type === "security_scope");
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [form, setForm] = useState<ScopeFormData>(EMPTY_SCOPE);

  const openCreate = () => {
    setForm(EMPTY_SCOPE);
    setOpen(true);
  };

  const openEdit = () => {
    if (!scope) return;
    setForm(scopeFromRecord(scope));
    setOpen(true);
  };

  const handleSubmit = async () => {
    if (!form.label.trim()) return;
    setBusy(true);
    try {
      await onSave(form, scope?.id);
      setOpen(false);
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="eb-card">
      <header className="eb-card-header">
        <div>
          <h3>Périmètre étudié</h3>
          <p>Délimiter le périmètre de l&apos;analyse de risques.</p>
        </div>
        {!scope && (
          <button type="button" className="eb-btn eb-btn-primary" onClick={openCreate}>
            Ajouter
          </button>
        )}
      </header>

      {!scope ? (
        <div className="eb-card-empty">
          <p>Aucun périmètre défini. Renseignez le scope de l&apos;étude EBIOS RM.</p>
        </div>
      ) : (
        <ul className="eb-card-list">
          <li>
            <div className="eb-card-item-main">
              <strong>{scope.label}</strong>
              {proposalStatusLabel(scope.status) && (
                <span className={`eb-status-badge ${proposalStatusClass(scope.status)}`}>
                  {proposalStatusLabel(scope.status)}
                </span>
              )}
              {scope.description && <p>{scope.description}</p>}
              <div className="eb-card-meta">
                {scope.properties.business_objectives ? (
                  <span>Objectifs : {String(scope.properties.business_objectives)}</span>
                ) : null}
                {scope.properties.activities ? (
                  <span>Activités : {String(scope.properties.activities)}</span>
                ) : null}
              </div>
            </div>
            <div className="eb-card-item-actions">
              <ProposalActions
                status={scope.status}
                onValidate={() => onValidate(scope.id)}
                onReject={() => onReject(scope.id)}
                onRestore={() => onRestore(scope.id)}
              />
              <button type="button" className="eb-btn eb-btn-ghost" onClick={openEdit}>
                Modifier
              </button>
              <button
                type="button"
                className="eb-btn eb-btn-danger"
                onClick={() => onDelete(scope.id)}
              >
                Supprimer
              </button>
            </div>
          </li>
        </ul>
      )}

      <RecordFormModal
        open={open}
        title={scope ? "Modifier le périmètre" : "Définir le périmètre étudié"}
        onClose={() => setOpen(false)}
        onSubmit={handleSubmit}
        submitLabel={scope ? "Enregistrer" : "Créer"}
        busy={busy}
      >
        <FormField label="Nom du périmètre" required>
          <FormInput
            value={form.label}
            onChange={(e) => setForm({ ...form, label: e.target.value })}
            placeholder="Ex. Périmètre SI métier"
          />
        </FormField>
        <FormField label="Description">
          <FormTextarea
            value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
          />
        </FormField>
        <FormField label="Objectifs métier concernés">
          <FormTextarea
            value={form.business_objectives}
            onChange={(e) => setForm({ ...form, business_objectives: e.target.value })}
          />
        </FormField>
        <FormField label="Activités concernées">
          <FormTextarea
            value={form.activities}
            onChange={(e) => setForm({ ...form, activities: e.target.value })}
          />
        </FormField>
        <FormField label="Applications concernées">
          <FormTextarea
            value={form.applications}
            onChange={(e) => setForm({ ...form, applications: e.target.value })}
          />
        </FormField>
        <FormField label="Sites concernés">
          <FormInput
            value={form.sites}
            onChange={(e) => setForm({ ...form, sites: e.target.value })}
          />
        </FormField>
        <FormField label="Contraintes réglementaires">
          <FormTextarea
            value={form.regulatory_constraints}
            onChange={(e) => setForm({ ...form, regulatory_constraints: e.target.value })}
          />
        </FormField>
      </RecordFormModal>
    </section>
  );
}
