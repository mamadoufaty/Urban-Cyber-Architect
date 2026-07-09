import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import {
  downloadUrbanismImportTemplate,
  executeUrbanismImport,
  listCartographies,
  listProjects,
  previewUrbanismImport,
  type Cartography,
  type Project,
  type UrbanismImportPreview,
  type UrbanismImportReport,
} from "../api";
import { resolveDefaultCartographyId, sortCartographies } from "../components/urbanism/cartographySelect";
import "../styles/urbanism-beta.css";

type Step = "source" | "preview" | "report";

const COUNT_LABELS: Array<[keyof UrbanismImportPreview["counts"], string]> = [
  ["metiers", "Métiers"],
  ["objectifs", "Objectifs"],
  ["processus", "Processus"],
  ["activites", "Activités"],
  ["classes", "Classes"],
  ["organisations", "Organisations"],
  ["operations", "Opérations"],
  ["fonctions", "Fonctions"],
  ["applications", "Applications"],
  ["serveurs", "Serveurs"],
  ["reseaux", "Réseaux"],
  ["sites", "Sites"],
  ["equipements", "Équipements"],
  ["flux", "Flux"],
  ["relations", "Relations"],
];

export default function UrbanismImport() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [projects, setProjects] = useState<Project[]>([]);
  const [projectId, setProjectId] = useState(searchParams.get("project") ?? "");
  const [cartographies, setCartographies] = useState<Cartography[]>([]);
  const [cartographyId, setCartographyId] = useState<string>("");
  const [mode, setMode] = useState<"merge" | "replace">("merge");
  const [file, setFile] = useState<File | null>(null);
  const [step, setStep] = useState<Step>("source");
  const [preview, setPreview] = useState<UrbanismImportPreview | null>(null);
  const [report, setReport] = useState<UrbanismImportReport | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listProjects().then((list) => {
      setProjects(list);
      const fromUrl = searchParams.get("project");
      if (fromUrl && list.some((p) => p.id === fromUrl)) setProjectId(fromUrl);
      else if (!projectId && list.length) setProjectId(list[0].id);
    });
  }, [searchParams]);

  useEffect(() => {
    if (!projectId) {
      setCartographies([]);
      setCartographyId("");
      return;
    }
    listCartographies(projectId).then((res) => {
      setCartographies(res.items);
      setCartographyId((prev) => resolveDefaultCartographyId(res.items, prev) ?? "");
    });
  }, [projectId]);

  const onProjectChange = (id: string) => {
    setProjectId(id);
    setSearchParams(id ? { project: id } : {});
  };

  const onFileChange = (selected: File | null) => {
    setFile(selected);
    setPreview(null);
    setReport(null);
    setStep("source");
    setError(null);
  };

  const runPreview = async () => {
    if (!projectId || !file) return;
    setBusy(true);
    setError(null);
    try {
      const result = await previewUrbanismImport(projectId, file, mode);
      setPreview(result);
      setStep("preview");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Prévisualisation impossible");
    } finally {
      setBusy(false);
    }
  };

  const runImport = async (force = false) => {
    if (!projectId || !file) return;
    setBusy(true);
    setError(null);
    try {
      const result = await executeUrbanismImport(projectId, file, mode, force, cartographyId || undefined);
      setReport(result);
      setStep("report");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Import impossible");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="ua-import-page">
      <header className="ua-import-header">
        <div>
          <h1>Importer une cartographie</h1>
          <p className="ua-import-subtitle">
            Construisez automatiquement la cartographie d&apos;urbanisme SI à partir du modèle Excel ou CSV officiel.
          </p>
        </div>
        <Link
          className="ua-import-link"
          to={
            projectId
              ? `/schema-urbanisme?project=${projectId}${cartographyId ? `&cartography=${cartographyId}` : ""}`
              : "/schema-urbanisme"
          }
        >
          Ouvrir le moteur d&apos;urbanisme
        </Link>
      </header>

      <section className="ua-import-card">
        <h2>1. Projet et mode</h2>
        <div className="ua-import-row">
          <label>
            Projet
            <select value={projectId} onChange={(e) => onProjectChange(e.target.value)}>
              {projects.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
          </label>
          <label>
            Cartographie cible
            <select value={cartographyId} onChange={(e) => setCartographyId(e.target.value)} disabled={!cartographies.length}>
              {sortCartographies(cartographies).map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                  {c.is_active ? " (active)" : ""}
                </option>
              ))}
            </select>
          </label>
          <label>
            Mode d&apos;import
            <select value={mode} onChange={(e) => setMode(e.target.value as "merge" | "replace")}>
              <option value="merge">Fusionner avec la cartographie existante</option>
              <option value="replace">Remplacer complètement la cartographie</option>
            </select>
          </label>
        </div>
        <p className="ua-import-subtitle">
          L&apos;import ne cible que la cartographie sélectionnée — les autres cartographies du projet ne sont
          jamais modifiées.
        </p>
      </section>

      <section className="ua-import-card">
        <h2>2. Fichier source</h2>
        <div className="ua-import-actions">
          <button type="button" className="ua-btn" onClick={() => downloadUrbanismImportTemplate()}>
            Télécharger le modèle Excel
          </button>
          <label className="ua-btn ua-btn-secondary">
            Importer Excel (.xlsx) ou CSV
            <input
              type="file"
              accept=".xlsx,.csv,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,text/csv"
              hidden
              onChange={(e) => onFileChange(e.target.files?.[0] ?? null)}
            />
          </label>
        </div>
        {file && <p className="ua-import-file">Fichier sélectionné : <strong>{file.name}</strong></p>}
        <div className="ua-import-actions">
          <button type="button" className="ua-btn" disabled={!file || !projectId || busy} onClick={runPreview}>
            Prévisualiser les données
          </button>
        </div>
      </section>

      {step === "preview" && preview && (
        <section className="ua-import-card">
          <h2>3. Prévisualisation</h2>
          <div className="ua-import-counts">
            {COUNT_LABELS.map(([key, label]) => (
              <div key={key} className="ua-import-count">
                <span>{label}</span>
                <strong>{preview.counts[key] ?? 0}</strong>
              </div>
            ))}
          </div>
          {preview.issues.length > 0 && (
            <div className="ua-import-issues">
              <h3>Erreurs et avertissements</h3>
              <ul>
                {preview.issues.map((issue, idx) => (
                  <li key={idx} className={issue.severity === "error" ? "error" : "warn"}>
                    [{issue.code}] {issue.message}
                    {issue.sheet ? ` — ${issue.sheet}` : ""}
                    {issue.row ? ` (ligne ${issue.row})` : ""}
                  </li>
                ))}
              </ul>
            </div>
          )}
          <div className="ua-import-actions">
            <button
              type="button"
              className="ua-btn ua-btn-primary"
              disabled={busy || (!preview.can_import && preview.issues.some((i) => i.severity === "error"))}
              onClick={() => runImport(false)}
            >
              Valider et construire la cartographie
            </button>
            {!preview.can_import && (
              <button type="button" className="ua-btn ua-btn-danger" disabled={busy} onClick={() => runImport(true)}>
                Forcer l&apos;import malgré les erreurs
              </button>
            )}
          </div>
        </section>
      )}

      {step === "report" && report && (
        <section className="ua-import-card ua-import-report">
          <h2>4. Rapport d&apos;import</h2>
          <ul className="ua-import-report-list">
            <li>✓ Objets créés : {Object.values(report.created).reduce((a, b) => a + b, 0)}</li>
            <li>✓ Objets mis à jour : {Object.values(report.updated).reduce((a, b) => a + b, 0)}</li>
            <li>✓ Relations créées : {report.relations_created}</li>
            <li>✓ Flux enregistrés : {report.flux_stored}</li>
            <li>✓ Objets orphelins : {report.orphans}</li>
            <li>✓ Incohérences : {report.inconsistencies}</li>
            <li>✓ Taux de complétude : {report.completeness_rate}%</li>
            <li>✓ Progression Urbanisme : {String((report.urbanism_progress as { overall_percent?: number }).overall_percent ?? "—")}%</li>
          </ul>
          <div className="ua-import-actions">
            <Link
              className="ua-btn ua-btn-primary"
              to={`/schema-urbanisme?project=${projectId}${cartographyId ? `&cartography=${cartographyId}` : ""}`}
            >
              Voir la cartographie
            </Link>
          </div>
        </section>
      )}

      {error && <p className="ua-import-error">{error}</p>}
    </div>
  );
}
