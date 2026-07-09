import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams, useSearchParams } from "react-router-dom";
import {
  getProject,
  listAdminOrganizations,
  listAdminUsers,
  listProjectTemplates,
  listReferentials,
  updateProject,
  type AdminOrganization,
  type AdminUser,
  type Project,
  type ProjectTemplate,
  type Referential,
} from "../api";
import ProjectActivityTab from "../components/projects/ProjectActivityTab";
import ProjectDashboardTab from "../components/projects/ProjectDashboardTab";
import ProjectFormModal, {
  buildProjectPayload,
  type ProjectFormValues,
} from "../components/projects/ProjectFormModal";
import ProjectTeamTab from "../components/projects/ProjectTeamTab";
import { useActiveProject } from "../context/ActiveProjectContext";
import { useAuth } from "../context/AuthContext";
import { isAdminRole } from "../auth/permissions";
import {
  projectPriorityLabel,
  projectStatusLabel,
} from "../projects/constants";
import { upsertOrganization } from "../projects/organizationSelect";
import { upsertReferential } from "../projects/referentialSelect";
import "../styles/projects.css";

const TABS = [
  { id: "dashboard", label: "Dashboard" },
  { id: "team", label: "Équipe" },
  { id: "activity", label: "Activité" },
  { id: "urbanism", label: "Urbanisme SI" },
  { id: "ebios", label: "EBIOS RM" },
  { id: "grc", label: "GRC" },
  { id: "soc", label: "SOC" },
  { id: "siem", label: "SIEM / SOAR" },
  { id: "ai", label: "IA" },
  { id: "deliverables", label: "Livrables" },
  { id: "settings", label: "Paramètres" },
] as const;

type TabId = (typeof TABS)[number]["id"];

function userDisplayName(user: AdminUser | undefined): string {
  if (!user) return "—";
  const name = [user.first_name, user.last_name].filter(Boolean).join(" ");
  return name || user.username;
}

