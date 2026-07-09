import { useState } from "react";
import type { EbiosRecord } from "../types";
import RecordFormModal, {
  FormField,
  FormInput,
  FormSelect,
  FormTextarea,
} from "../workshop1/RecordFormModal";
import ProposalActions, { proposalStatusClass, proposalStatusLabel } from "../workshop1/ProposalStatus";
import { CONFIDENCE_CLASS, SEVERITY_CLASS } from "../workshop2/constants";
import {
  EMPTY_SCENARIO,
  LIKELIHOOD_LEVELS,
  MOTIVATION_OPTIONS,
  scenarioConfidence,
  scenarioFromRecord,
  scenarioJustification,
  type StrategicScenarioFormData,
} from "./constants";

const MAX_LINKED_NAMES_SHOWN = 5;

function LinkedNames({ names, emptyLabel }: { names: string[]; emptyLabel: string }) {
  if (!names.length) {
    return <p className="eb-linked-empty">{emptyLabel}</p>;
  }
  const shown = names.slice(0, MAX_LINKED_NAMES_SHOWN);
  const remaining = names.length - shown.length;
  return (
    <ul className="eb-linked-names">
      {shown.map((name, idx) => (
        <li key={`${name}-${idx}`}>{name}</li>
      ))}
      {remaining > 0 ? <li className="eb-linked-names-more">… +{remaining} autre(s)</li> : null}
    </ul>
  );
}

type Props = {
  scenarios: EbiosRecord[];
  riskSources: EbiosRecord[];
  onSave: (data: StrategicScenarioFormData, existingId?: string) => Promise<void>;
  onValidate: (id: string) => Promise<void>;
  onReject: (id: string) => Promise<void>;
  onRestore: (id: string) => Promise<void>;
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
      <FormField label="Motivation">
        <FormSelect
          value={form.motivation}
          onChange={(e) => setForm({ ...form, motivation: e.target.value })}
        >
          {MOTIVATION_OPTIONS.map((m) => (
            <option key={m} value={m}>
              {m}
            </option>
          ))}
        </FormSelect>
      </FormField>
      <FormField label="Objectif stratégique">
        <FormTextarea
          value={form.strategic_objective}
          onChange={(e) =>
            setForm({ ...form, strategic_objective: e.target.value, target_objective: e.target.value })
          }
        />
      </FormField>
      <FormField label="Bien essentiel ciblé">
        <FormInput
          value={form.targeted_essential_asset}
          onChange={(e) => setForm({ ...form, targeted_essential_asset: e.target.value })}
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
  onReject,
  onRestore,
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
          const justification = scenarioJustification(item);
          const confidence = scenarioConfidence(item);
          return (
            <li key={item.id} className="eb-scenario-card">
              <div className="eb-scenario-card-main">
                <div className="eb-risk-source-title">
                  <strong>{item.label}</strong>
                  <span className={`eb-severity-badge ${SEVERITY_CLASS[data.severity] ?? ""}`}>
                    {data.severity}
                  </span>
                  <span className="eb-likelihood-badge">Vraisembl. {data.likelihood}</span>
                  {proposalStatusLabel(item.status) && (
                    <span className={`eb-status-badge ${proposalStatusClass(item.status)}`}>
                      {proposalStatusLabel(item.status)}
                    </span>
                  )}
                  {confidence.label ? (
                    <span
                      className={`eb-confidence-badge ${CONFIDENCE_CLASS[confidence.label] ?? ""}`}
                      title="Niveau de confiance indicatif de la proposition automatique"
                    >
                      Confiance IA : {confidence.label}
                      {confidence.score !== null ? ` (${confidence.score}%)` : ""}
                    </span>
                  ) : null}
                </div>
                <div className="eb-card-meta">
                  <span>Source de risque : {String(item.properties.risk_source_label ?? "—")}</span>
                  {data.motivation ? <span>Motivation : {data.motivation}</span> : null}
                  {data.scenario_uid ? (
                    <span className="eb-scenario-uid" title="Identifiant pour l'atelier 4">
                      ID {data.scenario_uid.slice(0, 8)}…
                    </span>
                  ) : null}
                </div>
                {data.strategic_objective ? (
                  <p>
                    <span className="eb-field-label">Objectif stratégique :</span>{" "}
                    {data.strategic_objective}
                  </p>
                ) : null}
                {data.targeted_essential_asset ? (
                  <p>
                    <span className="eb-field-label">Bien essentiel ciblé :</span>{" "}
                    {data.targeted_essential_asset}
                  </p>
                ) : null}
                {data.feared_event ? (
                  <p>
                    <span className="eb-field-label">Événement redouté :</span> {data.feared_event}
                  </p>
                ) : null}

                {justification.length > 0 ? (
                  <div className="eb-justification">
                    <span className="eb-field-label">Justification IA :</span>
                    <ul className="eb-justification-list">
                      {justification.map((bullet, idx) => (
                        <li key={idx}>{bullet}</li>
                      ))}
                    </ul>
                  </div>
                ) : null}

                <div>
                  <span className="eb-field-label">
                    Parties prenantes concernées ({data.stakeholder_ids.length}) :
                  </span>
                  <LinkedNames
                    names={
                      Array.isArray(item.properties.stakeholder_labels)
                        ? (item.properties.stakeholder_labels as unknown[]).map(String)
                        : []
                    }
                    emptyLabel="Aucune partie prenante liée."
                  />
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
