import { useState } from "react";
import type { EbiosRecord } from "../types";
import RecordFormModal, { FormField, FormInput, FormTextarea } from "../workshop1/RecordFormModal";
import { SEVERITY_CLASS } from "../workshop2/constants";
import {
  CRITICALITY_CLASS,
  STATUS_CLASS,
  WORKFLOW_VALIDATED,
  operationalFromRecord,
  type OperationalScenarioFormData,
} from "./constants";

type Props = {
  scenarios: EbiosRecord[];
  onSave: (data: OperationalScenarioFormData, id: string) => Promise<void>;
  onValidate: (id: string) => Promise<void>;
  onDelete: (id: string) => Promise<void>;
};

export default function OperationalScenarioList({
  scenarios,
  onSave,
  onValidate,
  onDelete,
}: Props) {
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [editId, setEditId] = useState("");
  const [form, setForm] = useState<OperationalScenarioFormData | null>(null);

  const openEdit = (record: EbiosRecord) => {
    setEditId(record.id);
    setForm(operationalFromRecord(record));
    setOpen(true);
  };

  const handleSubmit = async () => {
    if (!form?.label.trim()) return;
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
        <p>
          Aucun scénario opérationnel. Générez-les à partir des scénarios stratégiques validés
          (atelier 3).
        </p>
      </div>
    );
  }

  return (
    <>
      <ul className="eb-scenario-list">
        {scenarios.map((item) => {
          const data = operationalFromRecord(item);
          return (
            <li key={item.id} className="eb-scenario-card">
              <div className="eb-scenario-card-main">
                <div className="eb-risk-source-title">
                  <strong>{item.label}</strong>
                  <span className={`eb-severity-badge ${SEVERITY_CLASS[data.severity] ?? ""}`}>
                    {data.severity}
                  </span>
                  <span className="eb-likelihood-badge">Prob. {data.likelihood}</span>
                  <span
                    className={`eb-severity-badge ${CRITICALITY_CLASS[data.calculated_criticality] ?? ""}`}
                  >
                    Crit. {data.calculated_criticality}
                  </span>
                  <span className={`eb-status-badge ${STATUS_CLASS[data.workflow_status] ?? ""}`}>
                    {data.workflow_status}
                  </span>
                </div>
                <div className="eb-card-meta">
                  {data.strategic_scenario_label ? (
                    <span>Stratégique : {data.strategic_scenario_label}</span>
                  ) : null}
                  {data.threatening_actor ? <span>Acteur : {data.threatening_actor}</span> : null}
                </div>
                {data.attack_path ? (
                  <p className="eb-attack-path">
                    <span className="eb-field-label">Chemin d&apos;attaque :</span> {data.attack_path}
                  </p>
                ) : null}
                {data.impacted_supporting_asset ? (
                  <p>
                    <span className="eb-field-label">Bien support :</span>{" "}
                    {data.impacted_supporting_asset}
                  </p>
                ) : null}
                {data.consequence ? (
                  <p>
                    <span className="eb-field-label">Conséquence :</span> {data.consequence}
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

      {form ? (
        <RecordFormModal
          open={open}
          title="Modifier le scénario opérationnel"
          onClose={() => setOpen(false)}
          onSubmit={handleSubmit}
          submitLabel="Enregistrer"
          busy={busy}
        >
          <FormField label="Titre" required>
            <FormInput
              value={form.label}
              onChange={(e) => setForm({ ...form, label: e.target.value })}
            />
          </FormField>
          <FormField label="Acteur menaçant">
            <FormInput
              value={form.threatening_actor}
              onChange={(e) => setForm({ ...form, threatening_actor: e.target.value })}
            />
          </FormField>
          <FormField label="Chemin d'attaque">
            <FormTextarea
              value={form.attack_path}
              onChange={(e) => setForm({ ...form, attack_path: e.target.value })}
              rows={4}
            />
          </FormField>
          <FormField label="Conséquence">
            <FormTextarea
              value={form.consequence}
              onChange={(e) => setForm({ ...form, consequence: e.target.value })}
            />
          </FormField>
          <FormField label="Commentaire">
            <FormTextarea
              value={form.comment}
              onChange={(e) => setForm({ ...form, comment: e.target.value })}
            />
          </FormField>
        </RecordFormModal>
      ) : null}
    </>
  );
}
