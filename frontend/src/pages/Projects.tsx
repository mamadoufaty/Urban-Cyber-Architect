import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Project,
  ProjectDeleteConflictError,
  ProjectTemplate,
  archiveProject,
  createProject,
  deleteProject,
  duplicateProject,
  listAdminOrganizations,
  listAdminUsers,
  listProjectTemplates,
  listProjects,
  updateProject,
  type AdminOrganization,
  type AdminUser,
} from "../api";
import ProjectFormModal, {
  buildProjectPayload,
  type ProjectFormValues,
} from "../components/projects/ProjectFormModal";
import { useActiveProject } from "../context/ActiveProjectContext";
import {
  projectPriorityLabel,
  projectStatusLabel,
} from "../projects/constants";
import { formatDateOnly, formatDateTime } from "../projects/format";
import "../styles/projects.css";

type ModalMode = "create" | "edit" | null;

function userDisplayName(user: AdminUser | undefined): string {
  if (!user) return "—";
  const name = [user.first_name, user.last_name].filter(Boolean).join(" ");
  return name || user.username;
}

export default function Projects() {
  const navigate = useNavigate();
  const { activeProject, setActiveProject, clearActiveProject } = useActiveProject();
  const [projects, setProjects] = useState<Project[]>([]);
  const [organizations, setOrganizations] = useState<AdminOrganization[]>([]);
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [templates, setTemplates] = useState<ProjectTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [deleteConflict, setDeleteConflict] = useState<{ name: string; count: number }[] | null>(
    null,
  );
  const [modal, setModal] = useState<ModalMode>(null);
  const [editing, setEditing] = useState<Project | null>(null);
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const orgMap = useMemo(() => new Map(organizations.map((o) => [o.id, o])), [organizations]);
  const userMap = useMemo(() => new Map(users.map((u) => [u.id, u])), [users]);

  const refreshProjects = useCallback(async () => {
    const projs = await listProjects();
    setProjects(projs);
    return projs;
  }, []);

  const load = useCallback(async () => {
    setLoading(true);
    setLoadError(null);
    try {
      const [projs, orgsRes, usersRes] = await Promise.all([
        listProjects(),
        listAdminOrganizations().catch(() => ({ items: [] as AdminOrganization[] })),
        listAdminUsers().catch(() => ({ items: [] as AdminUser[] })),
      ]);
      setProjects(projs);
      setOrganizations(orgsRes.items);
      setUsers(usersRes.items);
      try {
        setTemplates(await listProjectTemplates());
      } catch {
        setTemplates([]);
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
    setFormError(null);
    setModal("create");
  }

  function openEdit(project: Project) {
    setEditing(project);
    setFormError(null);
    setModal("edit");
  }

  function closeModal() {
    setModal(null);
    setEditing(null);
    setFormError(null);
  }

  function organizationLabel(project: Project): string {
    if (project.organization_id) {
      return orgMap.get(project.organization_id)?.name ?? project.organization?.name ?? "—";
    }
    return project.organization?.name ?? "—";
  }

  function handleOpen(project: Project) {
    setActiveProject({ id: project.id, name: project.name, code: project.code });
    navigate(`/projects/${project.id}`);
  }

  async function handleFormSubmit(values: ProjectFormValues) {
    if (!values.name.trim()) {
      setFormError("Le nom du projet est obligatoire");
      return;
    }

    setSaving(true);
    setFormError(null);
    setError(null);

    try {
      if (modal === "create") {
        const created = await createProject(buildProjectPayload(values, "create"));
        closeModal();
        await refreshProjects();
        handleOpen(created);
      } else if (editing) {
        await updateProject(editing.id, buildProjectPayload(values, "edit"));
        closeModal();
        await refreshProjects();
      }
    } catch (e) {
      const message = e instanceof Error ? e.message : "Erreur lors de l'enregistrement";
      setFormError(message);
      setError(message);
    } finally {
      setSaving(false);
    }
  }

  async function handleArchive(project: Project) {
    if (!confirm(`Archiver le projet « ${project.name} » ?`)) return;
    setError(null);
    try {
      await archiveProject(project.id);
      await refreshProjects();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erreur archivage");
    }
  }

  async function handleDelete(project: Project) {
    if (!confirm(`Supprimer le projet « ${project.name} » ?`)) return;
    setDeleteConflict(null);
    try {
      await deleteProject(project.id);
      if (activeProject?.id === project.id) {
        clearActiveProject();
      }
      await refreshProjects();
    } catch (e) {
      if (e instanceof ProjectDeleteConflictError) {
        setDeleteConflict(e.dependencies);
        setError("Impossible de supprimer ce projet : il contient encore des données liées.");
        return;
      }
      setError(e instanceof Error ? e.message : "Erreur suppression");
    }
  }

  async function handleDuplicate(project: Project) {
    setError(null);
    try {
      const clone = await duplicateProject(project.id);
      await refreshProjects();
      handleOpen(clone);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erreur duplication");
    }
  }

  return (
    <>
      <div className="page-header projects-header">
        <div>
          <h2>Projets</h2>
          <p>Cockpit de gestion — créez, pilotez et ouvrez vos projets d'architecture</p>
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
            Créez votre premier projet pour centraliser l'urbanisme, la GRC, le SOC et les livrables.
          </p>
          <button type="button" className="btn btn-primary" onClick={openCreate}>
            Créer un projet
          </button>
        </div>
      ) : (
        <div className="projects-table-wrapper card projects-cockpit-table">
          <table className="projects-table">
            <thead>
              <tr>
                <th>Nom</th>
                <th>Code</th>
                <th>Client</th>
                <th>Organisation</th>
                <th>Responsable</th>
                <th>Statut</th>
                <th>Priorité</th>
                <th>Début</th>
                <th>Fin</th>
                <th>Dernière modif.</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {projects.map((p) => (
                <tr
                  key={p.id}
                  className={activeProject?.id === p.id ? "project-row-active" : undefined}
                >
                  <td>
                    <strong>{p.name}</strong>
                    {p.description && <span className="project-desc">{p.description}</span>}
                  </td>
                  <td>
                    <code className="project-code-cell">{p.code ?? "—"}</code>
                  </td>
                  <td>{p.client ?? "—"}</td>
                  <td>{organizationLabel(p)}</td>
                  <td>{userDisplayName(p.owner_id ? userMap.get(p.owner_id) : undefined)}</td>
                  <td>
                    <span className={`status-badge status-${p.status}`}>
                      {projectStatusLabel(p.status)}
                    </span>
                  </td>
                  <td>
                    <span className={`priority-badge priority-${p.priority ?? "medium"}`}>
                      {projectPriorityLabel(p.priority ?? "medium")}
                    </span>
                  </td>
                  <td>{formatDateOnly(p.start_date)}</td>
                  <td>{formatDateOnly(p.end_date)}</td>
                  <td>{formatDateTime(p.updated_at)}</td>
                  <td className="projects-actions">
                    <button
                      type="button"
                      className="btn btn-primary btn-sm"
                      onClick={() => handleOpen(p)}
                    >
                      Ouvrir
                    </button>
                    <button
                      type="button"
                      className="btn btn-secondary btn-sm"
                      onClick={() => openEdit(p)}
                    >
                      Modifier
                    </button>
                    <button
                      type="button"
                      className="btn btn-secondary btn-sm"
                      onClick={() => handleDuplicate(p)}
                    >
                      Dupliquer
                    </button>
                    {p.status !== "archived" && (
                      <button
                        type="button"
                        className="btn btn-secondary btn-sm"
                        onClick={() => handleArchive(p)}
                      >
                        Archiver
                      </button>
                    )}
                    <button
                      type="button"
                      className="btn btn-danger btn-sm"
                      onClick={() => handleDelete(p)}
                    >
                      Supprimer
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <ProjectFormModal
        mode={modal === "edit" ? "edit" : "create"}
        open={modal !== null}
        saving={saving}
        error={formError}
        initial={editing}
        organizations={organizations}
        users={users}
        templates={templates}
        onClose={closeModal}
        onSubmit={handleFormSubmit}
      />
    </>
  );
}
