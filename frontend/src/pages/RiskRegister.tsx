import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import {
  exportRiskRegister,
  getRiskRegister,
  listProjects,
  type Project,
} from "../api";
import GrcRibbon from "../components/grc/GrcRibbon";
import RegisterKpiCards, { type RegisterKpiKey } from "../components/grc/RegisterKpiCards";
import RiskRegisterTable from "../components/grc/RiskRegisterTable";
import type { RiskRegisterQuery, RiskRegisterResponse, RiskRegisterRow, RiskRegisterSortField } from "../components/grc/types";
import "../styles/grc-dashboard.css";
import "../styles/grc.css";

const PAGE_SIZE = 25;

function criticalityBucket(label: string): string {
  const normalized = label.trim();
  if (["Critique", "Élevée", "Modérée", "Faible"].includes(normalized)) return normalized;
  return "Modérée";
}

function computeKpisFromRows(rows: RiskRegisterRow[], totalRisks: number) {
  return {
    total: totalRisks,
    critical: rows.filter((r) => criticalityBucket(r.criticality) === "Critique").length,
    high: rows.filter((r) => criticalityBucket(r.criticality) === "Élevée").length,
    moderate: rows.filter((r) => criticalityBucket(r.criticality) === "Modérée").length,
    low: rows.filter((r) => criticalityBucket(r.criticality) === "Faible").length,
  };
}

function globalRiskLevel(stats: {
  total: number;
  critical: number;
  high: number;
  moderate: number;
}): string {
  if (stats.total === 0) return "Faible";
  if (stats.critical > 0) return "Critique";
  if (stats.high > 0) return "Élevé";
  if (stats.moderate > 0) return "Modéré";
  return "Faible";
}

