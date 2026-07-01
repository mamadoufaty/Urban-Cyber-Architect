export const TREATMENT_DECISIONS = ["Accepter", "Réduire", "Transférer", "Éviter"] as const;

export const WORKFLOW_AUTO = "Proposé automatiquement";
export const WORKFLOW_VALIDATED = "Validé";

export type UrbanismActorRef = {
  id: string;
  label: string;
  entity_type: string;
  description?: string | null;
  couche?: string | null;
};

export type Workshop5Bundle = {
  evaluation: import("../types").EbiosRecord;
  measures: import("../types").EbiosRecord[];
  actions: import("../types").EbiosRecord[];
  residual_risk: import("../types").EbiosRecord | null;
};

export type Workshop5Data = {
  evaluations: Workshop5Bundle[];
  validated_operational_count: number;
  urbanism_acteurs: UrbanismActorRef[];
  treatment_decisions: string[];
};

/** Moteur de mesures — remplaçable par IA / Knowledge Graph. */
export function generateSecurityMeasures(operationalProps: Record<string, unknown>) {
  const entry = String(operationalProps.entry_point ?? "").toLowerCase();
  const technical = String(operationalProps.technical_event ?? "").toLowerCase();
  const measures: Array<{ label: string; description: string; framework_refs: Record<string, string> }> = [];

  if (entry.includes("phishing")) {
    measures.push({
      label: "Sensibilisation anti-phishing",
      description: "Formation des utilisateurs.",
      framework_refs: { iso27002: "6.3", nist_csf: "PR.AT-1", cis_controls: "CIS 14.1", anssi: "Hygène" },
    });
  }
  if (technical.includes("ransom")) {
    measures.push({
      label: "Sauvegardes isolées",
      description: "Tests de restauration réguliers.",
      framework_refs: { iso27002: "8.13", nist_csf: "PR.IP-4", cis_controls: "CIS 11.1", anssi: "Continuité" },
    });
  }
  if (!measures.length) {
    measures.push({
      label: "Revue des contrôles de sécurité",
      description: "Renforcer les mesures sur le périmètre.",
      framework_refs: { iso27002: "5.36", nist_csf: "ID.RA-5", cis_controls: "CIS 1.1", anssi: "EBIOS" },
    });
  }
  return measures;
}

export function actorLabel(actor: Record<string, unknown> | null | undefined): string {
  return actor ? String(actor.label ?? "—") : "—";
}
