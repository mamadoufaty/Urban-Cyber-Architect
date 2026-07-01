import { useCallback, useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { getRssiDashboard, listProjects, type Project } from "../api";
import ComexSummaryPanel from "../components/grc/ComexSummaryPanel";
import ExposurePanel from "../components/grc/ExposurePanel";
import KpiCards from "../components/grc/KpiCards";
import PtrTrackingPanel from "../components/grc/PtrTrackingPanel";
import RiskHeatmapPanel from "../components/grc/RiskHeatmapPanel";
import TopRisksPanel from "../components/grc/TopRisksPanel";
import type { RssiDashboardResponse } from "../components/grc/dashboardTypes";
import "../styles/grc-dashboard.css";

export default function DashboardRssi() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedId, setSelectedId] = useState(searchParams.get("project") ?? "");
  const [data, setData] = useState<RssiDashboardResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadDashboard = useCallback(async () => {
    if (!selectedId) return;
    setLoading(true);
    setError(null);
    try {
      const response = await getRssiDashboard(selectedId);
      setData(response);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erreur de chargement du dashboard");
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [selectedId]);

  useEffect(() => {
    listProjects().then(setProjects).catch(() => setProjects([]));
  }, []);

  useEffect(() => {
    if (selectedId) {
      setSearchParams({ project: selectedId });
      loadDashboard();
    }
  }, [selectedId, loadDashboard, setSearchParams]);

  return (
    <div className="grc-dash-page">
      <header className="grc-dash-header">
        <div>
          <p className="grc-dash-eyebrow">GRC — Cybersécurité</p>
          <h1>Dashboard RSSI / COMEX</h1>
          <p className="grc-dash-subtitle">
            Tableau de bord exécutif en lecture seule, alimenté par le{" "}
            <Link to={`/registre-risques${selectedId ? `?project=${selectedId}` : ""}`}>
              registre des risques
            </Link>
            . Les modifications se font dans EBIOS RM et l&apos;urbanisme.
          </p>
        </div>
        <div className="grc-dash-header-actions">
          <label className="grc-dash-project-select">
            Projet
            <select
              value={selectedId}
              onChange={(e) => setSelectedId(e.target.value)}
            >
              <option value="">Sélectionner un projet…</option>
              {projects.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
          </label>
          <button type="button" className="grc-dash-btn" onClick={loadDashboard} disabled={!selectedId || loading}>
            Actualiser
          </button>
        </div>
      </header>

      {data?.metadata.read_only && (
        <div className="grc-dash-readonly-banner" role="status">
          Lecture seule — généré le{" "}
          {new Date(data.metadata.generated_at).toLocaleString("fr-FR")}
        </div>
      )}

      {error && <div className="grc-dash-error">{error}</div>}
      {loading && <div className="grc-dash-loading">Chargement du dashboard…</div>}

      {!loading && data && (
        <>
          <KpiCards kpis={data.kpis} />

          <div className="grc-dash-layout">
            <div className="grc-dash-main">
              <RiskHeatmapPanel heatmap={data.heatmap} />
              <TopRisksPanel items={data.top_risks} />
              <PtrTrackingPanel tracking={data.ptr_tracking} />
            </div>
            <aside className="grc-dash-aside">
              <ComexSummaryPanel
                comex={data.comex}
                projectName={data.metadata.project_name}
                exportEndpoints={data.metadata.export_endpoints}
              />
              <ExposurePanel title="Exposition par organisation" items={data.exposure_by_organization} />
              <ExposurePanel title="Biens supports exposés" items={data.exposure_by_supporting_asset} />
            </aside>
          </div>
        </>
      )}
    </div>
  );
}
