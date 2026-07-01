import Workshop1Panel from "./workshop1/Workshop1Panel";
import Workshop2Panel from "./workshop2/Workshop2Panel";
import Workshop3Panel from "./workshop3/Workshop3Panel";
import Workshop4Panel from "./workshop4/Workshop4Panel";
import Workshop5Panel from "./workshop5/Workshop5Panel";
import type { EbiosMetamodel, EbiosOverview, EbiosRecord, EbiosWorkshopSpec } from "./types";

type Props = {
  workshop: EbiosWorkshopSpec;
  records: EbiosRecord[];
  metamodel: EbiosMetamodel | null;
  projectId?: string;
  assessmentId?: string;
  workshop1Records?: EbiosRecord[];
  workshop2Records?: EbiosRecord[];
  onRecordsChange?: (records: EbiosRecord[]) => void;
  onOverviewChange?: (overview: EbiosOverview) => void;
  refreshOverview?: () => Promise<void>;
  refreshRecords?: () => Promise<void>;
};

export default function EbiosWorkshopPanel({
  workshop,
  records,
  metamodel,
  projectId,
  assessmentId,
  workshop1Records = [],
  workshop2Records = [],
  onRecordsChange,
  onOverviewChange,
  refreshOverview,
  refreshRecords,
}: Props) {
  if (
    workshop.number === 1 &&
    projectId &&
    assessmentId &&
    onRecordsChange &&
    onOverviewChange &&
    refreshOverview &&
    refreshRecords
  ) {
    return (
      <Workshop1Panel
        workshop={workshop}
        projectId={projectId}
        assessmentId={assessmentId}
        records={records}
        onRecordsChange={onRecordsChange}
        onOverviewChange={onOverviewChange}
        refreshOverview={refreshOverview}
        refreshRecords={refreshRecords}
      />
    );
  }

  if (
    workshop.number === 2 &&
    projectId &&
    assessmentId &&
    onRecordsChange &&
    refreshOverview &&
    refreshRecords
  ) {
    return (
      <Workshop2Panel
        workshop={workshop}
        projectId={projectId}
        assessmentId={assessmentId}
        records={records}
        workshop1Records={workshop1Records}
        onRecordsChange={onRecordsChange}
        refreshOverview={refreshOverview}
      />
    );
  }

  if (
    workshop.number === 3 &&
    projectId &&
    assessmentId &&
    onRecordsChange &&
    refreshOverview &&
    refreshRecords
  ) {
    return (
      <Workshop3Panel
        workshop={workshop}
        projectId={projectId}
        assessmentId={assessmentId}
        records={records}
        workshop1Records={workshop1Records}
        workshop2Records={workshop2Records}
        onRecordsChange={onRecordsChange}
        refreshOverview={refreshOverview}
      />
    );
  }

  if (
    workshop.number === 4 &&
    projectId &&
    assessmentId &&
    onRecordsChange &&
    refreshOverview &&
    refreshRecords
  ) {
    return (
      <Workshop4Panel
        workshop={workshop}
        projectId={projectId}
        assessmentId={assessmentId}
        onRecordsChange={onRecordsChange}
        refreshOverview={refreshOverview}
      />
    );
  }

  if (
    workshop.number === 5 &&
    projectId &&
    assessmentId &&
    onRecordsChange &&
    refreshOverview &&
    refreshRecords
  ) {
    return (
      <Workshop5Panel
        workshop={workshop}
        projectId={projectId}
        assessmentId={assessmentId}
        onRecordsChange={onRecordsChange}
        refreshOverview={refreshOverview}
      />
    );
  }

  const typeLabels = metamodel?.record_type_labels ?? {};

  return (
    <div className="eb-workshop-panel">
      <header className="eb-workshop-panel-header">
        <span className="eb-workshop-badge">Atelier {workshop.number}</span>
        <h2>{workshop.label}</h2>
        <p>{workshop.description}</p>
      </header>

      <div className="eb-workshop-placeholder">
        <p>
          Espace de travail pour l&apos;atelier <strong>{workshop.short_label}</strong>.
          Les règles métier EBIOS RM et ISO seront intégrées à l&apos;étape suivante.
        </p>
      </div>

      <section className="eb-record-types">
        <h3>Types d&apos;entités prévus</h3>
        <ul>
          {workshop.record_types.map((type) => (
            <li key={type}>
              <code>{type}</code>
              {typeLabels[type] && <span> — {typeLabels[type]}</span>}
            </li>
          ))}
        </ul>
      </section>

      {records.length > 0 && (
        <section className="eb-records-list">
          <h3>Enregistrements ({records.length})</h3>
          <ul>
            {records.map((r) => (
              <li key={r.id}>
                <strong>{r.label}</strong>
                <span className="eb-record-type">{typeLabels[r.record_type] ?? r.record_type}</span>
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}
