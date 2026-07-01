import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import {
  getEbiosAssessment,
  getEbiosExtensions,
  getEbiosMetamodel,
  getEbiosOverview,
  getEbiosRecords,
  listProjects,
  type Project,
} from "../api";
import EbiosExtensionPanel from "../components/ebios/EbiosExtensionPanel";
import EbiosProgressBar from "../components/ebios/EbiosProgressBar";
import EbiosRibbon from "../components/ebios/EbiosRibbon";
import EbiosWorkshopNav from "../components/ebios/EbiosWorkshopNav";
import EbiosWorkshopPanel from "../components/ebios/EbiosWorkshopPanel";
import { EBIOS_WORKSHOPS_FALLBACK } from "../components/ebios/constants";
import type {
  EbiosAssessment,
  EbiosExtensionRegistry,
  EbiosMetamodel,
  EbiosOverview,
  EbiosRecord,
} from "../components/ebios/types";
import "../styles/ebios.css";

export default function EbiosRm() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedId, setSelectedId] = useState(searchParams.get("project") ?? "");
  const [metamodel, setMetamodel] = useState<EbiosMetamodel | null>(null);
  const [extensions, setExtensions] = useState<EbiosExtensionRegistry | null>(null);
  const [assessment, setAssessment] = useState<EbiosAssessment | null>(null);
  const [overview, setOverview] = useState<EbiosOverview | null>(null);
  const [records, setRecords] = useState<EbiosRecord[]>([]);
  const [workshop1Records, setWorkshop1Records] = useState<EbiosRecord[]>([]);
  const [workshop2Records, setWorkshop2Records] = useState<EbiosRecord[]>([]);
  const [activeWorkshop, setActiveWorkshop] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const workshops = metamodel?.workshops ?? EBIOS_WORKSHOPS_FALLBACK;
  const activeSpec = workshops.find((w) => w.number === activeWorkshop) ?? workshops[0];

  const workshopStatuses = useMemo(() => {
    const map = new Map<number, string>();
    overview?.workshops.forEach((w) => map.set(w.workshop_number, w.status));
    return map;
  }, [overview]);

  const loadGlobal = useCallback(async () => {
    const [mm, ext] = await Promise.all([getEbiosMetamodel(), getEbiosExtensions()]);
    setMetamodel(mm);
    setExtensions(ext);
  }, []);

  const loadProjectData = useCallback(async (projectId: string) => {
    setLoading(true);
    setError(null);
    try {
      const ass = await getEbiosAssessment(projectId);
      setAssessment(ass);
      setActiveWorkshop(ass.current_workshop);
      const [ov, recs] = await Promise.all([
        getEbiosOverview(projectId, ass.id),
        getEbiosRecords(projectId, ass.id, ass.current_workshop),
      ]);
      setOverview(ov);
      setRecords(recs);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erreur de chargement EBIOS");
    } finally {
      setLoading(false);
    }
  }, []);

  const loadWorkshopRecords = useCallback(
    async (workshopNumber: number) => {
      if (!selectedId || !assessment) return;
      try {
        const recs = await getEbiosRecords(selectedId, assessment.id, workshopNumber);
        setRecords(recs);
        if (workshopNumber === 2) {
          const w1 = await getEbiosRecords(selectedId, assessment.id, 1);
          setWorkshop1Records(w1);
        }
        if (workshopNumber === 3) {
          const [w1, w2] = await Promise.all([
            getEbiosRecords(selectedId, assessment.id, 1),
            getEbiosRecords(selectedId, assessment.id, 2),
          ]);
          setWorkshop1Records(w1);
          setWorkshop2Records(w2);
        }
      } catch {
        setRecords([]);
      }
    },
    [assessment, selectedId]
  );

  useEffect(() => {
    listProjects().then((list) => {
      setProjects(list);
      const fromUrl = searchParams.get("project");
      if (fromUrl && list.some((p) => p.id === fromUrl)) setSelectedId(fromUrl);
      else if (!selectedId && list.length) setSelectedId(list[0].id);
    });
    loadGlobal().catch(() => undefined);
  }, [searchParams]);

  useEffect(() => {
    if (!selectedId) return;
    loadProjectData(selectedId);
  }, [selectedId, loadProjectData]);

  useEffect(() => {
    if (!selectedId || !assessment) return;
    loadWorkshopRecords(activeWorkshop);
  }, [activeWorkshop, assessment, selectedId, loadWorkshopRecords]);

  const handleProjectChange = (id: string) => {
    setSelectedId(id);
    setSearchParams(id ? { project: id } : {});
  };

  const refreshOverview = useCallback(async () => {
    if (!selectedId || !assessment) return;
    const ov = await getEbiosOverview(selectedId, assessment.id);
    setOverview(ov);
  }, [assessment, selectedId]);

  const refreshRecords = useCallback(async () => {
    if (!selectedId || !assessment) return;
    const recs = await getEbiosRecords(selectedId, assessment.id, activeWorkshop);
    setRecords(recs);
  }, [activeWorkshop, assessment, selectedId]);

  const handleWorkshopSelect = (number: number) => {
    const status = workshopStatuses.get(number) ?? "locked";
    if (status === "locked") return;
    setActiveWorkshop(number);
  };

  return (
    <div className="eb-workspace">
      <EbiosRibbon
        projects={projects}
        selectedProjectId={selectedId}
        onProjectChange={handleProjectChange}
        assessmentTitle={assessment?.title ?? "Analyse EBIOS RM"}
        overallProgress={overview?.overall_progress_percent ?? 0}
      />

      {!projects.length && (
        <div className="eb-panel eb-empty">
          <p>
            Aucun projet — <Link to="/projects">créer un projet</Link> pour démarrer une analyse EBIOS RM.
          </p>
        </div>
      )}

      {error && <div className="eb-panel eb-error">{error}</div>}

      {selectedId && (
        <div className="eb-body">
          <div className="eb-main">
            {loading && !overview && <div className="eb-panel">Chargement de l&apos;analyse…</div>}

            {overview && (
              <>
                <EbiosProgressBar
                  workshops={overview.workshops}
                  overallPercent={overview.overall_progress_percent}
                />

                <EbiosWorkshopNav
                  workshops={workshops}
                  activeWorkshop={activeWorkshop}
                  onSelect={handleWorkshopSelect}
                  workshopStatuses={workshopStatuses}
                />

                {activeSpec && assessment && (
                  <EbiosWorkshopPanel
                    workshop={activeSpec}
                    records={records}
                    metamodel={metamodel}
                    projectId={selectedId}
                    assessmentId={assessment.id}
                    workshop1Records={workshop1Records}
                    workshop2Records={workshop2Records}
                    onRecordsChange={setRecords}
                    onOverviewChange={setOverview}
                    refreshOverview={refreshOverview}
                    refreshRecords={refreshRecords}
                  />
                )}

                <footer className="eb-stats">
                  <span>{overview.link_count} liens</span>
                  <span>
                    {Object.values(overview.record_counts_by_workshop).reduce((a, b) => a + b, 0)} entités
                  </span>
                  <span>Version {assessment?.version ?? "1.0"}</span>
                </footer>
              </>
            )}
          </div>

          {extensions && (
            <EbiosExtensionPanel
              modules={extensions.future_modules}
              integrations={extensions.integrations}
            />
          )}
        </div>
      )}
    </div>
  );
}
