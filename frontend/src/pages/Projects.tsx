import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  Project,
  ProjectDeleteConflictError,
  ProjectTemplate,
  createProject,
  deleteProject,
  duplicateProject,
  listProjectTemplates,
  listProjects,
  updateProject,
} from "../api";

type ModalMode = "create" | "edit" | null;
type CreateMode = "blank" | "example";

const CREATE_TIMEOUT_MS = 10_000;

function withTimeout<T>(promise: Promise<T>, ms: number, message: string): Promise<T> {
  return new Promise((resolve, reject) => {
    const timer = window.setTimeout(() => reject(new Error(message)), ms);
    promise
      .then((value) => {
        window.clearTimeout(timer);
        resolve(value);
      })
      .catch((err) => {
        window.clearTimeout(timer);
        reject(err);
      });
  });
}

export default function Projects() {
  const navigate = useNavigate();
  const [projects, setProjects] = useState<Project[]>([]);
  const [templates, setTemplates] = useState<ProjectTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [deleteConflict, setDeleteConflict] = useState<{ name: string; count: number }[] | null>(
    null,
  );
  const [modal, setModal] = useState<ModalMode>(null);
  const [editing, setEditing] = useState<Project | null>(null);
  const [createMode, setCreateMode] = useState<CreateMode>("blank");
  const [formName, setFormName] = useState("");
  const [formExampleTemplate, setFormExampleTemplate] = useState("metropolis");
  const [formDescription, setFormDescription] = useState("");
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const exampleTemplates = templates.filter((t) => t.is_example);

  const refreshProjects = useCallback(async () => {
    const projs = await listProjects();
    setProjects(projs);
    return projs;
  }, []);

  const load = useCallback(async () => {
    setLoading(true);
    setLoadError(null);
    try {
      const projs = await listProjects();
      setProjects(projs);
      try {
        const tpls = await listProjectTemplates();
        setTemplates(tpls);
      } catch (tplErr) {
        console.warn("[Projects] Impossible de charger les modèles exemples", tplErr);
      }
    } catch (e) {
      setProjects([]);
      setLoadError(e instanceof Error ? e.message : "Erreur de chargement des projets");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  function openCreate() {
    setEditing(null);
    setCreateMode("blank");
    setFormName("");
    setFormExampleTemplate("metropolis");
    setFormDescription("");
    setFormError(null);
    setModal("create");
  }

  function openEdit(project: Project) {
    setEditing(project);
    setFormName(project.name);
    setFormDescription(project.description ?? "");
    setFormError(null);
    setModal("edit");
  }

  function closeModal() {
    setModal(null);
    setEditing(null);
    setFormError(null);
  }

  function onExampleTemplateChange(templateId: string) {
    setFormExampleTemplate(templateId);
    const tpl = exampleTemplates.find((t) => t.id === templateId);
    if (tpl?.default_name) {
      setFormName(tpl.default_name);
    }
  }

  async function handleCreateProject() {
    const payload = {
      name: formName.trim(),
      template: createMode === "example" ? formExampleTemplate : "blank",
      description: formDescription || undefined,
    };

    setSaving(true);
    setFormError(null);
    setError(null);

    try {
      console.log("[Projects] handleCreateProject — avant appel API", payload);

      const createdProject = await withTimeout(
        createProject(payload),
        CREATE_TIMEOUT_MS,
        "La requête a expiré après 10 secondes. Vérifiez que le backend est accessible.",
      );

      console.log("[Projects] handleCreateProject — après réponse API", createdProject);
      console.log("[Projects] handleCreateProject — contenu de la réponse", JSON.stringify(createdProject));

      const projectId = createdProject?.id;
      console.log("[Projects] handleCreateProject — projectId récupéré", projectId);

      if (!projectId) {
        throw new Error("Projet créé mais ID absent dans la réponse API");
      }

      console.log("[Projects] handleCreateProject — avant fermeture modale");
      closeModal();

      console.log("[Projects] handleCreateProject — avant navigate", `/schema-urbanisme?project=${projectId}`);
      navigate(`/schema-urbanisme?project=${projectId}`);

      refreshProjects().catch((refreshErr) => {
        console.warn("[Projects] refreshProjects en arrière-plan échoué", refreshErr);
      });
    } catch (e) {
      const message = e instanceof Error ? e.message : "Erreur lors de la création du projet";
      setFormError(message);
      setError(message);
    } finally {
      setSaving(false);
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!formName.trim()) {
      setFormError("Le nom du projet est obligatoire");
      return;
    }

    if (modal === "create") {
      await handleCreateProject();
      return;
    }

    if (!editing) return;

    setSaving(true);
    setFormError(null);
    setError(null);
    try {
      await updateProject(editing.id, {
        name: formName.trim(),
        description: formDescription || undefined,
      });
      closeModal();
      await refreshProjects();
    } catch (e) {
      const message = e instanceof Error ? e.message : "Erreur lors de l'enregistrement";
      setFormError(message);
      setError(message);
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(project: Project) {
    if (!confirm(`Supprimer le projet « ${project.name} » ?`)) return;
    setDeleteConflict(null);
    try {
      await deleteProject(project.id);
      await refreshProjects();
    } catch (e) {
      if (e instanceof ProjectDeleteConflictError) {
        setDeleteConflict(e.dependencies);
        setError(
          "Impossible de supprimer ce projet : il contient encore des données liées.",
        );
        return;
      }
      setError(e instanceof Error ? e.message : "Erreur suppression");
    }
  }

  async function handleDuplicate(project: Project) {
    try {
      const clone = await duplicateProject(project.id);
      refreshProjects().catch(() => undefined);
      navigate(`/schema-urbanisme?project=${clone.id}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erreur duplication");
    }
  }

  function objectCount(project: Project): number {
    const club = (project.urbanism?.club_urba ?? {}) as Record<string, Record<string, string[]>>;
    let n = 0;
    for (const couche of Object.values(club)) {
      if (typeof couche !== "object") continue;
      for (const items of Object.values(couche)) {
        if (Array.isArray(items)) n += items.length;
      }
    }
    return n;
  }

  return (
    <>
      <div className="page-header projects-header">
        <div>
          <h2>Projets</h2>
          <p>Créez un projet vierge et construisez votre cartographie Club Urba</p>
        </div>
        <button type="button" className="btn btn-primary" onClick={openCreate}>
          + Nouveau projet
        </button>
      </div>

      {error && (
        <div className="card project-error" role="alert">
          <p style={{ margin: deleteConflict?.length ? "0 0 0.75rem" : 0 }}>{error}</p>
          {deleteConflict && deleteConflict.length > 0 && (
            <ul style={{ margin: "0 0 0.75rem", paddingLeft: "1.25rem" }}>
              {deleteConflict.map((dep) => (
                <li key={dep.name}>
                  {dep.name} : {dep.count} élément{dep.count > 1 ? "s" : ""}
                </li>
              ))}
            </ul>
          )}
          <button
            type="button"
            className="btn btn-secondary"
            onClick={() => {
              setError(null);
              setDeleteConflict(null);
            }}
          >
            Fermer
          </button>
        </div>
      )}

      {loading ? (
        <div className="card">Chargement des projets…</div>
      ) : loadError ? (
        <div className="card project-error" role="alert">
          <p style={{ margin: "0 0 1rem" }}>{loadError}</p>
          <button type="button" className="btn btn-primary" onClick={() => load()}>
            Réessayer
          </button>
        </div>
      ) : projects.length === 0 ? (
        <div className="card projects-empty">
          <h3>Aucun projet</h3>
          <p style={{ color: "var(--muted)", margin: "0.75rem 0 1.25rem" }}>
            Créez un <strong>projet vierge</strong> et renseignez vos objectifs, processus, îlots et composants
            techniques. Les modèles Smart City, Banque, Santé et Industrie restent disponibles comme exemples optionnels.
          </p>
          <button type="button" className="btn btn-primary" onClick={openCreate}>
            Créer un projet vierge
          </button>
        </div>
      ) : (
        <div className="projects-table-wrapper card">
          <table className="projects-table">
            <thead>
              <tr>
                <th>Nom</th>
                <th>Secteur</th>
                <th>Objets Club Urba</th>
                <th>Statut</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {projects.map((p) => (
                <tr key={p.id}>
                  <td>
                    <strong>{p.name}</strong>
                    {p.description && <span className="project-desc">{p.description}</span>}
                  </td>
                  <td>{p.organization?.sector ?? "—"}</td>
                  <td>
                    <span className={objectCount(p) > 0 ? "status-badge" : "project-warn-badge"}>
                      {objectCount(p)} objets
                    </span>
                  </td>
                  <td>{p.status}</td>
                  <td className="projects-actions">
                    <Link to={`/schema-urbanisme?project=${p.id}`} className="btn btn-secondary btn-sm">
                      Cartographie
                    </Link>
                    <button type="button" className="btn btn-secondary btn-sm" onClick={() => openEdit(p)}>
                      Modifier
                    </button>
                    <button type="button" className="btn btn-secondary btn-sm" onClick={() => handleDuplicate(p)}>
                      Dupliquer
                    </button>
                    <button type="button" className="btn btn-danger btn-sm" onClick={() => handleDelete(p)}>
                      Supprimer
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {modal && (
        <div className="modal-overlay" onClick={closeModal}>
          <div className="modal-card modal-card-wide" onClick={(e) => e.stopPropagation()}>
            <h3>{modal === "create" ? "Nouveau projet" : "Modifier le projet"}</h3>
            {formError && (
              <div className="project-error modal-form-error" role="alert">
                {formError}
              </div>
            )}
            <form onSubmit={handleSubmit}>
              {modal === "create" && (
                <>
                  <div className="form-group">
                    <label>Type de création</label>
                    <div className="create-mode-toggle">
                      <button
                        type="button"
                        className={`create-mode-btn ${createMode === "blank" ? "selected" : ""}`}
                        onClick={() => {
                          setCreateMode("blank");
                          setFormName("");
                        }}
                      >
                        <strong>Projet vierge</strong>
                        <span>Cartographie vide — vous saisissez chaque zone</span>
                      </button>
                      <button
                        type="button"
                        className={`create-mode-btn ${createMode === "example" ? "selected" : ""}`}
                        onClick={() => {
                          setCreateMode("example");
                          onExampleTemplateChange(formExampleTemplate);
                        }}
                      >
                        <strong>Créer depuis un modèle exemple</strong>
                        <span>Préremplit une cartographie de démonstration</span>
                      </button>
                    </div>
                  </div>

                  {createMode === "example" && (
                    <div className="form-group">
                      <label>Modèle exemple (optionnel)</label>
                      <div className="template-grid">
                        {exampleTemplates.map((t) => (
                          <button
                            key={t.id}
                            type="button"
                            className={`template-card ${formExampleTemplate === t.id ? "selected" : ""}`}
                            onClick={() => onExampleTemplateChange(t.id)}
                          >
                            <strong>{t.label}</strong>
                            <span>{t.description}</span>
                          </button>
                        ))}
                      </div>
                    </div>
                  )}
                </>
              )}

              <div className="form-group">
                <label htmlFor="project-name">Nom du projet</label>
                <input
                  id="project-name"
                  value={formName}
                  onChange={(e) => setFormName(e.target.value)}
                  placeholder={createMode === "blank" ? "Mon projet" : "Nom du projet"}
                  required
                />
              </div>

              <div className="form-group">
                <label htmlFor="project-desc">Description</label>
                <textarea
                  id="project-desc"
                  value={formDescription}
                  onChange={(e) => setFormDescription(e.target.value)}
                  rows={2}
                  placeholder="Description optionnelle"
                />
              </div>

              <div className="modal-actions">
                <button type="button" className="btn btn-secondary" onClick={closeModal} disabled={saving}>
                  Annuler
                </button>
                <button type="submit" className="btn btn-primary" disabled={saving}>
                  {saving ? "Enregistrement…" : modal === "create" ? "Créer et ouvrir la cartographie" : "Enregistrer"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
}
