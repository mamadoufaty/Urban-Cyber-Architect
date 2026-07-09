import { useState } from "react";
import type { EbiosRecord } from "../types";
import RecordFormModal, {
  FormField,
  FormInput,
  FormSelect,
  FormTextarea,
} from "../workshop1/RecordFormModal";
import ProposalActions, { proposalStatusClass, proposalStatusLabel } from "../workshop1/ProposalStatus";
import {
  CONFIDENCE_CLASS,
  EMPTY_RISK_SOURCE,
  SEVERITY_CLASS,
  SEVERITY_LEVELS,
  isRiskSourceComplete,
  riskSourceConfidence,
  riskSourceFromRecord,
  riskSourceJustification,
  type RiskSourceFormData,
} from "./constants";

const MAX_LINKED_NAMES_SHOWN = 5;

function LinkedNames({
  ids,
  lookup,
  emptyLabel,
}: {
  ids: string[];
  lookup: Map<string, string>;
  emptyLabel: string;
}) {
  if (!ids.length) {
    return <p className="eb-linked-empty">{emptyLabel}</p>;
  }
  const names = ids.map((id) => lookup.get(id) ?? "Élément supprimé");
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
  records: EbiosRecord[];
  stakeholders: EbiosRecord[];
  supportingAssets: EbiosRecord[];
  onSave: (data: RiskSourceFormData, existingId?: string) => Promise<void>;
  onDelete: (id: string) => Promise<void>;
  onValidate: (id: string) => Promise<void>;
  onReject: (id: string) => Promise<void>;
  onRestore: (id: string) => Promise<void>;
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
  onValidate,
  onReject,
  onRestore,
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

  const stakeholderNameById = new Map(
    stakeholders.map((s) => [
      s.id,
      s.properties.role ? `${s.label} (${String(s.properties.role)})` : s.label,
    ])
  );
  const assetNameById = new Map(supportingAssets.map((a) => [a.id, a.label]));

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
            const justification = riskSourceJustification(item);
            const confidence = riskSourceConfidence(item);
            return (
              <li key={item.id}>
                <div className="eb-card-item-main">
                  <div className="eb-risk-source-title">
                    <strong>{item.label}</strong>
                    <span className={`eb-severity-badge ${SEVERITY_CLASS[data.severity] ?? ""}`}>
                      {data.severity}
                    </span>
                    {proposalStatusLabel(item.status) && (
                      <span className={`eb-status-badge ${proposalStatusClass(item.status)}`}>
                        {proposalStatusLabel(item.status)}
                      </span>
                    )}
                    {!complete ? <span className="eb-incomplete-badge">Incomplet</span> : null}
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

                  <div className="eb-risk-source-linked">
                    <div>
                      <span className="eb-field-label">
                        Biens supports ({data.supporting_asset_ids.length}) :
                      </span>
                      <LinkedNames
                        ids={data.supporting_asset_ids}
                        lookup={assetNameById}
                        emptyLabel="Aucun bien support lié."
                      />
                    </div>
                    <div>
                      <span className="eb-field-label">
                        Parties prenantes ({data.stakeholder_ids.length}) :
                      </span>
                      <LinkedNames
                        ids={data.stakeholder_ids}
                        lookup={stakeholderNameById}
                        emptyLabel="Aucune partie prenante liée."
                      />
                    </div>
                  </div>
                  {data.comment ? <p className="eb-risk-comment">{data.comment}</p> : null}
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