function formatLastUpdate(rows: RiskRegisterRow[], fallback?: string): string {
  if (!rows.length) {
    if (!fallback) return "—";
    return new Date(fallback).toLocaleString("fr-FR", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  }
  const max = rows.reduce((acc, row) => {
    const t = new Date(row.updated_at).getTime();
    return t > acc ? t : acc;
  }, 0);
  return new Date(max).toLocaleString("fr-FR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function RiskRegister() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedId, setSelectedId] = useState(searchParams.get("project") ?? "");
  const [data, setData] = useState<RiskRegisterResponse | null>(null);
  const [snapshot, setSnapshot] = useState<RiskRegisterResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [exporting, setExporting] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [search, setSearch] = useState("");
  const [organization, setOrganization] = useState("");
  const [severity, setSeverity] = useState("");
  const [criticality, setCriticality] = useState("");
  const [treatmentDecision, setTreatmentDecision] = useState("");
  const [status, setStatus] = useState("");
  const [sortBy, setSortBy] = useState<RiskRegisterSortField>("updated_at");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");
  const [page, setPage] = useState(1);

  const projectName = useMemo(
    () => projects.find((p) => p.id === selectedId)?.name ?? "—",
    [projects, selectedId]
  );

  const query = useMemo<RiskRegisterQuery>(
    () => ({
      search: search.trim() || undefined,
      organization: organization || undefined,
      severity: severity || undefined,
      criticality: criticality || undefined,
      treatment_decision: treatmentDecision || undefined,
      status: status || undefined,
      sort_by: sortBy,
      sort_dir: sortDir,
      page,
      page_size: PAGE_SIZE,
    }),
    [search, organization, severity, criticality, treatmentDecision, status, sortBy, sortDir, page]
  );

  const kpiStats = useMemo(() => {
    if (!snapshot) {
      return { total: 0, critical: 0, high: 0, moderate: 0, low: 0 };
    }
    return computeKpisFromRows(snapshot.rows, snapshot.metadata.total_risks);
  }, [snapshot]);

  const lastUpdated = useMemo(
    () => formatLastUpdate(snapshot?.rows ?? [], snapshot?.metadata.generated_at),
    [snapshot]
  );

  const activeKpi = useMemo((): RegisterKpiKey | null => {
    if (criticality === "Critique") return "critical";
    if (criticality === "Élevée") return "high";
    if (criticality === "Modérée") return "moderate";
    if (criticality === "Faible") return "low";
    if (!criticality && !severity && !status) return "total";
    return null;
  }, [criticality, severity, status]);

  const executiveSummary = useMemo(() => {
    const level = globalRiskLevel(kpiStats);
    if (kpiStats.total === 0) {
      return "Le registre ne contient aucun risque consolidé pour ce projet. Les risques sont alimentés automatiquement depuis EBIOS RM et le moteur d'urbanisme.";
    }
    return `Le registre contient ${kpiStats.total} risque${kpiStats.total > 1 ? "s" : ""}, dont ${kpiStats.critical} critique${kpiStats.critical > 1 ? "s" : ""} et ${kpiStats.high} élevé${kpiStats.high > 1 ? "s" : ""}. Le niveau global du projet est ${level}. Les risques sont alimentés automatiquement depuis EBIOS RM et le moteur d'urbanisme.`;
  }, [kpiStats]);

  const loadSnapshot = useCallback(async (projectId: string) => {
    try {
      const response = await getRiskRegister(projectId, {
        page: 1,
        page_size: 200,
        sort_by: "updated_at",
        sort_dir: "desc",
      });
      setSnapshot(response);
    } catch {
      setSnapshot(null);
    }
  }, []);

  const loadRegister = useCallback(async () => {
    if (!selectedId) return;
    setLoading(true);
    setError(null);
    try {
      const response = await getRiskRegister(selectedId, query);
      setData(response);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erreur de chargement du registre");
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [selectedId, query]);

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
    setSearchParams({ project: selectedId });
    loadSnapshot(selectedId);
  }, [selectedId, loadSnapshot, setSearchParams]);

  useEffect(() => {
    if (selectedId) loadRegister();
  }, [selectedId, loadRegister]);

  const totalPages = data ? Math.max(1, Math.ceil(data.total / data.page_size)) : 1;

  const handleProjectChange = (id: string) => {
    setSelectedId(id);
    setPage(1);
    setSearchParams(id ? { project: id } : {});
  };

  const handleSort = (field: RiskRegisterSortField) => {
    if (sortBy === field) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortBy(field);
      setSortDir("asc");
    }
    setPage(1);
  };

  const handleExport = async (format: "csv" | "xlsx" | "pdf") => {
    if (!selectedId) return;
    setExporting(format);
    try {
      await exportRiskRegister(selectedId, format, query);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erreur d'export");
    } finally {
      setExporting(null);
    }
  };

  const resetFilters = () => {
    setSearch("");
    setOrganization("");
    setSeverity("");
    setCriticality("");
    setTreatmentDecision("");
    setStatus("");
    setPage(1);
  };

  const handleKpiClick = (key: RegisterKpiKey) => {
    setPage(1);
    if (key === "total") {
      setSeverity("");
      setCriticality("");
      setStatus("");
      return;
    }
    const criticalityByKey: Record<Exclude<RegisterKpiKey, "total">, string> = {
      critical: "Critique",
      high: "Élevée",
      moderate: "Modérée",
      low: "Faible",
    };
    setCriticality(criticalityByKey[key]);
  };

  return (
    <div className="grc-workspace">
      <GrcRibbon
        projects={projects}
        selectedProjectId={selectedId}
        onProjectChange={handleProjectChange}
      />

      <div className="grc-page">
        <header className="grc-header">
          <h1>Registre des risques</h1>
          <dl className="grc-header-meta">
            <div className="grc-header-meta-row">
              <dt>Projet</dt>
              <dd>{projectName}</dd>
            </div>
            <div className="grc-header-meta-row">
              <dt>Nombre total de risques</dt>
              <dd>{snapshot?.metadata.total_risks ?? 0}</dd>
            </div>
            <div className="grc-header-meta-row">
              <dt>Dernière mise à jour</dt>
              <dd>
                <time dateTime={snapshot?.metadata.generated_at}>{lastUpdated}</time>
              </dd>
            </div>
          </dl>
        </header>

        {selectedId && (
          <>
            <RegisterKpiCards
              total={kpiStats.total}
              critical={kpiStats.critical}
              high={kpiStats.high}
              moderate={kpiStats.moderate}
              low={kpiStats.low}
              ptrOpen="—"
              activeKpi={activeKpi}
              onKpiClick={handleKpiClick}
            />
            <p className="grc-executive-summary">{executiveSummary}</p>
          </>
        )}

        <section className="grc-toolbar" aria-label="Filtres et exports">
          <div className="grc-filters">
            <input
              type="search"
              className="grc-field grc-search"
              placeholder="Recherche"
              aria-label="Recherche"
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setPage(1);
              }}
            />
            <select
              className="grc-field"
              aria-label="Organisation"
              value={organization}
              onChange={(e) => { setOrganization(e.target.value); setPage(1); }}
            >
              <option value="">Organisation</option>
              {data?.filter_options.organizations.map((o) => (
                <option key={o} value={o}>{o}</option>
              ))}
            </select>
            <select
              className="grc-field"
              aria-label="Gravité"
              value={severity}
              onChange={(e) => { setSeverity(e.target.value); setPage(1); }}
            >
              <option value="">Gravité</option>
              {data?.filter_options.severities.map((v) => (
                <option key={v} value={v}>{v}</option>
              ))}
            </select>
            <select
              className="grc-field"
              aria-label="Criticité"
              value={criticality}
              onChange={(e) => { setCriticality(e.target.value); setPage(1); }}
            >
              <option value="">Criticité</option>
              {data?.filter_options.criticalities.map((v) => (
                <option key={v} value={v}>{v}</option>
              ))}
            </select>
            <select
              className="grc-field"
              aria-label="Décision"
              value={treatmentDecision}
              onChange={(e) => { setTreatmentDecision(e.target.value); setPage(1); }}
            >
              <option value="">Décision</option>
              {data?.filter_options.treatment_decisions.map((v) => (
                <option key={v} value={v}>{v}</option>
              ))}
            </select>
            <select
              className="grc-field"
              aria-label="Statut"
              value={status}
              onChange={(e) => { setStatus(e.target.value); setPage(1); }}
            >
              <option value="">Statut</option>
              {data?.filter_options.statuses.map((v) => (
                <option key={v} value={v}>{v}</option>
              ))}
            </select>
            <button type="button" className="grc-dash-btn grc-dash-btn-ghost" onClick={resetFilters}>
              Réinitialiser
            </button>
          </div>
          <div className="grc-exports">
            {(
              [
                ["csv", "Exporter CSV"],
                ["xlsx", "Exporter Excel"],
                ["pdf", "Exporter PDF"],
              ] as const
            ).map(([format, label]) => (
              <button
                key={format}
                type="button"
                className="grc-dash-btn grc-dash-btn-export"
                disabled={!selectedId || !!exporting}
                onClick={() => handleExport(format)}
              >
                {exporting === format ? "Export…" : label}
              </button>
            ))}
          </div>
        </section>

        {error && <div className="grc-error">{error}</div>}

        <div className="grc-table-section">
          {loading && !data && <div className="grc-loading-inline">Chargement…</div>}
          {data && (
            <>
              <RiskRegisterTable
                rows={data.rows}
                sortBy={sortBy}
                sortDir={sortDir}
                onSort={handleSort}
              />
              <footer className="grc-pagination">
                <span>
                  {data.total} résultat(s) — page {data.page} / {totalPages}
                </span>
                <div className="grc-pagination-actions">
                  <button
                    type="button"
                    className="grc-dash-btn grc-dash-btn-ghost"
                    disabled={page <= 1}
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                  >
                    Précédent
                  </button>
                  <button
                    type="button"
                    className="grc-dash-btn grc-dash-btn-ghost"
                    disabled={page >= totalPages}
                    onClick={() => setPage((p) => p + 1)}
                  >
                    Suivant
                  </button>
                </div>
              </footer>
            </>
          )}
          {!loading && !data && selectedId && !error && (
            <div className="grc-empty">Aucune donnée disponible pour ce projet.</div>
          )}
          {!selectedId && (
            <div className="grc-empty">
              Sélectionnez un projet dans le ruban — ou{" "}
              <Link to="/projects">créez-en un</Link>.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
