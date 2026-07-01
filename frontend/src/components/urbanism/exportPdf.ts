import { jsPDF } from "jspdf";
import type { UrbanismGraph } from "./metamodel";

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString("fr-FR", { dateStyle: "long", timeStyle: "short" });
}

export async function exportUrbanismPdf(
  graph: UrbanismGraph,
  mapDataUrl: string,
  author?: string
): Promise<void> {
  const doc = new jsPDF({ unit: "mm", format: "a4", orientation: "portrait" });
  const margin = 18;
  let y = 22;

  const authorName = author || graph.author || "Urban Cyber Architect";
  const orgName = graph.organization?.name || "—";

  doc.setFont("helvetica", "bold");
  doc.setFontSize(20);
  doc.text("Cartographie Urbanisme SI", margin, y);
  y += 10;
  doc.setFontSize(10);
  doc.setFont("helvetica", "normal");
  doc.setTextColor(80, 80, 80);
  doc.text("Moteur d'urbanisme Club Urba — Graphe de dépendances", margin, y);
  y += 14;
  doc.setTextColor(0, 0, 0);

  doc.setFont("helvetica", "bold");
  doc.text("Informations projet", margin, y);
  y += 8;
  doc.setFont("helvetica", "normal");
  for (const [label, value] of [
    ["Projet", graph.project_name],
    ["Organisation", orgName],
    ["Date", formatDate(graph.generated_at)],
    ["Auteur", authorName],
  ]) {
    doc.setFont("helvetica", "bold");
    doc.text(`${label} :`, margin, y);
    doc.setFont("helvetica", "normal");
    doc.text(String(value), margin + 40, y);
    y += 7;
  }
  y += 6;

  doc.setFont("helvetica", "bold");
  doc.text("Synthèse quantitative", margin, y);
  y += 8;
  doc.setFont("helvetica", "normal");
  doc.text(`Objets : ${graph.stats.total_objects}`, margin, y);
  y += 6;
  doc.text(`Relations : ${graph.stats.total_relations}`, margin, y);
  y += 6;
  doc.text(`Objets orphelins : ${graph.analysis.orphan_count}`, margin, y);
  y += 6;
  doc.text(`Relations critiques : ${graph.analysis.critical_count}`, margin, y);
  y += 6;
  doc.text(`Incohérences : ${graph.analysis.inconsistency_count}`, margin, y);
  y += 12;

  doc.setFont("helvetica", "bold");
  doc.text("Relations par type", margin, y);
  y += 8;
  doc.setFont("helvetica", "normal");
  doc.setFontSize(9);
  for (const [rtype, count] of Object.entries(graph.stats.by_relation_type).sort((a, b) => b[1] - a[1])) {
    doc.text(`• ${rtype} : ${count}`, margin + 2, y);
    y += 5;
    if (y > 270) break;
  }
  y += 8;
  doc.setFontSize(11);

  doc.setFont("helvetica", "bold");
  doc.text("Légende des types de relations", margin, y);
  y += 8;
  doc.setFont("helvetica", "normal");
  doc.setFontSize(9);
  for (const rt of graph.relation_type_legend.slice(0, 20)) {
    doc.text(`• ${rt}`, margin + 2, y);
    y += 5;
  }

  if (graph.analysis.orphans.length > 0) {
    y += 8;
    doc.setFont("helvetica", "bold");
    doc.setFontSize(11);
    doc.text("Objets orphelins", margin, y);
    y += 7;
    doc.setFont("helvetica", "normal");
    doc.setFontSize(9);
    for (const o of graph.analysis.orphans.slice(0, 8)) {
      doc.text(`• ${o.label} (${o.entity_type})`, margin + 2, y);
      y += 5;
    }
  }

  if (graph.analysis.inconsistencies.length > 0) {
    y += 6;
    doc.setFont("helvetica", "bold");
    doc.setFontSize(11);
    doc.text("Incohérences détectées", margin, y);
    y += 7;
    doc.setFont("helvetica", "normal");
    doc.setFontSize(9);
    for (const inc of graph.analysis.inconsistencies.slice(0, 5)) {
      doc.text(`• ${inc.detail || inc.issue}`, margin + 2, y);
      y += 5;
    }
  }

  doc.addPage("a4", "landscape");
  const landW = doc.internal.pageSize.getWidth();
  const landH = doc.internal.pageSize.getHeight();
  doc.setFont("helvetica", "bold");
  doc.setFontSize(14);
  doc.text(`Cartographie — ${graph.project_name}`, 15, 16);
  doc.setFontSize(9);
  doc.setFont("helvetica", "normal");
  doc.text(`${graph.stats.total_objects} objets · ${graph.stats.total_relations} relations nommées`, 15, 22);

  const img = new Image();
  img.src = mapDataUrl;
  await new Promise<void>((resolve, reject) => {
    img.onload = () => resolve();
    img.onerror = () => reject(new Error("Image load failed"));
  });

  const imgMargin = 12;
  const imgTop = 28;
  const maxImgW = landW - imgMargin * 2;
  const maxImgH = landH - imgTop - imgMargin;
  const ratio = img.width / img.height;
  let drawW = maxImgW;
  let drawH = drawW / ratio;
  if (drawH > maxImgH) {
    drawH = maxImgH;
    drawW = drawH * ratio;
  }
  doc.addImage(mapDataUrl, "PNG", (landW - drawW) / 2, imgTop, drawW, drawH);

  doc.save(`cartographie-urbanisme-${graph.project_name.replace(/\s+/g, "-").toLowerCase()}.pdf`);
}

/** @deprecated */
export const exportClubUrbaPdf = exportUrbanismPdf;
