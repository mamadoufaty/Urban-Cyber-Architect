import { useCallback, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import {
  exportDeliverable,
  generateDeliverable,
  getDeliverable,
  getDeliverables,
  listProjects,
  type DeliverableContent,
  type DeliverableSummary,
  type Project,
} from "../api";
import CreateDeliverableModal from "../components/deliverables/CreateDeliverableModal";
import GrcRibbon from "../components/grc/GrcRibbon";
import "../styles/livrables.css";
import "../styles/grc.css";

function formatDate(value: string) {
  try {
    return new Date(value).toLocaleString("fr-FR");
  } catch {
    return value;
  }
}

function typeLabel(types: { id: string; label: string }[], id: string) {
  return types.find((t) => t.id === id)?.label ?? id;
}

export default function Livrables() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedId, setSelectedId] = useState(searchParams.get("project") ?? "");
  const [items, setItems] = useState<DeliverableSummary[]>([]);
  const [types, setTypes] = useState<{ id: string; label: string }[]>([]);
  const [loading, setLoading] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [preview, setPreview] = useState<DeliverableContent | null>(null);
  const [selectedDeliverableId, setSelectedDeliverableId] = useState<string | null>(null);
  const [exporting, setExporting] = useState(false);

  const projectName = useMemo(
    () => projects.find((p) => p.id === selectedId)?.name ?? "—",
    [projects, selectedId]
  );

  const loadDeliverables = useCallback(async () => {
    if (!selectedId) return;
    setLoading(true);
    setError(null);
    try {
      const data = await getDeliverables(selectedId);
      setItems(data.deliverables);
      setTypes(data.types);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erreur de chargement");
      setItems([]);
    } finally {
      setLoading(false);
    }
  }, [selectedId]);

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
    loadDeliverables();
  }, [loadDeliverables]);

  const handleGenerate = async (
    payload: Parameters<typeof generateDeliverable>[1],
    action: "generate" | "preview"
  ) => {
    if (!selectedId) return;
    setBusy(true);
    setError(null);
    try {
      const result = await generateDeliverable(selectedId, payload);
      setPreview(result.generated_content);
      if (action === "generate" && result.deliverable) {
        setSelectedDeliverableId(result.deliverable.id);
        setModalOpen(false);
        await loadDeliverables();
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Génération impossible");
    } finally {
      setBusy(false);
    }
  };

  const handleExportPdf = async (deliverableId?: string | null) => {
    const id = deliverableId ?? selectedDeliverableId;
    if (!selectedId || !id) return;
    setExporting(true);
    setError(null);
    try {
      await exportDeliverable(selectedId, id, "pdf");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Export PDF échoué");
    } finally {
      setExporting(false);
    }
  };

  return (
    <div className="livrables-page">
      <GrcRibbon
        projects={projects}
        selectedProjectId={selectedId}
        onProjectChange={setSelectedId}
        moduleLabel="Livrables — Générateur documentaire"
      />

      <header className="livrables-header">
        <div>
          <h1>Livrables</h1>
          <p>Générateur documentaire piloté par le besoin utilisateur — projet {projectName}</p>
        </div>
        <button type="button" className="livrables-btn" onClick={() => setModalOpen(true)}>
          + Nouveau livrable
        </button>
      </header>

      {error && <div className="livrables-error">{error}</div>}

      <div className="livrables-layout">
        <section className="livrables-list-panel">
          <h2>Livrables générés</h2>
          {loading && <p className="livrables-muted">Chargement…</p>}
          {!loading && items.length === 0 && (
            <p className="livrables-muted">Aucun livrable pour ce projet. Créez-en un avec le bouton ci-dessus.</p>
          )}
          <ul className="livrables-list">
            {items.map((item) => (
              <li key={item.id}>
                <button
                  type="button"
                  className={`livrables-list-item${selectedDeliverableId === item.id ? " active" : ""}`}
                  onClick={() => {
                    setSelectedDeliverableId(item.id);
                    setPreview(null);
                  }}
                >
                  <strong>{item.title}</strong>
                  <span>{typeLabel(types, item.deliverable_type)}</span>
                  <small>{formatDate(item.created_at)}</small>
                </button>
              </li>
            ))}
          </ul>
        </section>

        <section className="livrables-preview-panel">
          <div className="livrables-preview-toolbar">
            <h2>Aperçu</h2>
            {selectedDeliverableId && (
              <button
                type="button"
                className="livrables-btn livrables-btn-secondary"
                disabled={exporting}
                onClick={() => handleExportPdf(selectedDeliverableId)}
              >
                {exporting ? "Export…" : "Exporter PDF"}
              </button>
            )}
          </div>

          {!preview && !selectedDeliverableId && (
            <p className="livrables-muted">Prévisualisez ou sélectionnez un livrable généré.</p>
          )}

          {preview && (
            <DeliverablePreview content={preview} onExportPdf={() => handleExportPdf(selectedDeliverableId)} />
          )}

          {!preview && selectedDeliverableId && (
            <DeliverableDetailLoader
              projectId={selectedId}
              deliverableId={selectedDeliverableId}
              onExportPdf={() => handleExportPdf(selectedDeliverableId)}
              exporting={exporting}
            />
          )}
        </section>
      </div>

      <CreateDeliverableModal
        open={modalOpen}
        types={types}
        onClose={() => setModalOpen(false)}
        onSubmit={handleGenerate}
        busy={busy}
      />
    </div>
  );
}

function DeliverablePreview({
  content,
  onExportPdf,
}: {
  content: DeliverableContent;
  onExportPdf?: () => void;
}) {
  return (
    <article className="livrables-document">
      <header>
        <h3>{content.title}</h3>
        {content.metadata?.generated_at && (
          <p className="livrables-muted">Généré le {formatDate(String(content.metadata.generated_at))}</p>
        )}
        {onExportPdf && (
          <button type="button" className="livrables-btn livrables-btn-secondary" onClick={onExportPdf}>
            Exporter PDF
          </button>
        )}
      </header>
      {content.user_need && (
        <section>
          <h4>Besoin utilisateur</h4>
          <p>{content.user_need}</p>
        </section>
      )}
      {(content.sections || []).map((section) => (
        <section key={section.id ?? section.title}>
          <h4>{section.title}</h4>
          {section.content && <p>{section.content}</p>}
          {section.bullets && section.bullets.length > 0 && (
            <ul>
              {section.bullets.map((b) => (
                <li key={b}>{b}</li>
              ))}
            </ul>
          )}
        </section>
      ))}
    </article>
  );
}

function DeliverableDetailLoader({
  projectId,
  deliverableId,
  onExportPdf,
  exporting,
}: {
  projectId: string;
  deliverableId: string;
  onExportPdf: () => void;
  exporting: boolean;
}) {
  const [content, setContent] = useState<DeliverableContent | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    getDeliverable(projectId, deliverableId)
      .then((detail) => {
        if (!cancelled) setContent(detail.generated_content);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [projectId, deliverableId]);

  if (loading) return <p className="livrables-muted">Chargement du livrable…</p>;
  if (!content) return <p className="livrables-muted">Contenu indisponible.</p>;
  return <DeliverablePreview content={content} onExportPdf={exporting ? undefined : onExportPdf} />;
}
