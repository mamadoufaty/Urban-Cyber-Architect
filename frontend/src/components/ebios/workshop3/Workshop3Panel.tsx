import { useState } from "react";
import {
  createEbiosRecord,
  deleteEbiosRecord,
  generateEbiosStrategicScenarios,
  getEbiosRecords,
  updateEbiosRecord,
} from "../../../api";
import type { EbiosRecord, EbiosWorkshopSpec } from "../types";
import StrategicScenarioList, { StrategicScenarioCreateModal } from "./StrategicScenarioList";
import {
  EMPTY_SCENARIO,
  WORKFLOW_PROPOSED,
  WORKFLOW_VALIDATED,
  generateStrategicScenario,
  scenarioFromRecord,
  type StrategicScenarioFormData,
} from "./constants";

type Props = {
  workshop: EbiosWorkshopSpec;
  projectId: string;
  assessmentId: string;
  records: EbiosRecord[];
  workshop1Records: EbiosRecord[];
  workshop2Records: EbiosRecord[];
  onRecordsChange: (records: EbiosRecord[]) => void;
  refreshOverview: () => Promise<void>;
};

export default function Workshop3Panel({
  workshop,
  projectId,
  assessmentId,
  records,
  workshop1Records,
  workshop2Records,
  onRecordsChange,
  refreshOverview,
}: Props) {
  const scenarios = records.filter((r) => r.record_type === "strategic_scenario");
  const riskSources = workshop2Records.filter((r) => r.record_type === "risk_source");
  const stakeholders = workshop1Records.filter((r) => r.record_type === "stakeholder");
  const assets = workshop2Records.filter((r) => r.record_type === "supporting_asset");

  const [generating, setGenerating] = useState(false);
  const [createOpen, setCreateOpen] = useState(false);
  const [createBusy, setCreateBusy] = useState(false);
  const [createForm, setCreateForm] = useState<StrategicScenarioFormData>(EMPTY_SCENARIO);

  const refreshWorkshop3 = async () => {
    const recs = await getEbiosRecords(projectId, assessmentId, 3);
    onRecordsChange(recs);
  };

  const buildProperties = (data: StrategicScenarioFormData, existing?: EbiosRecord) => {
    const riskSource = riskSources.find((r) => r.id === data.risk_source_id);
    const existingProps = existing?.properties ?? {};
    return {
      ...existingProps,
      scenario_uid: data.scenario_uid ?? crypto.randomUUID(),
      risk_source_id: data.risk_source_id,
      risk_source_label: riskSource?.label ?? "",
      motivation: data.motivation,
      target_objective: data.target_objective,
      strategic_objective: data.strategic_objective,
      targeted_essential_asset: data.targeted_essential_asset,
      feared_event: data.feared_event,
      narrative_description: data.narrative_description,
      stakeholder_ids: data.stakeholder_ids,
      supporting_asset_ids: data.supporting_asset_ids,
      severity: data.severity,
      likelihood: data.likelihood,
      comment: data.comment,
      workflow_status: data.workflow_status,
      scenario_seed: {
        strategic_scenario_uid: data.scenario_uid ?? crypto.randomUUID(),
        operational_ready: true,
        risk_source_id: data.risk_source_id,
      },
    };
  };

  const handleGenerate = async (regenerate: boolean) => {
    if (regenerate) {
      const ok = window.confirm(
        "Régénérer tous les scénarios ? Les scénarios existants seront remplacés."
      );
      if (!ok) return;
    }
    setGenerating(true);
    try {
      await generateEbiosStrategicScenarios(projectId, assessmentId, regenerate);
      await refreshWorkshop3();
      await refreshOverview();
    } finally {
      setGenerating(false);
    }
  };

  const handleSave = async (data: StrategicScenarioFormData, existingId?: string) => {
    const existing = existingId ? scenarios.find((s) => s.id === existingId) : undefined;
    const properties = buildProperties(data, existing);
    if (existingId) {
      await updateEbiosRecord(projectId, assessmentId, existingId, {
        label: data.label.trim(),
        description: data.narrative_description.trim() || null,
        properties,
      });
    } else {
      await createEbiosRecord(projectId, assessmentId, {
        workshop_number: 3,
        record_type: "strategic_scenario",
        label: data.label.trim(),
        description: data.narrative_description.trim() || null,
        properties,
        status: "proposed",
      });
    }
    await refreshWorkshop3();
    await refreshOverview();
  };

  const setRecordStatus = async (id: string, status: string, workflowStatus?: string) => {
    const record = scenarios.find((s) => s.id === id);
    if (!record) return;
    const properties = buildProperties(scenarioFromRecord(record), record);
    if (workflowStatus) properties.workflow_status = workflowStatus;
    await updateEbiosRecord(projectId, assessmentId, id, { status, properties });
    await refreshWorkshop3();
    await refreshOverview();
  };

  const handleValidate = (id: string) => setRecordStatus(id, "validated", WORKFLOW_VALIDATED);
  const handleReject = (id: string) => setRecordStatus(id, "rejected");
  const handleRestore = (id: string) => setRecordStatus(id, "proposed");

  const handleDelete = async (id: string) => {
    await deleteEbiosRecord(projectId, assessmentId, id);
    await refreshWorkshop3();
    await refreshOverview();
  };

  const openCreate = () => {
    const firstSource = riskSources[0];
    if (firstSource) {
      const generated = generateStrategicScenario(firstSource, stakeholders, assets, { auto: false });
      setCreateForm({ ...generated, workflow_status: WORKFLOW_PROPOSED });
    } else {
      setCreateForm({ ...EMPTY_SCENARIO, workflow_status: WORKFLOW_PROPOSED });
    }
    setCreateOpen(true);
  };

  const submitCreate = async () => {
    if (!createForm.label.trim()) return;
    setCreateBusy(true);
    try {
      await handleSave(createForm);
      setCreateOpen(false);
    } finally {
      setCreateBusy(false);
    }
  };

  return (
    <div className="eb-workshop-panel">
      <header className="eb-workshop-panel-header">
        <span className="eb-workshop-badge">Atelier {workshop.number}</span>
        <h2>{workshop.label}</h2>
        <p>{workshop.description}</p>
      </header>

      <div className="eb-workshop3-toolbar">
        <p className="eb-workshop3-intro">
          Scénarios stratégiques générés à partir des sources de risque. Validez chaque scénario pour
          progresser vers l&apos;atelier 4.
        </p>
        {scenarios.length === 0 ? (
          <button
            type="button"
            className="eb-btn eb-btn-primary"
            onClick={() => handleGenerate(false)}
            disabled={generating || !riskSources.length}
          >
            {generating ? "Génération…" : "🤖 Générer les scénarios stratégiques"}
          </button>
        ) : (
          <button
            type="button"
            className="eb-btn eb-btn-ghost"
            onClick={() => handleGenerate(true)}
            disabled={generating}
          >
            {generating ? "Régénération…" : "Régénérer"}
          </button>
        )}
      </div>

      <StrategicScenarioList
        scenarios={scenarios}
        riskSources={riskSources}
        onSave={handleSave}
        onValidate={handleValidate}
        onReject={handleReject}
        onRestore={handleRestore}
        onDelete={handleDelete}
        onCreateNew={openCreate}
      />

      <StrategicScenarioCreateModal
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        form={createForm}
        setForm={setCreateForm}
        riskSources={riskSources}
        onSubmit={submitCreate}
        busy={createBusy}
      />
    </div>
  );
}
