import { useState } from "react";
import type { EbiosRecord } from "../types";
import RecordFormModal, {
  FormField,
  FormInput,
  FormSelect,
  FormTextarea,
} from "../workshop1/RecordFormModal";
import { SEVERITY_CLASS } from "../workshop2/constants";
import {
  EMPTY_SCENARIO,
  LIKELIHOOD_LEVELS,
  STATUS_CLASS,
  WORKFLOW_VALIDATED,
  scenarioFromRecord,
  type StrategicScenarioFormData,
} from "./constants";

type Props = {
  scenarios: EbiosRecord[];
  riskSources: EbiosRecord[];
  onSave: (data: StrategicScenarioFormData, existingId?: string) => Promise<void>;
  onValidate: (id: string) => Promise<void>;
  onDelete: (id: string) => Promise<void>;
  onCreateNew: () => void;
};

function ScenarioForm({
  form,
  setForm,
  riskSources,
}: {
  form: StrategicScenarioFormData;
  setForm: (f: StrategicScenarioFormData) => void;
  riskSources: EbiosRecord[];
}) {
  return (
    <>
      <FormField label="Titre" required>
        <FormInput value={form.label} onChange={(e) => setForm({ ...form, label: e.target.value })} />
      </FormField>
      <FormField label="Source de risque">
        <FormSelect
          value={form.risk_source_id}
          onChange={(e) => setForm({ ...form, risk_source_id: e.target.value })}
        >
          <option value="">—</option>
          {riskSources.map((rs) => (
            <option key={rs.id} value={rs.id}>
              {rs.label}
            </option>
          ))}
        </FormSelect>
      </FormField>
      <FormField label="Objectif de la source">
        <FormTextarea
          value={form.target_objective}
          onChange={(e) => setForm({ ...form, target_objective: e.target.value })}
        />
      </FormField>
      <FormField label="Événement redouté">
        <FormTextarea
          value={form.feared_event}
          onChange={(e) => setForm({ ...form, feared_event: e.target.value })}
        />
      </FormField>
      <FormField label="Description narrative">
        <FormTextarea
          value={form.narrative_description}
          onChange={(e) => setForm({ ...form, narrative_description: e.target.value })}
          rows={5}
        />
      </FormField>
      <FormField label="Gravité">
        <FormSelect
          value={form.severity}
          onChange={(e) => setForm({ ...form, severity: e.target.value })}
        >
          {LIKELIHOOD_LEVELS.map((l) => (
            <option key={l} value={l}>
              {l}
            </option>
          ))}
        </FormSelect>
      </FormField>
      <FormField label="Niveau de vraisemblance">
        <FormSelect
          value={form.likelihood}
          onChange={(e) => setForm({ ...form, likelihood: e.target.value })}
        >
          {LIKELIHOOD_LEVELS.map((l) => (
            <option key={l} value={l}>
              {l}
            </option>
          ))}
        </FormSelect>
      </FormField>
      <FormField label="Commentaires">
        <FormTextarea
          value={form.comment}
          onChange={(e) => setForm({ ...form, comment: e.target.value })}
        />
      </FormField>
    </>
  );
}

export default function StrategicScenarioList({
  scenarios,
  riskSources,
  onSave,
  onValidate,
  onDelete,
  onCreateNew,
}: Props) {
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [editId, setEditId] = useState<string | undefined>();
  const [form, setForm] = useState<StrategicScenarioFormData>(EMPTY_SCENARIO);

  const openEdit = (record: EbiosRecord) => {
    setEditId(record.id);
    setForm(scenarioFromRecord(record));
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

  if (!scenarios.length) {
    return (
      <div className="eb-card-empty">
        <p>Aucun scénario stratégique. Générez les scénarios à partir des sources de risque de l&apos;atelier 2.</p>
      </div>
    );
  }

  return (
    <>
      <ul className="eb-scenario-list">
        {scenarios.map((item) => {
          const data = scenarioFromRecord(item);
          const statusClass = STATUS_CLASS[data.workflow_status] ?? "";
          return (
            <li key={item.id} className="eb-scenario-card">
              <div className="eb-scenario-card-main">
                <div className="eb-risk-source-title">
                  <strong>{item.label}</strong>
                  <span className={`eb-severity-badge ${SEVERITY_CLASS[data.severity] ?? ""}`}>
                    {data.severity}
                  </span>
                  <span className="eb-likelihood-badge">Vraisembl. {data.likelihood}</span>
                  <span className={`eb-status-badge ${statusClass}`}>{data.workflow_status}</span>
                </div>
                <div className="eb-card-meta">
                  <span>Source : {String(item.properties.risk_source_label ?? "—")}</span>
                  {data.scenario_uid ? (
                    <span className="eb-scenario-uid" title="Identifiant pour l'atelier 4">
                      ID {data.scenario_uid.slice(0, 8)}…
                    </span>
                  ) : null}
                </div>
                {data.feared_event ? (
                  <p>
                    <span className="eb-field-label">Événement redouté :</span> {data.feared_event}
                  </p>
                ) : null}
              </div>
              <div className="eb-card-item-actions">
                <button type="button" className="eb-btn eb-btn-ghost" onClick={() => openEdit(item)}>
                  Modifier
                </button>
                {data.workflow_status !== WORKFLOW_VALIDATED ? (
                  <button type="button" className="eb-btn eb-btn-primary" onClick={() => onValidate(item.id)}>
                    Valider
                  </button>
                ) : null}
                <button type="button" className="eb-btn eb-btn-danger" onClick={() => onDelete(item.id)}>
                  Supprimer
                </button>
              </div>
            </li>
          );
        })}
      </ul>

      <div className="eb-scenario-actions">
        <button type="button" className="eb-btn eb-btn-ghost" onClick={onCreateNew}>
          Créer un scénario
        </button>
      </div>

      <RecordFormModal
        open={open}
        title={editId ? "Modifier le scénario stratégique" : "Nouveau scénario stratégique"}
        onClose={() => setOpen(false)}
        onSubmit={handleSubmit}
        submitLabel={editId ? "Enregistrer" : "Créer"}
        busy={busy}
      >
        <ScenarioForm form={form} setForm={setForm} riskSources={riskSources} />
      </RecordFormModal>
    </>
  );
}

export function StrategicScenarioCreateModal({
  open,
  onClose,
  form,
  setForm,
  riskSources,
  onSubmit,
  busy,
}: {
  open: boolean;
  onClose: () => void;
  form: StrategicScenarioFormData;
  setForm: (f: StrategicScenarioFormData) => void;
  riskSources: EbiosRecord[];
  onSubmit: () => void;
  busy: boolean;
}) {
  return (
    <RecordFormModal
      open={open}
      title="Créer un scénario stratégique"
      onClose={onClose}
      onSubmit={onSubmit}
      submitLabel="Créer"
      busy={busy}
    >
      <ScenarioForm form={form} setForm={setForm} riskSources={riskSources} />
    </RecordFormModal>
  );
}
