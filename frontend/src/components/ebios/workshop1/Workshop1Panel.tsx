import { useState } from "react";
import {
  createEbiosRecord,
  deleteEbiosRecord,
  generateEbiosWorkshop1FromCartography,
  updateEbiosRecord,
} from "../../../api";
import type { EbiosOverview, EbiosRecord, EbiosWorkshopSpec } from "../types";
import BaselineCard from "./BaselineCard";
import DocumentCard from "./DocumentCard";
import ScopeCard from "./ScopeCard";
import StakeholderCard from "./StakeholderCard";
import type {
  BaselineFormData,
  DocumentFormData,
  ScopeFormData,
  StakeholderFormData,
} from "./constants";

type Props = {
  workshop: EbiosWorkshopSpec;
  projectId: string;
  assessmentId: string;
  records: EbiosRecord[];
  onRecordsChange: (records: EbiosRecord[]) => void;
  onOverviewChange: (overview: EbiosOverview) => void;
  refreshOverview: () => Promise<void>;
  refreshRecords: () => Promise<void>;
};

export default function Workshop1Panel({
  workshop,
  projectId,
  assessmentId,
  records,
  onRecordsChange,
  refreshOverview,
  refreshRecords,
}: Props) {
  const [generating, setGenerating] = useState(false);
  const [generateMessage, setGenerateMessage] = useState<string | null>(null);
  const upsertRecord = async (
    recordType: string,
    label: string,
    description: string | null,
    properties: Record<string, unknown>,
    existingId?: string
  ) => {
    if (existingId) {
      const updated = await updateEbiosRecord(projectId, assessmentId, existingId, {
        label,
        description,
        properties,
      });
      onRecordsChange(records.map((r) => (r.id === existingId ? updated : r)));
    } else {
      const created = await createEbiosRecord(projectId, assessmentId, {
        workshop_number: 1,
        record_type: recordType,
        label,
        description,
        properties,
      });
      onRecordsChange([...records, created]);
    }
    await refreshOverview();
  };

  const removeRecord = async (id: string) => {
    await deleteEbiosRecord(projectId, assessmentId, id);
    onRecordsChange(records.filter((r) => r.id !== id));
    await refreshOverview();
  };

  const setRecordStatus = async (id: string, status: string) => {
    const updated = await updateEbiosRecord(projectId, assessmentId, id, { status });
    onRecordsChange(records.map((r) => (r.id === id ? updated : r)));
    await refreshOverview();
  };

  const handleValidate = (id: string) => setRecordStatus(id, "validated");
  const handleReject = (id: string) => setRecordStatus(id, "rejected");
  const handleRestore = (id: string) => setRecordStatus(id, "proposed");

  const handleGenerate = async () => {
    setGenerating(true);
    setGenerateMessage(null);
    try {
      const result = await generateEbiosWorkshop1FromCartography(projectId, assessmentId);
      await refreshRecords();
      await refreshOverview();
      setGenerateMessage(
        result.generated_count > 0
          ? `${result.generated_count} proposition(s) générée(s) depuis la cartographie active — à valider ci-dessous.`
          : "Aucune nouvelle proposition : la cartographie active ne contient aucun élément exploitable ou toutes les propositions existent déjà."
      );
    } finally {
      setGenerating(false);
    }
  };

  const saveScope = (data: ScopeFormData, existingId?: string) =>
    upsertRecord(
      "security_scope",
      data.label.trim(),
      data.description.trim() || null,
      {
        business_objectives: data.business_objectives,
        activities: data.activities,
        applications: data.applications,
        sites: data.sites,
        regulatory_constraints: data.regulatory_constraints,
      },
      existingId
    );

  const saveStakeholder = (data: StakeholderFormData, existingId?: string) =>
    upsertRecord(
      "stakeholder",
      data.label.trim(),
      null,
      {
        role: data.role,
        organization: data.organization,
        responsibility: data.responsibility,
        contact: data.contact,
        involvement_level: data.involvement_level,
      },
      existingId
    );

  const saveBaseline = (data: BaselineFormData, existingId?: string) =>
    upsertRecord(
      "security_baseline",
      data.label.trim(),
      data.description.trim() || null,
      {
        domain: data.domain,
        status: data.status,
        maturity_level: data.maturity_level,
        iso27002_ref: data.iso27002_ref,
      },
      existingId
    );

  const saveDocument = (data: DocumentFormData, existingId?: string) =>
    upsertRecord(
      "reference_document",
      data.label.trim(),
      data.comment.trim() || null,
      {
        doc_type: data.doc_type,
        version: data.version,
        date: data.date,
        owner: data.owner,
        link: data.link,
        comment: data.comment,
      },
      existingId
    );

  return (
    <div className="eb-workshop-panel">
      <header className="eb-workshop-panel-header">
        <span className="eb-workshop-badge">Atelier {workshop.number}</span>
        <h2>{workshop.label}</h2>
        <p>{workshop.description}</p>
      </header>

      <div className="eb-workshop1-toolbar">
        <p className="eb-workshop1-toolbar-intro">
          Analysez la cartographie active (organisations, métiers, processus, activités,
          applications, composants techniques) pour proposer automatiquement le périmètre, les
          parties prenantes, le socle de sécurité et compléter les documents de référence. Chaque
          proposition reste à <strong>valider</strong>, <strong>modifier</strong> ou{" "}
          <strong>rejeter</strong> — rien n&apos;est jamais considéré comme acquis.
        </p>
        <button
          type="button"
          className="eb-btn eb-btn-primary"
          onClick={handleGenerate}
          disabled={generating}
        >
          {generating ? "Analyse de la cartographie…" : "🤖 Générer automatiquement depuis la cartographie"}
        </button>
      </div>
      {generateMessage && <p className="eb-urbanism-msg">{generateMessage}</p>}

      <div className="eb-workshop1-grid">
        <ScopeCard
          records={records}
          onSave={saveScope}
          onDelete={removeRecord}
          onValidate={handleValidate}
          onReject={handleReject}
          onRestore={handleRestore}
        />
        <StakeholderCard
          records={records}
          onSave={saveStakeholder}
          onDelete={removeRecord}
          onValidate={handleValidate}
          onReject={handleReject}
          onRestore={handleRestore}
        />
        <BaselineCard
          records={records}
          onSave={saveBaseline}
          onDelete={removeRecord}
          onValidate={handleValidate}
          onReject={handleReject}
          onRestore={handleRestore}
        />
        <DocumentCard
          records={records}
          onSave={saveDocument}
          onDelete={removeRecord}
          onValidate={handleValidate}
          onReject={handleReject}
          onRestore={handleRestore}
        />
      </div>
    </div>
  );
}
