import {
  createEbiosRecord,
  deleteEbiosRecord,
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
  const supportingAssets = records.filter((r) => r.record_type === "supporting_asset");

  const refreshWorkshop2Records = async () => {
    const recs = await getEbiosRecords(projectId, assessmentId, 2);
    onRecordsChange(recs);
  };

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

      <SupportingAssetsBanner
        projectId={projectId}
        assessmentId={assessmentId}
        assetCount={supportingAssets.length}
        onSyncComplete={refreshWorkshop2Records}
      />

      <div className="eb-workshop2-content">
        <RiskSourceCard
          records={records}
          stakeholders={workshop1Records.filter((r) => r.record_type === "stakeholder")}
          supportingAssets={supportingAssets}
          onSave={saveRiskSource}
          onDelete={removeRecord}
        />
      </div>
    </div>
  );
}
