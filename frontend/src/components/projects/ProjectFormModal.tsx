import { useEffect, useMemo, useState } from "react";
import {
  createAdminOrganization,
  createReferential,
  type AdminOrganization,
  type AdminUser,
  type Project,
  type ProjectTemplate,
  type Referential,
} from "../../api";
import { PROJECT_PRIORITY_OPTIONS, PROJECT_STATUS_OPTIONS } from "../../projects/constants";
import type { ProjectCreatePayload } from "../../api";
import { parseTagsInput, tagsToInput, toDateInputValue, validateProjectDateRange } from "../../projects/format";
import { activeOrganizations, upsertOrganization } from "../../projects/organizationSelect";
import {
  upsertReferential,
  withReferentialPreselected,
  type QuickAddReferentialValues,
} from "../../projects/referentialSelect";
import OrganizationFormModal, {
  type OrganizationFormValues,
} from "../admin/OrganizationFormModal";
import DatePicker from "./DatePicker";
import OrganizationCombobox from "./OrganizationCombobox";
import QuickAddReferentialModal from "./QuickAddReferentialModal";

export type ProjectFormValues = {
  name: string;
  code: string;
  description: string;
  client: string;
  organization_id: string;
  status: string;
  priority: string;
  start_date: string;
  end_date: string;
  owner_id: string;
  referentials: string[];
  tags: string;
  template: string;
  createMode: "blank" | "example";
};

type Props = {
  mode: "create" | "edit";
  open: boolean;
  saving: boolean;
  error: string | null;
  initial?: Project | null;
  organizations: AdminOrganization[];
  users: AdminUser[];
  templates: ProjectTemplate[];
  referentials: Referential[];
  /** L'utilisateur peut-il changer l'organisation (Administrateur / SuperAdmin) ? */
  canChangeOrganization?: boolean;
  /** Organisation à présélectionner en création (celle de l'utilisateur). */
  defaultOrganizationId?: string | null;
  /** Notifie le parent d'une organisation créée depuis le formulaire. */
  onOrganizationCreated?: (organization: AdminOrganization) => void;
  /** L'utilisateur peut-il créer un référentiel depuis ce formulaire (Administrateur / SuperAdmin) ? */
  canManageReferentials?: boolean;
  /** Notifie le parent d'un référentiel créé depuis le formulaire. */
  onReferentialCreated?: (referential: Referential) => void;
  onClose: () => void;
  onSubmit: (values: ProjectFormValues) => void;
};

function defaultValues(
  initial: Project | null | undefined,
  mode: "create" | "edit",
  defaultOrganizationId?: string | null,
): ProjectFormValues {
  const organizationId =
    initial?.organization_id ?? (mode === "create" ? defaultOrganizationId ?? "" : "");
  return {
    name: initial?.name ?? "",
    code: initial?.code ?? "",
    description: initial?.description ?? "",
    client: initial?.client ?? "",
    organization_id: organizationId ?? "",
    status: initial?.status ?? "draft",
    priority: initial?.priority ?? "medium",
    start_date: toDateInputValue(initial?.start_date),
    end_date: toDateInputValue(initial?.end_date),
    owner_id: initial?.owner_id ?? "",
    referentials: initial?.referentials ?? [],
    tags: tagsToInput(initial?.tags),
    template: "metropolis",
    createMode: "blank",
  };
}

function userLabel(user: AdminUser): string {
  const name = [user.first_name, user.last_name].filter(Boolean).join(" ");
  return name ? `${name} (${user.username})` : user.username;
}

