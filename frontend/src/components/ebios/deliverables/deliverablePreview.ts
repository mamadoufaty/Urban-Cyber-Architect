import type { EbiosDeliverableResponse } from "./types";

/** Extrait les colonnes tabulaires d'un livrable (registre, PTR). */
export function deliverableTableColumns(
  deliverable: EbiosDeliverableResponse
): Array<{ key: string; label: string }> {
  const columns = deliverable.data.columns;
  if (!Array.isArray(columns)) return [];
  return columns
    .filter((c): c is { key: string; label: string } => Boolean(c && typeof c === "object" && "key" in c))
    .map((c) => ({ key: String(c.key), label: String(c.label) }));
}

/** Extrait les lignes tabulaires d'un livrable. */
export function deliverableTableRows(
  deliverable: EbiosDeliverableResponse
): Array<Record<string, unknown>> {
  const rows = deliverable.data.rows;
  if (!Array.isArray(rows)) return [];
  return rows.filter((r): r is Record<string, unknown> => Boolean(r && typeof r === "object"));
}

/** KPIs de la synthèse COMEX. */
export function executiveSummaryKpis(
  deliverable: EbiosDeliverableResponse
): Record<string, number> | null {
  const kpis = deliverable.data.kpis;
  if (!kpis || typeof kpis !== "object") return null;
  return kpis as Record<string, number>;
}

/** Indique si le livrable doit afficher un tableau de données. */
export function deliverableHasTable(deliverable: EbiosDeliverableResponse): boolean {
  return deliverableTableRows(deliverable).length > 0 && deliverableTableColumns(deliverable).length > 0;
}
