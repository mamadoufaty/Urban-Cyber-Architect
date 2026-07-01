import { useState } from "react";
import { deduplicateUrbanism } from "../../api";
import type { UrbanismAnalysis } from "./metamodel";

interface Props {
  projectId: string;
  analysis: UrbanismAnalysis | null;
  onDeduplicated?: (analysis: UrbanismAnalysis) => void;
  hideDeduplicateButton?: boolean;
}

function normalizeLabel(label: string): string {
  return label
    .trim()
    .toLowerCase()
    .replace(/\s*\([^)]+\)\s*$/, "")
    .replace(/\s+/g, " ");
}

function dedupeOrphans(orphans: UrbanismAnalysis["orphans"]) {
  const seen = new Set<string>();
  return orphans.filter((o) => {
    const key = `${o.entity_type}::${normalizeLabel(o.label)}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

export default function UrbanismAnalysisPanel({ projectId, analysis, onDeduplicated, hideDeduplicateButton }: Props) {
  const [cleaning, setCleaning] = useState(false);
  const [cleanError, setCleanError] = useState<string | null>(null);

  if (!analysis) return null;

  const orphans = dedupeOrphans(analysis.orphans);
  const orphanCount = orphans.length;
  const hasDuplicateOrphans = orphanCount < analysis.orphan_count;

  const hasIssues =
    orphanCount > 0 ||
    analysis.inconsistency_count > 0 ||
    analysis.isolated_couches.length > 0;

  const handleDeduplicate = async () => {
    setCleaning(true);
    setCleanError(null);
    try {
      const result = await deduplicateUrbanism(projectId);
      onDeduplicated?.(result.analysis);
    } catch (e) {
      setCleanError(e instanceof Error ? e.message : "Erreur de déduplication");
    } finally {
      setCleaning(false);
    }
  };

  return (
    <div className="card urbanism-analysis-panel ua-panel">
      <h4 className="urbanism-analysis-title">Analyse temps réel</h4>
      <div className="urbanism-analysis-stats">
        <span>{orphanCount} orphelin(s)</span>
        <span>{analysis.inconsistency_count} incohérence(s)</span>
        <span>{analysis.critical_count} critique(s)</span>
      </div>

      {!hideDeduplicateButton && (hasDuplicateOrphans || orphanCount > 0) && (
        <button
          type="button"
          className="btn btn-secondary btn-sm"
          onClick={handleDeduplicate}
          disabled={cleaning}
        >
          {cleaning ? "Fusion…" : "Fusionner les doublons"}
        </button>
      )}
      {cleanError && <p className="project-error">{cleanError}</p>}

      {!hasIssues && (
        <p className="urbanism-analysis-ok">Graphe cohérent — aucun problème détecté.</p>
      )}

      {orphanCount > 0 && (
        <div className="urbanism-analysis-section">
          <strong>Objets orphelins</strong>
          <ul>
            {orphans.map((o) => (
              <li key={o.id}>{o.label} <em>({o.entity_type})</em></li>
            ))}
          </ul>
        </div>
      )}

      {analysis.inconsistency_count > 0 && (
        <div className="urbanism-analysis-section project-error">
          <strong>Relations invalides</strong>
          <ul>
            {analysis.inconsistencies.map((inc, i) => (
              <li key={i}>{inc.detail ?? inc.issue}</li>
            ))}
          </ul>
        </div>
      )}

      {analysis.isolated_couches.length > 0 && (
        <div className="urbanism-analysis-section">
          <strong>Couches isolées</strong>
          <p>{analysis.isolated_couches.join(", ")}</p>
        </div>
      )}
    </div>
  );
}
