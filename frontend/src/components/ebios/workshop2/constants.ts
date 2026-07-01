export const SEVERITY_LEVELS = ["Faible", "Modérée", "Élevée", "Critique"] as const;

export type RiskSourceFormData = {
  label: string;
  target_objective: string;
  feared_event: string;
  stakeholder_ids: string[];
  supporting_asset_ids: string[];
  severity: string;
  comment: string;
};

export const EMPTY_RISK_SOURCE: RiskSourceFormData = {
  label: "",
  target_objective: "",
  feared_event: "",
  stakeholder_ids: [],
  supporting_asset_ids: [],
  severity: "Modérée",
  comment: "",
};

export function riskSourceFromRecord(record: import("../types").EbiosRecord): RiskSourceFormData {
  const p = record.properties ?? {};
  return {
    label: record.label,
    target_objective: String(p.target_objective ?? ""),
    feared_event: String(p.feared_event ?? ""),
    stakeholder_ids: Array.isArray(p.stakeholder_ids) ? p.stakeholder_ids.map(String) : [],
    supporting_asset_ids: Array.isArray(p.supporting_asset_ids)
      ? p.supporting_asset_ids.map(String)
      : [],
    severity: String(p.severity ?? "Modérée"),
    comment: String(p.comment ?? record.description ?? ""),
  };
}

export function isRiskSourceComplete(record: import("../types").EbiosRecord): boolean {
  const data = riskSourceFromRecord(record);
  return (
    data.label.trim() !== "" &&
    data.target_objective.trim() !== "" &&
    data.feared_event.trim() !== "" &&
    SEVERITY_LEVELS.includes(data.severity as (typeof SEVERITY_LEVELS)[number]) &&
    data.stakeholder_ids.length > 0 &&
    data.supporting_asset_ids.length > 0
  );
}

export const SEVERITY_CLASS: Record<string, string> = {
  Faible: "severity-low",
  Modérée: "severity-moderate",
  Élevée: "severity-high",
  Critique: "severity-critical",
};
