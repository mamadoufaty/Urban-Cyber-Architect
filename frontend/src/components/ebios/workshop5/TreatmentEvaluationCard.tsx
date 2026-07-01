import type { Workshop5Bundle } from "./constants";
import { CRITICALITY_CLASS } from "../workshop4/constants";
import { SEVERITY_CLASS } from "../workshop2/constants";
import { TREATMENT_DECISIONS, WORKFLOW_VALIDATED, actorLabel } from "./constants";

type Props = {
  bundle: Workshop5Bundle;
  treatmentDecisions: string[];
  onDecisionChange: (evaluationId: string, decision: string) => void;
  onValidate: (evaluationId: string) => void;
  onDelete: (evaluationId: string) => void;
  onToggleMeasure: (measureId: string, retained: boolean) => void;
  onActionUpdate: (actionId: string, field: string, value: string) => void;
};

export default function TreatmentEvaluationCard({
  bundle,
  treatmentDecisions,
  onDecisionChange,
  onValidate,
  onDelete,
  onToggleMeasure,
  onActionUpdate,
}: Props) {
  const ev = bundle.evaluation;
  const p = ev.properties ?? {};
  const status = String(p.workflow_status ?? "");
  const decisions = treatmentDecisions.length ? treatmentDecisions : [...TREATMENT_DECISIONS];

  return (
    <article className="eb-treatment-card">
      <header className="eb-treatment-card-header">
        <div>
          <h3>{ev.label}</h3>
          <p className="eb-treatment-subtitle">{String(p.operational_scenario_label ?? "")}</p>
        </div>
        <div className="eb-risk-source-title">
          <span className={`eb-severity-badge ${SEVERITY_CLASS[String(p.severity)] ?? ""}`}>
            Gravité {String(p.severity ?? "—")}
          </span>
          <span className="eb-likelihood-badge">Prob. {String(p.likelihood ?? "—")}</span>
          <span className={`eb-severity-badge ${CRITICALITY_CLASS[String(p.criticality)] ?? ""}`}>
            Crit. {String(p.criticality ?? "—")}
          </span>
        </div>
      </header>

      <div className="eb-treatment-context">
        <div>
          <span className="eb-field-label">Bien support</span>
          <p>{String(p.supporting_asset ?? "—")}</p>
        </div>
        <div>
          <span className="eb-field-label">Source de risque</span>
          <p>{String(p.risk_source_label ?? "—")}</p>
        </div>
        <div>
          <span className="eb-field-label">Organisation</span>
          <p>{actorLabel(p.organization as Record<string, unknown>)}</p>
        </div>
        <div>
          <span className="eb-field-label">Acteur propriétaire</span>
          <p>{actorLabel(p.owner_actor as Record<string, unknown>)}</p>
        </div>
        <div>
          <span className="eb-field-label">Décideur métier</span>
          <p>{actorLabel(p.decision_maker_actor as Record<string, unknown>)}</p>
        </div>
        <div>
          <span className="eb-field-label">Validateur</span>
          <p>{actorLabel(p.validator_actor as Record<string, unknown>)}</p>
        </div>
      </div>

      <section className="eb-treatment-section">
        <h4>Décision de traitement</h4>
        <div className="eb-decision-buttons">
          {decisions.map((d) => (
            <button
              key={d}
              type="button"
              className={`eb-btn ${p.treatment_decision === d ? "eb-btn-primary" : "eb-btn-ghost"}`}
              onClick={() => onDecisionChange(ev.id, d)}
            >
              {d}
            </button>
          ))}
        </div>
      </section>

      <section className="eb-treatment-section">
        <h4>Mesures proposées automatiquement</h4>
        <ul className="eb-measure-list">
          {bundle.measures.map((m) => {
            const mp = m.properties ?? {};
            const refs = (mp.framework_refs as Record<string, string>) ?? {};
            return (
              <li key={m.id}>
                <label className="eb-multi-select-item">
                  <input
                    type="checkbox"
                    checked={Boolean(mp.retained ?? true)}
                    onChange={(e) => onToggleMeasure(m.id, e.target.checked)}
                  />
                  <span>
                    <strong>{m.label}</strong>
                    {m.description ? <small>{m.description}</small> : null}
                    <small className="eb-framework-refs">
                      ISO 27002 {refs.iso27002} · NIST {refs.nist_csf} · CIS {refs.cis_controls} · ANSSI{" "}
                      {refs.anssi}
                    </small>
                  </span>
                </label>
              </li>
            );
          })}
        </ul>
      </section>

      <section className="eb-treatment-section">
        <h4>Plan de Traitement des Risques (PTR)</h4>
        <div className="eb-ptr-table-wrap">
          <table className="eb-ptr-table">
            <thead>
              <tr>
                <th>Mesure</th>
                <th>Responsable</th>
                <th>Échéance</th>
                <th>Priorité</th>
                <th>Budget</th>
                <th>Statut</th>
              </tr>
            </thead>
            <tbody>
              {bundle.actions.map((a) => {
                const ap = a.properties ?? {};
                return (
                  <tr key={a.id}>
                    <td>{a.label}</td>
                    <td>{String(ap.responsible_actor_label ?? "—")}</td>
                    <td>
                      <input
                        className="eb-input eb-ptr-input"
                        type="date"
                        value={String(ap.due_date ?? "")}
                        onChange={(e) => onActionUpdate(a.id, "due_date", e.target.value)}
                      />
                    </td>
                    <td>
                      <select
                        className="eb-select eb-ptr-input"
                        value={String(ap.priority ?? "Haute")}
                        onChange={(e) => onActionUpdate(a.id, "priority", e.target.value)}
                      >
                        <option value="Haute">Haute</option>
                        <option value="Moyenne">Moyenne</option>
                        <option value="Basse">Basse</option>
                      </select>
                    </td>
                    <td>
                      <input
                        className="eb-input eb-ptr-input"
                        placeholder="Optionnel"
                        value={ap.budget != null ? String(ap.budget) : ""}
                        onChange={(e) => onActionUpdate(a.id, "budget", e.target.value)}
                      />
                    </td>
                    <td>
                      <select
                        className="eb-select eb-ptr-input"
                        value={String(ap.status ?? "Planifié")}
                        onChange={(e) => onActionUpdate(a.id, "status", e.target.value)}
                      >
                        <option value="Planifié">Planifié</option>
                        <option value="En cours">En cours</option>
                        <option value="Terminé">Terminé</option>
                      </select>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>

      <section className="eb-treatment-section eb-risk-calc">
        <h4>Calcul automatique</h4>
        <div className="eb-risk-calc-grid">
          <div>
            <span className="eb-field-label">Risque initial</span>
            <strong>
              {String(p.initial_risk_label ?? "—")} ({String(p.initial_risk_score ?? "—")})
            </strong>
          </div>
          <div>
            <span className="eb-field-label">Mesures retenues</span>
            <strong>{String(p.retained_measure_count ?? bundle.measures.length)}</strong>
          </div>
          <div>
            <span className="eb-field-label">Risque résiduel</span>
            <strong>
              {String(p.residual_risk_label ?? bundle.residual_risk?.properties?.residual_risk_label ?? "—")} (
              {String(p.residual_risk_score ?? bundle.residual_risk?.properties?.residual_risk_score ?? "—")})
            </strong>
          </div>
        </div>
      </section>

      <footer className="eb-treatment-card-footer">
        <span className={`eb-status-badge ${status === WORKFLOW_VALIDATED ? "status-validated" : "status-auto"}`}>
          {status}
        </span>
        <div className="eb-card-item-actions eb-treatment-actions">
          {status !== WORKFLOW_VALIDATED ? (
            <button type="button" className="eb-btn eb-btn-primary" onClick={() => onValidate(ev.id)}>
              Valider
            </button>
          ) : null}
          <button type="button" className="eb-btn eb-btn-danger" onClick={() => onDelete(ev.id)}>
            Supprimer
          </button>
        </div>
      </footer>
    </article>
  );
}
