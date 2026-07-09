import { useState } from "react";
import {
  createEbiosRecord,
  deleteEbiosRecord,
  generateEbiosWorkshop2RiskSources,
  getEbiosRecords,
  updateEbiosRecord,
} from "../../../api";
import type { EbiosRecord, EbiosWorkshopSpec } from "../types";
import RiskSourceCard from "./RiskSourceCard";
import SupportingAssetsBanner from "./SupportingAssetsBanner";
import type { RiskSourceFormData } from "./constants";

type Props = {
  workshop: EbiosWorkshopSpec;
  projectId: string;
  assessmentId: string;
  records: EbiosRecord[];
  workshop1Records: EbiosRecord[];
  onRecordsChange: (records: EbiosRecord[]) => void;
  refreshOverview: () => Promise<void>;
};

export default function Workshop2Panel({
  workshop,
  projectId,
  assessmentId,
  records,
  workshop1Records,
  onRecordsChange,
  refreshOverview,
}: Props) {
  const [generating, setGenerating] = useState(false);
  const [generateMessage, setGenerateMessage] = useState<string | null>(null);
  const supportingAssets = records.filter((r) => r.record_type === "supporting_asset");
  const riskSources = records.filter((r) => r.record_type === "risk_source");

  const validatedCount = riskSources.filter((r) => r.status === "validated").length;
  const toReviewCount = riskSources.filter((r) => r.status === "proposed").length;
  const rejectedCount = riskSources.filter((r) => r.status === "rejected").length;
  const concernedStakeholderIds = new Set<string>();
  riskSources.forEach((r) => {
    const ids = r.properties?.stakeholder_ids;
    if (Array.isArray(ids)) ids.forEach((id) => concernedStakeholderIds.add(String(id)));
  });

  const refreshWorkshop2Records = async () => {
    const recs = await getEbiosRecords(projectId, assessmentId, 2);
    onRecordsChange(recs);
  };

  const handleGenerate = async () => {
    setGenerating(true);
    setGenerateMessage(null);
    try {
      const result = await generateEbiosWorkshop2RiskSources(projectId, assessmentId);
      await refreshWorkshop2Records();
      await refreshOverview();
      setGenerateMessage(
        result.generated_count > 0
          ? `${result.generated_count} source(s) de risque générée(s) — à valider ci-dessous.`
          : "Aucune nouvelle source de risque : toutes les propositions existent déjà ou la cartographie active ne contient aucun élément exploitable."
      );
    } finally {
      setGenerating(false);
    }
  };

  const setRecordStatus = async (id: string, status: string) => {
    await updateEbiosRecord(projectId, assessmentId, id, { status });
    await refreshWorkshop2Records();
    await refreshOverview();
  };

  const handleValidate = (id: string) => setRecordStatus(id, "validated");
  const handleReject = (id: string) => setRecordStatus(id, "rejected");
  const handleRestore = (id: string) => setRecordStatus(id, "proposed");

  const saveRiskSource = async (data: RiskSourceFormData, existingId?: string) => {
    const properties = {
      target_objective: data.target_objective,
      feared_event: data.feared_event,
      stakeholder_ids: data.stakeholder_ids,
      supporting_asset_ids: data.supporting_asset_ids,
      severity: data.severity,
      comment: data.comment,
      scenario_seed: { strategic_ready: true, operational_ready: false },
    };

    if (existingId) {
      await updateEbiosRecord(projectId, assessmentId, existingId, {
        label: data.label.trim(),
        description: data.comment.trim() || null,
        properties,
      });
    } else {
      await createEbiosRecord(projectId, assessmentId, {
        workshop_number: 2,
        record_type: "risk_source",
        label: data.label.trim(),
        description: data.comment.trim() || null,
        properties,
      });
    }
    await refreshWorkshop2Records();
    await refreshOverview();
  };

  const removeRecord = async (id: string) => {
    await deleteEbiosRecord(projectId, assessmentId, id);
    await refreshWorkshop2Records();
    await refreshOverview();
  };

  return (
    <div className="eb-workshop-panel">
      <header className="eb-workshop-panel-header">
        <span className="eb-workshop-badge">Atelier {workshop.number}</span>
        <h2>{workshop.label}</h2>
        <p>{workshop.description}</p>
      </header>

      {riskSources.length > 0 && (
        <div className="eb-workshop2-summary">
          <div className="eb-workshop2-summary-item">
            <strong>{riskSources.length}</strong>
            <span>Source(s) générée(s)</span>
          </div>
          <div className="eb-workshop2-summary-item summary-validated">
            <strong>{validatedCount}</strong>
            <span>Validée(s)</span>
          </div>
          <div className="eb-workshop2-summary-item summary-proposed">
            <strong>{toReviewCount}</strong>
            <span>À revoir</span>
          </div>
          <div className="eb-workshop2-summary-item summary-rejected">
            <strong>{rejectedCount}</strong>
            <span>Rejetée(s)</span>
          </div>
          <div className="eb-workshop2-summary-item">
            <strong>{supportingAssets.length}</strong>
            <span>Bien(s) support utilisé(s)</span>
          </div>
          <div className="eb-workshop2-summary-item">
            <strong>{concernedStakeholderIds.size}</strong>
            <span>Partie(s) prenante(s) concernée(s)</span>
          </div>
        </div>
      )}

      <SupportingAssetsBanner
        projectId={projectId}
        assessmentId={assessmentId}
        assetCount={supportingAssets.length}
        onSyncComplete={refreshWorkshop2Records}
      />

      <div className="eb-workshop2-toolbar">
        <p className="eb-workshop2-toolbar-intro">
          Analysez l&apos;Atelier 1 validé, la cartographie active et les biens supports
          synchronisés pour proposer automatiquement des sources de risque, leurs objectifs
          visés et événements redoutés, reliés aux biens supports et parties prenantes
          concernés. Chaque proposition reste à <strong>valider</strong>, <strong>modifier</strong>{" "}
          ou <strong>rejeter</strong> — rien n&apos;est jamais considéré comme acquis.
        </p>
        <button
          type="button"
          className="eb-btn eb-btn-primary"
          onClick={handleGenerate}
          disabled={generating}
        >
          {generating ? "Analyse en cours…" : "🤖 Générer les sources de risque"}
        </button>
      </div>
      {generateMessage && <p className="eb-urbanism-msg">{generateMessage}</p>}

      <div className="eb-workshop2-content">
        <RiskSourceCard
          records={records}
          stakeholders={workshop1Records.filter((r) => r.record_type === "stakeholder")}
          supportingAssets={supportingAssets}
          onSave={saveRiskSource}
          onDelete={removeRecord}
          onValidate={handleValidate}
          onReject={handleReject}
          onRestore={handleRestore}
        />
      </div>
    </div>
  );
}
