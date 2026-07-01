import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { exportSoa, getSoa, listProjects, type Project } from "../api";
import GrcRibbon from "../components/grc/GrcRibbon";
import SoaExportButtons from "../components/grc/soa/SoaExportButtons";
import SoaFilters from "../components/grc/soa/SoaFilters";
import SoaHeader from "../components/grc/soa/SoaHeader";
import SoaSummaryCards from "../components/grc/soa/SoaSummaryCards";
import SoaTable from "../components/grc/soa/SoaTable";
import type { SoaKpiKey, SoaQuery, SoaResponse } from "../components/grc/soa/types";
import "../styles/grc-soa.css";
import "../styles/grc.css";

const PAGE_SIZE = 50;

export default function StatementOfApplicability() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedId, setSelectedId] = useState(searchParams.get("project") ?? "");
  const [data, setData] = useState<SoaResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [exporting, setExporting] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [search, setSearch] = useState("");
  const [isoReference, setIsoReference] = useState("");
  const [applicable, setApplicable] = useState("");
  const [implemented, setImplemented] = useState("");
  const [responsible, setResponsible] = useState("");
  const [status, setStatus] = useState("");
  const [page, setPage] = useState(1);

  const projectName = useMemo(
    () => projects.find((p) => p.id === selectedId)?.name ?? "—",
    [projects, selectedId]
  );

  const query = useMemo<SoaQuery>(
    () => ({
      search: search.trim() || undefined,
      iso_reference: isoReference || undefined,
      applicable: applicable || undefined,
      implemented: implemented || undefined,
      responsible: responsible || undefined,
      status: status || undefined,
      page,
      page_size: PAGE_SIZE,
    }),
    [search, isoReference, applicable, implemented, responsible, status, page]
  );

  const activeKpi = useMemo((): SoaKpiKey | null => {
    if (applicable === "Oui" && !implemented) return "applicable";
    if (applicable === "Non") return "non_applicable";
    if (implemented === "Oui") return "implemented";
    if (!applicable && !implemented && !isoReference && !responsible && !status && !search) {
      return "total";
    }
    return null;
  }, [applicable, implemented, isoReference, responsible, status, search]);

  const loadSoa = useCallback(async () => {
    if (!selectedId) return;
    setLoading(true);
    setError(null);
    try {
      const response = await getSoa(selectedId, query);
      setData(response);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erreur de chargement de la SoA");
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
  }, [selectedId, setSearchParams]);

  useEffect(() => {
    if (selectedId) loadSoa();
  }, [selectedId, loadSoa]);

  const totalPages = data ? Math.max(1, Math.ceil(data.total / data.page_size)) : 1;

  const handleProjectChange = (id: string) => {
    setSelectedId(id);
    setPage(1);
    setSearchParams(id ? { project: id } : {});
  };

  const resetFilters = () => {
    setSearch("");
    setIsoReference("");
    setApplicable("");
    setImplemented("");
    setResponsible("");
    setStatus("");
    setPage(1);
  };

  const handleKpiClick = (key: SoaKpiKey) => {
    setPage(1);
    if (key === "total") {
      resetFilters();
      return;
    }
    if (key === "applicable") {
      setApplicable("Oui");
      setImplemented("");
      return;
    }
    if (key === "non_applicable") {
      setApplicable("Non");
      setImplemented("");
      return;
    }
    if (key === "implemented") {
      setApplicable("Oui");
      setImplemented("Oui");
    }
  };

  const handleExport = async (format: "csv" | "xlsx" | "pdf") => {
    if (!selectedId) return;
    setExporting(format);
    try {
      await exportSoa(selectedId, format, query);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erreur d'export");
    } finally {
      setExporting(null);
    }
  };

  return (
    <div className="grc-workspace soa-workspace">
      <GrcRibbon
        projects={projects}
        selectedProjectId={selectedId}
        onProjectChange={handleProjectChange}
        moduleLabel="GRC — Déclaration d'applicabilité"
      />

      <div className="soa-page">
        <SoaHeader summary={data?.summary ?? null} projectName={projectName} />

        {selectedId && data && (
          <SoaSummaryCards
            summary={data.summary}
            activeKpi={activeKpi}
            onKpiClick={handleKpiClick}
          />
        )}

        <section className="soa-toolbar" aria-label="Filtres et exports">
          <SoaFilters
            search={search}
            isoReference={isoReference}
            applicable={applicable}
            implemented={implemented}
            responsible={responsible}
            status={status}
            filterOptions={data?.filter_options}
            onSearchChange={(v) => {
              setSearch(v);
              setPage(1);
            }}
            onIsoReferenceChange={(v) => {
              setIsoReference(v);
              setPage(1);
            }}
            onApplicableChange={(v) => {
              setApplicable(v);
              setPage(1);
            }}
            onImplementedChange={(v) => {
              setImplemented(v);
              setPage(1);
            }}
            onResponsibleChange={(v) => {
              setResponsible(v);
              setPage(1);
            }}
            onStatusChange={(v) => {
              setStatus(v);
              setPage(1);
            }}
            onReset={resetFilters}
          />
          <SoaExportButtons
            disabled={!selectedId}
            exporting={exporting}
            onExport={handleExport}
          />
        </section>

        {error && <div className="soa-error">{error}</div>}

        <div className="soa-table-section">
          {loading && !data && <div className="soa-loading">Chargement…</div>}
          {data && (
            <>
              <SoaTable rows={data.rows} />
              <footer className="soa-pagination">
                <span>
                  {data.total} contrôle(s) — page {data.page} / {totalPages}
                </span>
                <div className="soa-pagination-actions">
                  <button
                    type="button"
                    className="soa-btn soa-btn-ghost"
                    disabled={page <= 1}
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                  >
                    Précédent
                  </button>
                  <button
                    type="button"
                    className="soa-btn soa-btn-ghost"
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
            <div className="soa-empty">Aucune donnée disponible pour ce projet.</div>
          )}
          {!selectedId && (
            <div className="soa-empty">
              Sélectionnez un projet dans le ruban — ou{" "}
              <Link to="/projects">créez-en un</Link>.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