export default function ProjectFormModal({
  mode,
  open,
  saving,
  error,
  initial,
  organizations,
  users,
  templates,
  referentials,
  canChangeOrganization = true,
  defaultOrganizationId,
  onOrganizationCreated,
  canManageReferentials = false,
  onReferentialCreated,
  onClose,
  onSubmit,
}: Props) {
  const [values, setValues] = useState<ProjectFormValues>(() =>
    defaultValues(initial, mode, defaultOrganizationId),
  );
  const [dateError, setDateError] = useState<string | null>(null);
  const [orgs, setOrgs] = useState<AdminOrganization[]>(organizations);
  const [orgModalOpen, setOrgModalOpen] = useState(false);
  const [orgSaving, setOrgSaving] = useState(false);
  const [orgError, setOrgError] = useState<string | null>(null);
  const [refs, setRefs] = useState<Referential[]>(referentials);
  const [refModalOpen, setRefModalOpen] = useState(false);
  const [refSaving, setRefSaving] = useState(false);
  const [refError, setRefError] = useState<string | null>(null);
  const exampleTemplates = templates.filter((t) => t.is_example);

  const availableOrganizations = useMemo(() => {
    // Toujours actives + trie, mais on conserve l'organisation déjà rattachée
    // (édition) même si elle a été désactivée depuis.
    const active = activeOrganizations(orgs);
    const current = orgs.find((o) => o.id === values.organization_id);
    if (current && !active.some((o) => o.id === current.id)) {
      return upsertOrganization(active, current);
    }
    return active;
  }, [orgs, values.organization_id]);

  useEffect(() => {
    if (open) {
      setValues(defaultValues(initial, mode, defaultOrganizationId));
      setDateError(null);
      setOrgs(organizations);
      setRefs(referentials);
    }
  }, [open, initial, mode, defaultOrganizationId, organizations, referentials]);

  if (!open) return null;

  function update<K extends keyof ProjectFormValues>(key: K, value: ProjectFormValues[K]) {
    setValues((prev) => ({ ...prev, [key]: value }));
  }

  function toggleReferential(ref: string) {
    setValues((prev) => ({
      ...prev,
      referentials: prev.referentials.includes(ref)
        ? prev.referentials.filter((r) => r !== ref)
        : [...prev.referentials, ref],
    }));
  }

  async function handleCreateOrganization(formValues: OrganizationFormValues) {
    setOrgSaving(true);
    setOrgError(null);
    try {
      const created = await createAdminOrganization({
        name: formValues.name.trim(),
        code: formValues.code.trim(),
        description: formValues.description || undefined,
        status: formValues.status,
      });
      setOrgs((prev) => upsertOrganization(prev, created));
      update("organization_id", created.id);
      onOrganizationCreated?.(created);
      setOrgModalOpen(false);
    } catch (e) {
      let message = "Création de l'organisation impossible.";
      if (e instanceof Error) {
        try {
          const parsed = JSON.parse(e.message) as { detail?: string };
          message = parsed.detail ?? e.message;
        } catch {
          message = e.message;
        }
      }
      setOrgError(message);
    } finally {
      setOrgSaving(false);
    }
  }

  async function handleCreateReferential(formValues: QuickAddReferentialValues) {
    setRefSaving(true);
    setRefError(null);
    try {
      const created = await createReferential({
        label: formValues.label.trim(),
        code: formValues.code.trim(),
        description: formValues.description.trim() || undefined,
        status: formValues.status,
      });
      setRefs((prev) => upsertReferential(prev, created));
      update("referentials", withReferentialPreselected(values.referentials, created.label));
      onReferentialCreated?.(created);
      setRefModalOpen(false);
    } catch (e) {
      let message = "Création du référentiel impossible.";
      if (e instanceof Error) {
        try {
          const parsed = JSON.parse(e.message) as { detail?: string };
          message = parsed.detail ?? e.message;
        } catch {
          message = e.message;
        }
      }
      setRefError(message);
    } finally {
      setRefSaving(false);
    }
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!values.name.trim()) return;

    const rangeError = validateProjectDateRange(values.start_date, values.end_date);
    if (rangeError) {
      setDateError(rangeError);
      return;
    }
    setDateError(null);
    onSubmit(values);
  }

  return (
    <>
      <div className="modal-overlay" onClick={onClose}>
      <div className="modal-card modal-card-wide project-form-modal" onClick={(e) => e.stopPropagation()}>
        <h3>{mode === "create" ? "Nouveau projet" : "Modifier le projet"}</h3>
        {error && (
          <div className="project-error modal-form-error" role="alert">
            {error}
          </div>
        )}
        {dateError && (
          <div className="project-error modal-form-error" role="alert">
            {dateError}
          </div>
        )}
        <form onSubmit={handleSubmit}>
          {mode === "create" && (
            <div className="form-group">
              <label>Type de création</label>
              <div className="create-mode-toggle">
                <button
                  type="button"
                  className={`create-mode-btn ${values.createMode === "blank" ? "selected" : ""}`}
                  onClick={() => update("createMode", "blank")}
                >
                  <strong>Projet vierge</strong>
                  <span>Cartographie vide</span>
                </button>
                <button
                  type="button"
                  className={`create-mode-btn ${values.createMode === "example" ? "selected" : ""}`}
                  onClick={() => update("createMode", "example")}
                >
                  <strong>Modèle exemple</strong>
                  <span>Préremplit une démonstration</span>
                </button>
              </div>
            </div>
          )}

          {mode === "create" && values.createMode === "example" && (
            <div className="form-group">
              <label>Modèle exemple</label>
              <div className="template-grid">
                {exampleTemplates.map((t) => (
                  <button
                    key={t.id}
                    type="button"
                    className={`template-card ${values.template === t.id ? "selected" : ""}`}
                    onClick={() => {
                      update("template", t.id);
                      if (t.default_name) update("name", t.default_name);
                    }}
                  >
                    <strong>{t.label}</strong>
                    <span>{t.description}</span>
                  </button>
                ))}
              </div>
            </div>
          )}

          <div className="project-form-grid">
            <div className="form-group">
              <label htmlFor="pf-name">Nom *</label>
              <input
                id="pf-name"
                value={values.name}
                onChange={(e) => update("name", e.target.value)}
                required
              />
            </div>
            <div className="form-group">
              <label htmlFor="pf-code">Code</label>
              <input
                id="pf-code"
                value={values.code}
                onChange={(e) => update("code", e.target.value)}
                placeholder="auto-généré si vide"
              />
            </div>
            <div className="form-group project-form-full">
              <label htmlFor="pf-desc">Description</label>
              <textarea
                id="pf-desc"
                value={values.description}
                onChange={(e) => update("description", e.target.value)}
                rows={2}
              />
            </div>
            <div className="form-group">
              <label htmlFor="pf-client">Client</label>
              <input
                id="pf-client"
                value={values.client}
                onChange={(e) => update("client", e.target.value)}
              />
            </div>
            <div className="form-group">
              <label htmlFor="pf-org">Organisation</label>
              <OrganizationCombobox
                id="pf-org"
                organizations={availableOrganizations}
                value={values.organization_id}
                onChange={(orgId) => update("organization_id", orgId)}
                onCreateNew={canChangeOrganization ? () => {
                  setOrgError(null);
                  setOrgModalOpen(true);
                } : undefined}
                disabled={!canChangeOrganization}
                allowClear={canChangeOrganization}
              />
              {!canChangeOrganization && (
                <span className="field-hint">
                  Organisation rattachée à votre compte. Seul un administrateur peut la modifier.
                </span>
              )}
            </div>
            <div className="form-group">
              <label htmlFor="pf-status">Statut</label>
              <select
                id="pf-status"
                value={values.status}
                onChange={(e) => update("status", e.target.value)}
              >
                {PROJECT_STATUS_OPTIONS.map((s) => (
                  <option key={s.value} value={s.value}>
                    {s.label}
                  </option>
                ))}
              </select>
            </div>
            <div className="form-group">
              <label htmlFor="pf-priority">Priorité</label>
              <select
                id="pf-priority"
                value={values.priority}
                onChange={(e) => update("priority", e.target.value)}
              >
                {PROJECT_PRIORITY_OPTIONS.map((p) => (
                  <option key={p.value} value={p.value}>
                    {p.label}
                  </option>
                ))}
              </select>
            </div>
            <div className="form-group">
              <label htmlFor="pf-start">Date début</label>
              <DatePicker
                id="pf-start"
                value={values.start_date}
                ariaLabel="Date de début"
                onChange={(iso) => {
                  update("start_date", iso);
                  setDateError(null);
                }}
              />
            </div>
            <div className="form-group">
              <label htmlFor="pf-end">Date fin</label>
              <DatePicker
                id="pf-end"
                value={values.end_date}
                ariaLabel="Date de fin"
                min={values.start_date || undefined}
                onChange={(iso) => {
                  update("end_date", iso);
                  setDateError(null);
                }}
              />
            </div>
            <div className="form-group">
              <label htmlFor="pf-owner">Responsable</label>
              <select
                id="pf-owner"
                value={values.owner_id}
                onChange={(e) => update("owner_id", e.target.value)}
              >
                <option value="">— Non assigné —</option>
                {users.map((user) => (
                  <option key={user.id} value={user.id}>
                    {userLabel(user)}
                  </option>
                ))}
              </select>
            </div>
            <div className="form-group project-form-full">
              <label>Tags (séparés par des virgules)</label>
              <input
                value={values.tags}
                onChange={(e) => update("tags", e.target.value)}
                placeholder="cyber, urbanisme, conformité"
              />
            </div>
            <div className="form-group project-form-full">
              <div className="referentials-header">
                <label>Référentiels</label>
                {canManageReferentials && (
                  <button
                    type="button"
                    className="btn btn-link referential-add-btn"
                    onClick={() => {
                      setRefError(null);
                      setRefModalOpen(true);
                    }}
                  >
                    + Ajouter un référentiel
                  </button>
                )}
              </div>
              {refs.length === 0 ? (
                <p className="field-hint">
                  Aucun référentiel disponible.
                  {canManageReferentials
                    ? " Utilisez le bouton ci-dessus pour en créer un."
                    : " Un administrateur peut en ajouter depuis « Administration › Référentiels »."}
                </p>
              ) : (
                <div className="referential-checkboxes">
                  {refs.map((ref) => (
                    <label key={ref.id} className="referential-chip">
                      <input
                        type="checkbox"
                        checked={values.referentials.includes(ref.label)}
                        onChange={() => toggleReferential(ref.label)}
                      />
                      {ref.label}
                    </label>
                  ))}
                  {/* Référentiels déjà rattachés mais désormais absents du catalogue. */}
                  {values.referentials
                    .filter((label) => !refs.some((r) => r.label === label))
                    .map((label) => (
                      <label key={label} className="referential-chip">
                        <input
                          type="checkbox"
                          checked
                          onChange={() => toggleReferential(label)}
                        />
                        {label}
                      </label>
                    ))}
                </div>
              )}
            </div>
          </div>

          <div className="modal-actions">
            <button type="button" className="btn btn-secondary" onClick={onClose} disabled={saving}>
              Annuler
            </button>
            <button type="submit" className="btn btn-primary" disabled={saving}>
              {saving ? "Enregistrement…" : mode === "create" ? "Créer le projet" : "Enregistrer"}
            </button>
          </div>
        </form>
      </div>
      </div>

      <OrganizationFormModal
        open={orgModalOpen}
        mode="create"
        organization={null}
        saving={orgSaving}
        error={orgError}
        onClose={() => setOrgModalOpen(false)}
        onSubmit={handleCreateOrganization}
      />

      <QuickAddReferentialModal
        open={refModalOpen}
        saving={refSaving}
        error={refError}
        existing={refs}
        onClose={() => setRefModalOpen(false)}
        onSubmit={handleCreateReferential}
      />
    </>
  );
}

export function buildProjectPayload(
  values: ProjectFormValues,
  mode: "create" | "edit",
): ProjectCreatePayload {
  const tags = parseTagsInput(values.tags);
  const payload: ProjectCreatePayload = {
    name: values.name.trim(),
    description: values.description.trim() || undefined,
    client: values.client.trim() || undefined,
    organization_id: values.organization_id || undefined,
    status: values.status,
    priority: values.priority,
    start_date: values.start_date || undefined,
    end_date: values.end_date || undefined,
    owner_id: values.owner_id || undefined,
    referentials: values.referentials,
    tags,
  };
  if (values.code.trim()) {
    payload.code = values.code.trim();
  }
  if (mode === "create") {
    payload.template = values.createMode === "example" ? values.template : "blank";
  }
  return payload;
}
