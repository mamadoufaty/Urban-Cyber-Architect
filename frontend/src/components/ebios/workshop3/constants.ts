import type { EbiosRecord } from "../types";

export const LIKELIHOOD_LEVELS = ["Faible", "Modérée", "Élevée", "Critique"] as const;

export const WORKFLOW_AUTO = "Proposé automatiquement";
export const WORKFLOW_PROPOSED = "Proposé";
export const WORKFLOW_MODIFIED = "Modifié";
export const WORKFLOW_VALIDATED = "Validé";

export type StrategicScenarioFormData = {
  label: string;
  risk_source_id: string;
  target_objective: string;
  feared_event: string;
  narrative_description: string;
  stakeholder_ids: string[];
  supporting_asset_ids: string[];
  severity: string;
  likelihood: string;
  comment: string;
  workflow_status: string;
  scenario_uid?: string;
};

export const EMPTY_SCENARIO: StrategicScenarioFormData = {
  label: "",
  risk_source_id: "",
  target_objective: "",
  feared_event: "",
  narrative_description: "",
  stakeholder_ids: [],
  supporting_asset_ids: [],
  severity: "Modérée",
  likelihood: "Modérée",
  comment: "",
  workflow_status: WORKFLOW_PROPOSED,
};

const SEVERITY_TO_LIKELIHOOD: Record<string, string> = {
  Faible: "Faible",
  Modérée: "Modérée",
  Élevée: "Élevée",
  Critique: "Critique",
};

function labelsForIds(records: EbiosRecord[], ids: string[]): string[] {
  const idSet = new Set(ids.map(String));
  return records.filter((r) => idSet.has(r.id)).map((r) => r.label);
}

/** Moteur de génération — remplaçable par OpenAI / Gemini. */
export function generateStrategicScenario(
  riskSource: EbiosRecord,
  stakeholderRecords: EbiosRecord[],
  assetRecords: EbiosRecord[],
  options?: { auto?: boolean }
): StrategicScenarioFormData & { scenario_uid: string } {
  const auto = options?.auto ?? true;
  const p = riskSource.properties ?? {};
  const stakeholderIds = Array.isArray(p.stakeholder_ids) ? p.stakeholder_ids.map(String) : [];
  const assetIds = Array.isArray(p.supporting_asset_ids) ? p.supporting_asset_ids.map(String) : [];
  const severity = String(p.severity ?? "Modérée");
  const target = String(p.target_objective ?? "").trim();
  const feared = String(p.feared_event ?? "").trim();
  const sourceLabel = riskSource.label.trim();

  const stakeholderNames = labelsForIds(stakeholderRecords, stakeholderIds);
  const assetNames = labelsForIds(assetRecords, assetIds);
  const stakeholdersText = stakeholderNames.length
    ? stakeholderNames.join(", ")
    : "les parties prenantes identifiées";
  const assetsText = assetNames.length ? assetNames.join(", ") : "les biens supports concernés";

  const scenario_uid = crypto.randomUUID();
  const label = `Scénario stratégique — ${sourceLabel}`;
  const narrative = (
    `Dans le contexte de l'analyse EBIOS RM, la source de risque « ${sourceLabel} » ` +
    `poursuit l'objectif suivant : ${target}. ` +
    `L'événement redouté est : ${feared}. ` +
    `Ce scénario stratégique décrit comment cette menace pourrait affecter ${assetsText}, ` +
    `avec des impacts significatifs pour ${stakeholdersText}. ` +
    `La gravité estimée est ${severity}, nécessitant une évaluation approfondie ` +
    `des mesures de sécurité existantes et des scénarios opérationnels associés.`
  );

  return {
    scenario_uid,
    label,
    risk_source_id: riskSource.id,
    target_objective: target,
    feared_event: feared,
    narrative_description: narrative,
    stakeholder_ids: stakeholderIds,
    supporting_asset_ids: assetIds,
    severity,
    likelihood: SEVERITY_TO_LIKELIHOOD[severity] ?? "Modérée",
    comment: "",
    workflow_status: auto ? WORKFLOW_AUTO : WORKFLOW_PROPOSED,
  };
}

export function scenarioFromRecord(record: EbiosRecord): StrategicScenarioFormData {
  const p = record.properties ?? {};
  return {
    label: record.label,
    risk_source_id: String(p.risk_source_id ?? ""),
    target_objective: String(p.target_objective ?? ""),
    feared_event: String(p.feared_event ?? ""),
    narrative_description: String(p.narrative_description ?? record.description ?? ""),
    stakeholder_ids: Array.isArray(p.stakeholder_ids) ? p.stakeholder_ids.map(String) : [],
    supporting_asset_ids: Array.isArray(p.supporting_asset_ids)
      ? p.supporting_asset_ids.map(String)
      : [],
    severity: String(p.severity ?? "Modérée"),
    likelihood: String(p.likelihood ?? "Modérée"),
    comment: String(p.comment ?? ""),
    workflow_status: String(p.workflow_status ?? WORKFLOW_PROPOSED),
    scenario_uid: p.scenario_uid ? String(p.scenario_uid) : undefined,
  };
}

export const STATUS_CLASS: Record<string, string> = {
  [WORKFLOW_AUTO]: "status-auto",
  [WORKFLOW_PROPOSED]: "status-proposed",
  [WORKFLOW_MODIFIED]: "status-modified",
  [WORKFLOW_VALIDATED]: "status-validated",
};
