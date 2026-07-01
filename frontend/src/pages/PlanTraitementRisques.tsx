import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { exportPtr, getPtr, listProjects, patchPtrAction, type Project } from "../api";
import GrcRibbon from "../components/grc/GrcRibbon";
import PtrExportButtons from "../components/grc/ptr/PtrExportButtons";
import PtrFilters from "../components/grc/ptr/PtrFilters";
import PtrHeader from "../components/grc/ptr/PtrHeader";
import PtrSummaryCards from "../components/grc/ptr/PtrSummaryCards";
import PtrTable from "../components/grc/ptr/PtrTable";
import PtrTimelineView from "../components/grc/ptr/PtrTimeline";
import type { PtrKpiKey, PtrQuery, PtrResponse, TimelineScale } from "../components/grc/ptr/types";
import "../styles/grc-ptr.css";
import "../styles/grc.css";

const PAGE_SIZE = 50;

export default function PlanTraitementRisques() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedId, setSelectedId] = useState(searchParams.get("project") ?? "");
  const [data, setData] = useState<PtrResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [exporting, setExporting] = useState<string | null>(null);
  const [savingId, setSavingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [view, setView] = useState<"table" | "timeline">("table");
  const [timelineScale, setTimelineScale] = useState<TimelineScale>("week");

  const [search, setSearch] = useState("");
  const [responsible, setResponsible] = useState("");
  const [organization, setOrganization] = useState("");
  const [priority, setPriority] = useState("");
  const [status, setStatus] = useState("");
  const [treatmentDecision, setTreatmentDecision] = useState("");
  const [dueFilter, setDueFilter] = useState("");
  const [page, setPage] = useState(1);

  const projectName = useMemo(
    () => projects.find((p) => p.id === selectedId)?.name ?? "—",
    [projects, selectedId]
  );

  const query = useMemo<PtrQuery>(
    () => ({
      search: search.trim() || undefined,
      responsible: responsible || undefined,
      organization: organization || undefined,
      priority: priority || undefined,
      status: status || undefined,
      treatment_decision: treatmentDecision || undefined,
      due_filter: (dueFilter || undefined) as PtrQuery["due_filter"],
      page,
      page_size: PAGE_SIZE,
    }),
    [search, responsible, organization, priority, status, treatmentDecision, dueFilter, page]
  );

  const activeKpi = useMemo((): PtrKpiKey | null => {
    if (status === "En cours") return "in_progress";
    if (status === "Terminé") return "completed";
    if (status === "En retard" || dueFilter === "overdue") return "overdue";
    if (!status && !dueFilter && !responsible && !priority && !search) return "total";
    return null;
  }, [status, dueFilter, responsible, priority, search]);

  const loadPtr = useCallback(async () => {
    if (!selectedId) return;
    setLoading(true);
    setError(null);
    try {
      const response = await getPtr(selectedId, query);
      setData(response);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erreur de chargement du PTR");
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
    if (selectedId) loadPtr();
  }, [selectedId, loadPtr]);

  const totalPages = data ? Math.max(1, Math.ceil(data.total / data.page_size)) : 1;

  const handleProjectChange = (id: string) => {
    setSelectedId(id);
    setPage(1);
    setSearchParams(id ? { project: id } : {});
  };

  const resetFilters = () => {
    setSearch("");
    setResponsible("");
    setOrganization("");
    setPriority("");
    setStatus("");
    setTreatmentDecision("");
    setDueFilter("");
    setPage(1);
  };

  const handleKpiClick = (key: PtrKpiKey) => {
    setPage(1);
    if (key === "total") {
      resetFilters();
      return;
    }
    if (key === "in_progress") {
      setStatus("En cours");
      setDueFilter("");
      return;
    }
    if (key === "completed") {
      setStatus("Terminé");
      setDueFilter("");
      return;
    }
    if (key === "overdue") {
      setStatus("");
      setDueFilter("overdue");
    }
  };

  const handleExport = async (format: "csv" | "xlsx" | "pdf") => {
    if (!selectedId) return;
    setExporting(format);
    try {
      await exportPtr(selectedId, format, query);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erreur d'export");
    } finally {
      setExporting(null);
    }
  };

  const handlePatch = async (
    actionId: string,
    patch: { status?: string; progress_percent?: number }
  ) => {
    if (!selectedId) return;
    setSavingId(actionId);
    try {
      await patchPtrAction(selectedId, actionId, patch);
      await loadPtr();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erreur de mise à jour");
    } finally {
      setSavingId(null);
    }
  };

  return (
    <div className="grc-workspace ptr-workspace">
      <GrcRibbon
        projects={projects}
        selectedProjectId={selectedId}
        onProjectChange={handleProjectChange}
        moduleLabel="GRC — Plan de traitement des risques"
      />

      <div className="ptr-page">
        <PtrHeader summary={data?.summary ?? null} projectName={projectName} />

        {selectedId && data && (
          <PtrSummaryCards
            summary={data.summary}
            activeKpi={activeKpi}
            onKpiClick={handleKpiClick}
          />
        )}

        <section className="ptr-toolbar" aria-label="Filtres et exports">
          <PtrFilters
            search={search}
            responsible={responsible}
            organization={organization}
            priority={priority}
            status={status}
            treatmentDecision={treatmentDecision}
            dueFilter={dueFilter}
            filterOptions={data?.filter_options}
            onSearchChange={(v) => { setSearch(v); setPage(1); }}
            onResponsibleChange={(v) => { setResponsible(v); setPage(1); }}
            onOrganizationChange={(v) => { setOrganization(v); setPage(1); }}
            onPriorityChange={(v) => { setPriority(v); setPage(1); }}
            onStatusChange={(v) => { setStatus(v); setPage(1); }}
            onTreatmentDecisionChange={(v) => { setTreatmentDecision(v); setPage(1); }}
            onDueFilterChange={(v) => { setDueFilter(v); setPage(1); }}
            onReset={resetFilters}
          />
          <PtrExportButtons
            disabled={!selectedId}
            exporting={exporting}
            onExport={handleExport}
          />
        </section>

        <div className="ptr-view-toggle">
          <button
            type="button"
            className={`ptr-btn ptr-btn-ghost${view === "table" ? " ptr-view-active" : ""}`}
            onClick={() => setView("table")}
          >
            Tableau
          </button>
          <button
            type="button"
            className={`ptr-btn ptr-btn-ghost${view === "timeline" ? " ptr-view-active" : ""}`}
            onClick={() => setView("timeline")}
          >
            Timeline
          </button>
        </div>

        {error && <div className="ptr-error">{error}</div>}

        <div className="ptr-content">
          {loading && !data && <div className="ptr-loading">Chargement…</div>}
          {data && view === "table" && (
            <>
              <PtrTable
                rows={data.rows}
                editable={data.metadata.limited_edit}
                savingId={savingId}
                onPatch={handlePatch}
              />
              <footer className="ptr-pagination">
                <span>
                  {data.total} action(s) — page {data.page} / {totalPages}
                </span>
                <div className="ptr-pagination-actions">
                  <button
                    type="button"
                    className="ptr-btn ptr-btn-ghost"
                    disabled={page <= 1}
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                  >
                    Précédent
                  </button>
                  <button
                    type="button"
                    className="ptr-btn ptr-btn-ghost"
                    disabled={page >= totalPages}
                    onClick={() => setPage((p) => p + 1)}
                  >
                    Suivant
                  </button>
                </div>
              </footer>
            </>
          )}
          {data && view === "timeline" && (
            <PtrTimelineView
              timeline={data.timeline}
              scale={timelineScale}
              onScaleChange={setTimelineScale}
            />
          )}
          {!loading && !data && selectedId && !error && (
            <div className="ptr-empty">Aucune donnée PTR pour ce projet.</div>
          )}
          {!selectedId && (
            <div className="ptr-empty">
              Sélectionnez un projet — ou <Link to="/projects">créez-en un</Link>.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
