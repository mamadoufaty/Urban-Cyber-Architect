import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import {
  getEbiosAssessment,
  getEbiosDeliverable,
  getEbiosOverview,
  listCartographies,
  listProjects,
  type Cartography,
  type Project,
} from "../api";
import EbiosDeliverablePreview from "../components/ebios/deliverables/EbiosDeliverablePreview";
import {
  DELIVERABLE_BUTTONS,
  type EbiosDeliverableKind,
  type EbiosDeliverableResponse,
} from "../components/ebios/deliverables/types";
import { resolveDefaultCartographyId, sortCartographies } from "../components/urbanism/cartographySelect";
import GrcRibbon from "../components/grc/GrcRibbon";
import "../styles/livrables.css";
import "../styles/grc.css";
import "../styles/ebios.css";

export default function Livrables() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedId, setSelectedId] = useState(searchParams.get("project") ?? "");
  const [cartographies, setCartographies] = useState<Cartography[]>([]);
  const [selectedCartographyId, setSelectedCartographyId] = useState<string | null>(null);
  const [assessmentId, setAssessmentId] = useState<string | null>(null);
  const [progressPercent, setProgressPercent] = useState<number | null>(null);
  const [preview, setPreview] = useState<EbiosDeliverableResponse | null>(null);
  const [activeKind, setActiveKind] = useState<EbiosDeliverableKind | null>(null);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState<EbiosDeliverableKind | null>(null);
  const [error, setError] = useState<string | null>(null);

  const projectName = useMemo(
    () => projects.find((p) => p.id === selectedId)?.name ?? "—",
    [projects, selectedId]
  );

  const loadContext = useCallback(async () => {
    if (!selectedId) return;
    setLoading(true);
    setError(null);
    try {
      const carts = sortCartographies((await listCartographies(selectedId)).items);
      setCartographies(carts);
      const cartographyId = resolveDefaultCartographyId(carts, selectedCartographyId);
      setSelectedCartographyId(cartographyId);
      const assessment = await getEbiosAssessment(selectedId, cartographyId);
      setAssessmentId(assessment.id);
      const overview = await getEbiosOverview(selectedId, assessment.id);
      setProgressPercent(overview.overall_progress_percent);
    } catch (e) {
      setAssessmentId(null);
      setProgressPercent(null);
      setError(e instanceof Error ? e.message : "Impossible de charger l'étude EBIOS");
    } finally {
      setLoading(false);
    }
  }, [selectedId, selectedCartographyId]);

  useEffect(() => {
    listProjects().then((list) => {
      setProjects(list);
      const fromUrl = searchParams.get("project");
      if (fromUrl && list.some((p) => p.id === fromUrl)) setSelectedId(fromUrl);
      else if (!selectedId && list.length) setSelectedId(list[0].id);
    });
  }, [searchParams]);

  useEffect(() => {
    if (!selectedId) return;
    const params: Record<string, string> = { project: selectedId };
    if (selectedCartographyId) params.cartography = selectedCartographyId;
    setSearchParams(params);
  }, [selectedId, selectedCartographyId, setSearchParams]);

  useEffect(() => {
    const cartFromUrl = searchParams.get("cartography");
    if (cartFromUrl) setSelectedCartographyId(cartFromUrl);
  }, [searchParams]);

  useEffect(() => {
    loadContext();
  }, [loadContext]);

  const handleGenerate = async (kind: EbiosDeliverableKind) => {
    if (!selectedId || !assessmentId) return;
    setGenerating(kind);
    setError(null);
    try {
      const result = await getEbiosDeliverable(selectedId, assessmentId, kind);
      setPreview(result);
      setActiveKind(kind);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Génération impossible");
    } finally {
      setGenerating(null);
    }
  };

  return (
    <div className="livrables-page">
      <GrcRibbon
        projects={projects}
        selectedProjectId={selectedId}
        onProjectChange={setSelectedId}
        moduleLabel="Livrables EBIOS RM"
      />

      <header className="livrables-header">
        <div>
          <h1>Livrables EBIOS RM</h1>
          <p>
            Génération automatique des livrables à partir de l&apos;étude validée — projet {projectName}
          </p>
        </div>
        {assessmentId ? (
          <Link to={`/ebios?project=${selectedId}`} className="livrables-btn livrables-btn-secondary">
            Ouvrir l&apos;étude EBIOS
          </Link>
        ) : null}
      </header>

      {cartographies.length > 1 ? (
        <div className="ebios-deliverable-cartography-bar">
          <label>
            <span>Cartographie</span>
            <select
              className="grc-ribbon-select"
              value={selectedCartographyId ?? ""}
              onChange={(e) => setSelectedCartographyId(e.target.value || null)}
            >
              {cartographies.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name} — v{c.version}
                </option>
              ))}
            </select>
          </label>
        </div>
      ) : null}

      {loading ? <p className="livrables-muted">Chargement de l&apos;étude…</p> : null}

      {progressPercent !== null ? (
        <div className="ebios-deliverable-progress">
          <span>Progression de l&apos;étude :</span>
          <strong>{progressPercent} %</strong>
          {progressPercent < 100 ? (
            <span className="ebios-deliverable-progress-hint">
              — les livrables restent générables mais porteront un avertissement.
            </span>
          ) : (
            <span className="ebios-deliverable-progress-hint status-complete">— étude complète.</span>
          )}
        </div>
      ) : null}

      {error && <div className="livrables-error">{error}</div>}

      <div className="livrables-layout">
        <section className="livrables-list-panel">
          <h2>Générer un livrable</h2>
          <p className="livrables-muted">
            Chaque livrable agrège uniquement les données validées des ateliers 1 à 5.
          </p>
          <ul className="ebios-deliverable-actions">
            {DELIVERABLE_BUTTONS.map((btn) => (
              <li key={btn.kind}>
                <button
                  type="button"
                  className={`livrables-btn ebios-deliverable-action${activeKind === btn.kind ? " active" : ""}`}
                  disabled={!assessmentId || generating !== null}
                  onClick={() => handleGenerate(btn.kind)}
                >
                  {generating === btn.kind ? "Génération…" : btn.label}
                </button>
                <p className="livrables-muted">{btn.description}</p>
              </li>
            ))}
          </ul>
        </section>

        <section className="livrables-preview-panel">
          <h2>Aperçu HTML</h2>
          {!preview ? (
            <p className="livrables-muted">
              Sélectionnez un livrable pour afficher l&apos;aperçu structuré. L&apos;export PDF/DOCX/XLSX
              sera disponible dans une prochaine version.
            </p>
          ) : (
            <EbiosDeliverablePreview deliverable={preview} />
          )}
        </section>
      </div>
    </div>
  );
}
