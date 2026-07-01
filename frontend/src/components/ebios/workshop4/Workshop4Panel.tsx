import { useEffect, useState } from "react";
import {
  deleteEbiosOperationalScenario,
  generateEbiosOperationalScenarios,
  getEbiosWorkshop4,
  patchEbiosOperationalScenario,
} from "../../../api";
import type { EbiosRecord, EbiosWorkshopSpec } from "../types";
import OperationalScenarioList from "./OperationalScenarioList";
import { calculateCriticality, type OperationalScenarioFormData } from "./constants";

type Props = {
  workshop: EbiosWorkshopSpec;
  projectId: string;
  assessmentId: string;
  onRecordsChange: (records: EbiosRecord[]) => void;
  refreshOverview: () => Promise<void>;
};

export default function Workshop4Panel({
  workshop,
  projectId,
  assessmentId,
  onRecordsChange,
  refreshOverview,
}: Props) {
  const [scenarios, setScenarios] = useState<EbiosRecord[]>([]);
  const [validatedStrategicCount, setValidatedStrategicCount] = useState(0);
  const [generating, setGenerating] = useState(false);

  const refreshWorkshop4 = async () => {
    const data = await getEbiosWorkshop4(projectId, assessmentId);
    setScenarios(data.scenarios);
    setValidatedStrategicCount(data.validated_strategic_count);
    onRecordsChange(data.scenarios);
  };

  useEffect(() => {
    refreshWorkshop4().catch(() => undefined);
    // eslint-disable-next-line react-hooks/exhaustive-deps -- chargement à l'ouverture
  }, [projectId, assessmentId]);

  const handleGenerate = async (regenerate: boolean) => {
    if (regenerate) {
      const ok = window.confirm(
        "Régénérer tous les scénarios opérationnels ? Les scénarios existants seront remplacés."
      );
      if (!ok) return;
    }
    setGenerating(true);
    try {
      await generateEbiosOperationalScenarios(projectId, assessmentId, regenerate);
      await refreshWorkshop4();
      await refreshOverview();
    } finally {
      setGenerating(false);
    }
  };

  const buildProperties = (data: OperationalScenarioFormData, existing?: EbiosRecord) => {
    const base = existing?.properties ?? {};
    return {
      ...base,
      threatening_actor: data.threatening_actor,
      entry_point: data.entry_point,
      target: data.target,
      impacted_supporting_asset: data.impacted_supporting_asset,
      attack_path: data.attack_path,
      technical_event: data.technical_event,
      consequence: data.consequence,
      likelihood: data.likelihood,
      severity: data.severity,
      calculated_criticality: calculateCriticality(data.severity, data.likelihood),
      comment: data.comment,
    };
  };

  const handleSave = async (data: OperationalScenarioFormData, id: string) => {
    const existing = scenarios.find((s) => s.id === id);
    await patchEbiosOperationalScenario(projectId, assessmentId, id, {
      label: data.label.trim(),
      properties: buildProperties(data, existing),
    });
    await refreshWorkshop4();
    await refreshOverview();
  };

  const handleValidate = async (id: string) => {
    await patchEbiosOperationalScenario(projectId, assessmentId, id, { set_validated: true });
    await refreshWorkshop4();
    await refreshOverview();
  };

  const handleDelete = async (id: string) => {
    await deleteEbiosOperationalScenario(projectId, assessmentId, id);
    await refreshWorkshop4();
    await refreshOverview();
  };

  return (
    <div className="eb-workshop-panel">
      <header className="eb-workshop-panel-header">
        <span className="eb-workshop-badge">Atelier {workshop.number}</span>
        <h2>{workshop.label}</h2>
        <p>{workshop.description}</p>
      </header>

      <div className="eb-workshop3-toolbar eb-workshop4-toolbar">
        <p className="eb-workshop3-intro">
          {validatedStrategicCount} scénario(s) stratégique(s) validé(s) — {scenarios.length}{" "}
          scénario(s) opérationnel(s). Validez chaque scénario pour déverrouiller l&apos;atelier 5.
        </p>
        {scenarios.length === 0 ? (
          <button
            type="button"
            className="eb-btn eb-btn-primary"
            onClick={() => handleGenerate(false)}
            disabled={generating || validatedStrategicCount === 0}
          >
            {generating ? "Génération…" : "Générer les scénarios opérationnels"}
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

      <OperationalScenarioList
        scenarios={scenarios}
        onSave={handleSave}
        onValidate={handleValidate}
        onDelete={handleDelete}
      />
    </div>
  );
}
