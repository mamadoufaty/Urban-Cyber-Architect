import type { EbiosRecord } from "../types";

export const WORKFLOW_AUTO = "Proposé automatiquement";
export const WORKFLOW_VALIDATED = "Validé";
export const WORKFLOW_MODIFIED = "Modifié";

export type OperationalScenarioFormData = {
  label: string;
  threatening_actor: string;
  entry_point: string;
  target: string;
  impacted_supporting_asset: string;
  attack_path: string;
  technical_event: string;
  consequence: string;
  likelihood: string;
  severity: string;
  calculated_criticality: string;
  comment: string;
  workflow_status: string;
  operational_scenario_uid?: string;
  strategic_scenario_label?: string;
};

export const EMPTY_OPERATIONAL: OperationalScenarioFormData = {
  label: "",
  threatening_actor: "",
  entry_point: "",
  target: "",
  impacted_supporting_asset: "",
  attack_path: "",
  technical_event: "",
  consequence: "",
  likelihood: "Modérée",
  severity: "Modérée",
  calculated_criticality: "Modérée",
  comment: "",
  workflow_status: WORKFLOW_AUTO,
};

const LEVEL_SCORE: Record<string, number> = {
  Faible: 1,
  Modérée: 2,
  Élevée: 3,
  Critique: 4,
};

export function calculateCriticality(severity: string, likelihood: string): string {
  const score = (LEVEL_SCORE[severity] ?? 2) * (LEVEL_SCORE[likelihood] ?? 2);
  if (score <= 4) return "Faible";
  if (score <= 6) return "Modérée";
  if (score <= 9) return "Élevée";
  return "Critique";
}

/** Moteur de génération — remplaçable par OpenAI / Knowledge Graph. */
export function generateOperationalScenario(
  strategic: EbiosRecord,
  riskSourceLabel: string,
  assetLabels: string[],
  stakeholderLabels: string[]
): OperationalScenarioFormData & { operational_scenario_uid: string } {
  const p = strategic.properties ?? {};
  const feared = String(p.feared_event ?? "");
  const severity = String(p.severity ?? "Modérée");
  const likelihood = String(p.likelihood ?? severity);
  const primaryAsset = assetLabels[0] ?? "Bien support critique";
  const primaryStakeholder = stakeholderLabels[0] ?? "SOC";
  const actor = riskSourceLabel.toLowerCase().includes("cyber")
    ? "Cybercriminels spécialisés ransomware"
    : `Acteur externe — ${riskSourceLabel}`;
  const entryPoint =
    actor.toLowerCase().includes("ransom") || actor.toLowerCase().includes("cyber")
      ? "Phishing ciblé"
      : "Exploitation d'une faille exposée";
  const technicalEvent =
    actor.toLowerCase().includes("ransom") || feared.toLowerCase().includes("chiffr")
      ? "Déploiement ransomware"
      : "Compromission du système cible";
  const consequence = feared
    ? `${feared} — impact sur ${primaryStakeholder}`
    : `Indisponibilité opérationnelle — ${primaryStakeholder}`;
  const attackPath = [
    actor,
    entryPoint,
    "Vol d'identifiants",
    "Connexion VPN",
    primaryAsset,
    technicalEvent,
    consequence.split("—")[0].trim(),
  ].join(" → ");

  return {
    operational_scenario_uid: crypto.randomUUID(),
    label: `Scénario opérationnel — ${strategic.label.replace("Scénario stratégique — ", "")}`,
    threatening_actor: actor,
    entry_point: entryPoint,
    target: primaryAsset,
    impacted_supporting_asset: primaryAsset,
    attack_path: attackPath,
    technical_event: technicalEvent,
    consequence,
    likelihood,
    severity,
    calculated_criticality: calculateCriticality(severity, likelihood),
    comment: "",
    workflow_status: WORKFLOW_AUTO,
    strategic_scenario_label: strategic.label,
  };
}

export function operationalFromRecord(record: EbiosRecord): OperationalScenarioFormData {
  const p = record.properties ?? {};
  return {
    label: record.label,
    threatening_actor: String(p.threatening_actor ?? ""),
    entry_point: String(p.entry_point ?? ""),
    target: String(p.target ?? ""),
    impacted_supporting_asset: String(p.impacted_supporting_asset ?? ""),
    attack_path: String(p.attack_path ?? record.description ?? ""),
    technical_event: String(p.technical_event ?? ""),
    consequence: String(p.consequence ?? ""),
    likelihood: String(p.likelihood ?? "Modérée"),
    severity: String(p.severity ?? "Modérée"),
    calculated_criticality: String(p.calculated_criticality ?? "Modérée"),
    comment: String(p.comment ?? ""),
    workflow_status: String(p.workflow_status ?? WORKFLOW_AUTO),
    operational_scenario_uid: p.operational_scenario_uid
      ? String(p.operational_scenario_uid)
      : undefined,
    strategic_scenario_label: p.strategic_scenario_label
      ? String(p.strategic_scenario_label)
      : undefined,
  };
}

export const STATUS_CLASS: Record<string, string> = {
  [WORKFLOW_AUTO]: "status-auto",
  [WORKFLOW_VALIDATED]: "status-validated",
  [WORKFLOW_MODIFIED]: "status-modified",
};

export const CRITICALITY_CLASS: Record<string, string> = {
  Faible: "severity-low",
  Modérée: "severity-moderate",
  Élevée: "severity-high",
  Critique: "severity-critical",
};
