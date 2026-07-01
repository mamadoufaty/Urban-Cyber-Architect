import { useEffect, useState } from "react";
import {
  deleteEbiosRiskEvaluation,
  generateEbiosTreatments,
  getEbiosWorkshop5,
  patchEbiosRiskEvaluation,
  patchEbiosTreatmentAction,
  patchEbiosSecurityMeasure,
} from "../../../api";
import type { EbiosWorkshopSpec } from "../types";
import TreatmentEvaluationCard from "./TreatmentEvaluationCard";
import type { Workshop5Data } from "./constants";

type Props = {
  workshop: EbiosWorkshopSpec;
  projectId: string;
  assessmentId: string;
  onRecordsChange: (records: import("../types").EbiosRecord[]) => void;
  refreshOverview: () => Promise<void>;
};

export default function Workshop5Panel({
  workshop,
  projectId,
  assessmentId,
  onRecordsChange,
  refreshOverview,
}: Props) {
  const [data, setData] = useState<Workshop5Data | null>(null);
  const [generating, setGenerating] = useState(false);

  const refresh = async () => {
    const w5 = await getEbiosWorkshop5(projectId, assessmentId);
    setData(w5);
    const flat = w5.evaluations.flatMap((b) => [
      b.evaluation,
      ...b.measures,
      ...b.actions,
      ...(b.residual_risk ? [b.residual_risk] : []),
    ]);
    onRecordsChange(flat);
  };

  useEffect(() => {
    refresh().catch(() => undefined);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId, assessmentId]);

  const handleGenerate = async (regenerate: boolean) => {
    if (regenerate) {
      const ok = window.confirm("Régénérer les évaluations de traitement ? Les données existantes seront remplacées.");
      if (!ok) return;
    }
    setGenerating(true);
    try {
      await generateEbiosTreatments(projectId, assessmentId, regenerate);
      await refresh();
      await refreshOverview();
    } finally {
      setGenerating(false);
    }
  };

  const handleDecision = async (evaluationId: string, decision: string) => {
    await patchEbiosRiskEvaluation(projectId, assessmentId, evaluationId, { treatment_decision: decision });
    await refresh();
    await refreshOverview();
  };

  const handleValidate = async (evaluationId: string) => {
    await patchEbiosRiskEvaluation(projectId, assessmentId, evaluationId, { set_validated: true });
    await refresh();
    await refreshOverview();
  };

  const handleDelete = async (evaluationId: string) => {
    await deleteEbiosRiskEvaluation(projectId, assessmentId, evaluationId);
    await refresh();
    await refreshOverview();
  };

  const handleToggleMeasure = async (measureId: string, retained: boolean) => {
    await patchEbiosSecurityMeasure(projectId, assessmentId, measureId, { retained });
    await refresh();
  };

  const handleActionUpdate = async (actionId: string, field: string, value: string) => {
    const payload: Record<string, unknown> = { [field]: field === "budget" && value ? value : value };
    if (field === "budget" && !value) payload.budget = null;
    await patchEbiosTreatmentAction(projectId, assessmentId, actionId, payload);
    await refresh();
  };

  const evaluations = data?.evaluations ?? [];

  return (
    <div className="eb-workshop-panel">
      <header className="eb-workshop-panel-header">
        <span className="eb-workshop-badge">Atelier {workshop.number}</span>
        <h2>{workshop.label}</h2>
        <p>{workshop.description}</p>
      </header>

      <div className="eb-workshop3-toolbar eb-workshop5-toolbar">
        <p className="eb-workshop3-intro">
          Moteur de décision GRC alimenté par les scénarios opérationnels validés et les acteurs
          urbanisme. {data?.validated_operational_count ?? 0} scénario(s) opérationnel(s) validé(s).
        </p>
        {evaluations.length === 0 ? (
          <button
            type="button"
            className="eb-btn eb-btn-primary"
            disabled={generating || (data?.validated_operational_count ?? 0) === 0}
            onClick={() => handleGenerate(false)}
          >
            {generating ? "Génération…" : "Générer les évaluations de traitement"}
          </button>
        ) : (
          <button
            type="button"
            className="eb-btn eb-btn-ghost"
            disabled={generating}
            onClick={() => handleGenerate(true)}
          >
            {generating ? "Régénération…" : "Régénérer"}
          </button>
        )}
      </div>

      {!evaluations.length ? (
        <div className="eb-card-empty">
          <p>
            Aucune évaluation de traitement. Validez les scénarios opérationnels (atelier 4) puis
            générez les traitements.
          </p>
        </div>
      ) : (
        <div className="eb-treatment-list">
          {evaluations.map((bundle) => (
            <TreatmentEvaluationCard
              key={bundle.evaluation.id}
              bundle={bundle}
              treatmentDecisions={data?.treatment_decisions ?? []}
              onDecisionChange={handleDecision}
              onValidate={handleValidate}
              onDelete={handleDelete}
              onToggleMeasure={handleToggleMeasure}
              onActionUpdate={handleActionUpdate}
            />
          ))}
        </div>
      )}
    </div>
  );
}