export default function ProjectDetail() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const { setActiveProject } = useActiveProject();
  const { user } = useAuth();
  const canChangeOrganization = isAdminRole(user?.role);
  const activeTab = (searchParams.get("tab") as TabId) || "dashboard";

  const [project, setProject] = useState<Project | null>(null);
  const [organizations, setOrganizations] = useState<AdminOrganization[]>([]);
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [templates, setTemplates] = useState<ProjectTemplate[]>([]);
  const [referentials, setReferentials] = useState<Referential[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const orgMap = useMemo(() => new Map(organizations.map((o) => [o.id, o])), [organizations]);
  const userMap = useMemo(() => new Map(users.map((u) => [u.id, u])), [users]);

  const load = useCallback(async () => {
    if (!projectId) return;
    setLoading(true);
    setError(null);
    try {
      const [proj, orgsRes, usersRes, tpls, refsRes] = await Promise.all([
        getProject(projectId),
        listAdminOrganizations(),
        listAdminUsers(),
        listProjectTemplates().catch(() => [] as ProjectTemplate[]),
        listReferentials(true).catch(() => ({ items: [] as Referential[] })),
      ]);
      setProject(proj);
      setOrganizations(orgsRes.items);
      setUsers(usersRes.items);
      setTemplates(tpls);
      setReferentials(refsRes.items);
      setActiveProject({ id: proj.id, name: proj.name, code: proj.code });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Projet introuvable");
      setProject(null);
    } finally {
      setLoading(false);
    }
  }, [projectId, setActiveProject]);

  useEffect(() => {
    load();
  }, [load]);

  function setTab(tab: TabId) {
    setSearchParams({ tab });
  }

  async function handleSettingsSubmit(values: ProjectFormValues) {
    if (!project) return;
    setSaving(true);
    setFormError(null);
    try {
      const updated = await updateProject(project.id, buildProjectPayload(values, "edit"));
      setProject(updated);
      setActiveProject({ id: updated.id, name: updated.name, code: updated.code });
      setSettingsOpen(false);
    } catch (e) {
      setFormError(e instanceof Error ? e.message : "Erreur enregistrement");
    } finally {
      setSaving(false);
    }
  }

  if (!projectId) {
    return <div className="card project-error">Identifiant projet manquant.</div>;
  }

  if (loading) {
    return <div className="card">Chargement du projet…</div>;
  }

  if (error || !project) {
    return (
      <div className="card project-error">
        <p>{error ?? "Projet introuvable"}</p>
        <button type="button" className="btn btn-secondary" onClick={() => navigate("/projects")}>
          Retour aux projets
        </button>
      </div>
    );
  }

  const orgName =
    (project.organization_id && orgMap.get(project.organization_id)?.name) ||
    project.organization?.name ||
    "—";
  const ownerName = userDisplayName(
    project.owner_id ? userMap.get(project.owner_id) : undefined,
  );

  return (
    <>
      <div className="page-header project-detail-header">
        <div>
          <Link to="/projects" className="project-back-link">
            ← Projets
          </Link>
          <h2>{project.name}</h2>
          <p className="project-detail-meta">
            {project.code && <span className="project-code-badge">{project.code}</span>}
            <span>{orgName}</span>
            {project.client && <span>· {project.client}</span>}
            <span className={`priority-badge priority-${project.priority ?? "medium"}`}>
              {projectPriorityLabel(project.priority ?? "medium")}
            </span>
            <span className={`status-badge status-${project.status}`}>
              {projectStatusLabel(project.status)}
            </span>
          </p>
        </div>
      </div>

      <nav className="project-tabs" aria-label="Sections du projet">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            type="button"
            className={`project-tab${activeTab === tab.id ? " active" : ""}`}
            onClick={() => setTab(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </nav>

      {activeTab === "dashboard" && (
        <ProjectDashboardTab
          project={project}
          organizationName={orgName}
          ownerName={ownerName}
        />
      )}

      {activeTab === "team" && <ProjectTeamTab projectId={project.id} />}
      {activeTab === "activity" && <ProjectActivityTab projectId={project.id} />}

      {activeTab === "urbanism" && (
        <ModuleLinkPanel
          title="Urbanisme SI"
          description="Cartographie Club Urba, moteur d'urbanisme et validation métamodèle."
          links={[
            { label: "Moteur d'urbanisme", to: `/schema-urbanisme?project=${project.id}` },
            { label: "Validation métamodèle", to: `/validation-metamodele?project=${project.id}` },
          ]}
        />
      )}

      {activeTab === "ebios" && (
        <ModuleLinkPanel
          title="EBIOS RM"
          description="Ateliers EBIOS, scénarios et évaluation des risques."
          links={[{ label: "Ouvrir EBIOS RM", to: `/ebios?project=${project.id}` }]}
        />
      )}

      {activeTab === "grc" && (
        <ModuleLinkPanel
          title="GRC"
          description="Registre des risques, dashboard RSSI, SoA et plan de traitement."
          links={[
            { label: "Registre des risques", to: `/registre-risques?project=${project.id}` },
            { label: "Dashboard RSSI", to: `/dashboard-rssi?project=${project.id}` },
            { label: "Déclaration d'applicabilité", to: `/declaration-applicabilite?project=${project.id}` },
            { label: "Plan de traitement", to: `/plan-traitement-risques?project=${project.id}` },
          ]}
        />
      )}

      {activeTab === "soc" && (
        <ModuleLinkPanel
          title="SOC"
          description="Supervision Wazuh et corrélations sécurité."
          links={[
            { label: "Dashboard Wazuh", to: `/soc/wazuh?project=${project.id}` },
            { label: "Corrélations", to: `/soc/correlations?project=${project.id}` },
          ]}
        />
      )}

      {activeTab === "siem" && (
        <ModuleLinkPanel
          title="SIEM / SOAR"
          description="Module en cours d'intégration — orchestration des playbooks et remontées SIEM."
          links={[]}
          placeholder
        />
      )}

      {activeTab === "ai" && (
        <ModuleLinkPanel
          title="IA"
          description="Gouvernance IA, prompts et base de connaissances."
          links={[
            { label: "AI Governance", to: `/ai-governance?project=${project.id}` },
            { label: "Prompt Studio", to: `/prompt-studio?project=${project.id}` },
            { label: "Knowledge Base", to: `/knowledge-base?project=${project.id}` },
          ]}
        />
      )}

      {activeTab === "deliverables" && (
        <ModuleLinkPanel
          title="Livrables"
          description="Génération et export des livrables projet."
          links={[{ label: "Ouvrir les livrables", to: `/livrables?project=${project.id}` }]}
        />
      )}

      {activeTab === "settings" && (
        <div className="project-tab-panel">
          <div className="card">
            <h4>Paramètres du projet</h4>
            <p style={{ color: "var(--muted)" }}>
              Modifiez les métadonnées, le périmètre et les référentiels associés.
            </p>
            <button type="button" className="btn btn-primary" onClick={() => setSettingsOpen(true)}>
              Modifier le projet
            </button>
          </div>
        </div>
      )}

      <ProjectFormModal
        mode="edit"
        open={settingsOpen}
        saving={saving}
        error={formError}
        initial={project}
        organizations={organizations}
        users={users}
        templates={templates}
        referentials={referentials}
        canChangeOrganization={canChangeOrganization}
        defaultOrganizationId={user?.organizationId ?? null}
        onOrganizationCreated={(org) =>
          setOrganizations((prev) => upsertOrganization(prev, org))
        }
        canManageReferentials={canChangeOrganization}
        onReferentialCreated={(ref) =>
          setReferentials((prev) => upsertReferential(prev, ref))
        }
        onClose={() => {
          setSettingsOpen(false);
          setFormError(null);
        }}
        onSubmit={handleSettingsSubmit}
      />
    </>
  );
}

function ModuleLinkPanel({
  title,
  description,
  links,
  placeholder,
}: {
  title: string;
  description: string;
  links: { label: string; to: string }[];
  placeholder?: boolean;
}) {
  return (
    <div className="project-tab-panel">
      <div className="card">
        <h4>{title}</h4>
        <p style={{ color: "var(--muted)" }}>{description}</p>
        {placeholder && links.length === 0 ? (
          <p style={{ color: "var(--muted)", fontStyle: "italic" }}>
            Fonctionnalité prévue dans une prochaine version.
          </p>
        ) : (
          <div className="project-module-links">
            {links.map((link) => (
              <Link key={link.to} to={link.to} className="btn btn-primary">
                {link.label}
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
