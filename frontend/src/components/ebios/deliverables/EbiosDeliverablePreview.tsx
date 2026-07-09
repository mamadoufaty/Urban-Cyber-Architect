import {
  deliverableHasTable,
  deliverableTableColumns,
  deliverableTableRows,
  executiveSummaryKpis,
} from "./deliverablePreview";
import type { EbiosDeliverableResponse } from "./types";

function formatDate(value: string) {
  try {
    return new Date(value).toLocaleString("fr-FR");
  } catch {
    return value;
  }
}

function cellValue(value: unknown): string {
  if (value == null || value === "") return "—";
  if (Array.isArray(value)) return value.join(", ");
  return String(value);
}

type Props = {
  deliverable: EbiosDeliverableResponse;
};

export default function EbiosDeliverablePreview({ deliverable }: Props) {
  const columns = deliverableTableColumns(deliverable);
  const rows = deliverableTableRows(deliverable);
  const kpis = executiveSummaryKpis(deliverable);
  const showTable = deliverableHasTable(deliverable);

  return (
    <article className="livrables-document ebios-deliverable-preview">
      <header className="ebios-deliverable-preview-header">
        <h3>{deliverable.title}</h3>
        <p className="livrables-muted">
          Généré le {formatDate(deliverable.generated_at)} — progression étude :{" "}
          {deliverable.overall_progress_percent} %
        </p>
      </header>

      {!deliverable.is_complete && deliverable.completeness_warning ? (
        <div className="ebios-deliverable-warning" role="alert">
          <strong>Étude incomplète</strong>
          <p>{deliverable.completeness_warning}</p>
        </div>
      ) : null}

      {deliverable.deliverable_type === "executive_summary" && kpis ? (
        <section className="ebios-deliverable-kpis">
          <h4>Indicateurs clés</h4>
          <div className="ebios-deliverable-kpi-grid">
            <div>
              <span className="eb-field-label">Progression globale</span>
              <strong>{kpis.overall_progress_percent ?? 0} %</strong>
            </div>
            <div>
              <span className="eb-field-label">Ateliers validés</span>
              <strong>
                {kpis.workshops_completed ?? 0} / {kpis.workshops_total ?? 5}
              </strong>
            </div>
            <div>
              <span className="eb-field-label">Risques évalués</span>
              <strong>{kpis.risks_total ?? 0}</strong>
            </div>
            <div>
              <span className="eb-field-label">Actions PTR</span>
              <strong>
                {kpis.treatment_actions_completed ?? 0} / {kpis.treatment_actions_total ?? 0}
              </strong>
            </div>
            <div>
              <span className="eb-field-label">Budget estimé</span>
              <strong>{kpis.estimated_budget ?? 0} €</strong>
            </div>
            <div>
              <span className="eb-field-label">Actions en retard</span>
              <strong>{kpis.treatment_actions_overdue ?? 0}</strong>
            </div>
          </div>
        </section>
      ) : null}

      {(deliverable.sections || []).map((section) => (
        <section key={section.id}>
          <h4>{section.title}</h4>
          {section.content ? <p>{section.content}</p> : null}
          {section.bullets && section.bullets.length > 0 ? (
            <ul>
              {section.bullets.map((bullet) => (
                <li key={bullet}>{bullet}</li>
              ))}
            </ul>
          ) : null}
        </section>
      ))}

      {showTable ? (
        <section className="ebios-deliverable-table-section">
          <h4>Données détaillées</h4>
          <div className="ebios-deliverable-table-wrap">
            <table className="ebios-deliverable-table">
              <thead>
                <tr>
                  {columns.map((col) => (
                    <th key={col.key}>{col.label}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {rows.map((row, idx) => (
                  <tr key={String(row.ptr_id ?? row.risk_id ?? idx)}>
                    {columns.map((col) => (
                      <td key={col.key}>{cellValue(row[col.key])}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      ) : null}
    </article>
  );
}
