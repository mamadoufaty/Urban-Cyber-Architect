import type { UrbanismGraph } from "./metamodel";

/** Nom de fichier d'export : cartographie + version sélectionnées uniquement (§11). */
export function buildExportFilename(graph: UrbanismGraph, extension: string): string {
  const project = graph.project_name.replace(/\s+/g, "-").toLowerCase();
  const cartography = graph.cartography?.name.replace(/\s+/g, "-").toLowerCase() ?? "cartographie";
  const version = graph.cartography_version?.version ?? "1.0";
  return `${project}-${cartography}-v${version}.${extension}`;
}

export function graphToJsonString(graph: UrbanismGraph): string {
  return JSON.stringify(graph, null, 2);
}

function csvEscape(value: unknown): string {
  const str = value === null || value === undefined ? "" : String(value);
  if (/[",\n;]/.test(str)) {
    return `"${str.replace(/"/g, '""')}"`;
  }
  return str;
}

/** Deux sections (objets puis relations) dans un même fichier CSV, séparées par
 * une ligne vide — reste ouvert à un futur export ArchiMate dédié (§11). */
export function graphToCsvString(graph: UrbanismGraph): string {
  const nodeHeader = ["id", "type", "couche", "label"];
  const nodeRows = graph.nodes.map((n) => [n.id, n.entity_type, n.couche, n.label].map(csvEscape).join(","));

  const edgeHeader = ["id", "source", "target", "relation_type", "category", "criticite"];
  const edgeRows = graph.edges.map((e) =>
    [e.id, e.source, e.target, e.relation_type, e.category, e.criticite ?? ""].map(csvEscape).join(",")
  );

  return [
    "# Objets",
    nodeHeader.join(","),
    ...nodeRows,
    "",
    "# Relations",
    edgeHeader.join(","),
    ...edgeRows,
  ].join("\n");
}

export function downloadTextFile(filename: string, content: string, mime: string): void {
  const blob = new Blob([content], { type: mime });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}
