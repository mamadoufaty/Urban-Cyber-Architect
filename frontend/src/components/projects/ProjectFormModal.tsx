import { useEffect, useState } from "react";
import type { AdminOrganization, AdminUser, Project, ProjectTemplate } from "../../api";
import {
  PROJECT_PRIORITY_OPTIONS,
  PROJECT_STATUS_OPTIONS,
  REFERENTIAL_OPTIONS,
} from "../../projects/constants";
import type { ProjectCreatePayload } from "../../api";
import { parseTagsInput, tagsToInput, toDateInputValue, validateProjectDateRange } from "../../projects/format";

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
  onClose: () => void;
  onSubmit: (values: ProjectFormValues) => void;
};

function defaultValues(initial?: Project | null): ProjectFormValues {
  return {
    name: initial?.name ?? "",
    code: initial?.code ?? "",
    description: initial?.description ?? "",
    client: initial?.client ?? "",
    organization_id: initial?.organization_id ?? "",
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
  onClose,
  onSubmit,
}: Props) {
  const [values, setValues] = useState<ProjectFormValues>(() => defaultValues(initial));
  const [dateError, setDateError] = useState<string | null>(null);
  const exampleTemplates = templates.filter((t) => t.is_example);

  useEffect(() => {
    if (open) {
      setValues(defaultValues(initial));
      setDateError(null);
    }
  }, [open, initial]);

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
              <select
                id="pf-org"
                value={values.organization_id}
                onChange={(e) => update("organization_id", e.target.value)}
              >
                <option value="">— Non renseigné —</option>
                {organizations.map((org) => (
                  <option key={org.id} value={org.id}>
                    {org.name}
                  </option>
                ))}
              </select>
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
              <input
                id="pf-start"
                type="date"
                value={values.start_date}
                onChange={(e) => {
                  update("start_date", e.target.value);
                  setDateError(null);
                }}
              />
            </div>
            <div className="form-group">
              <label htmlFor="pf-end">Date fin</label>
              <input
                id="pf-end"
                type="date"
                value={values.end_date}
                min={values.start_date || undefined}
                onChange={(e) => {
                  update("end_date", e.target.value);
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
              <label>Référentiels</label>
              <div className="referential-checkboxes">
                {REFERENTIAL_OPTIONS.map((ref) => (
                  <label key={ref} className="referential-chip">
                    <input
                      type="checkbox"
                      checked={values.referentials.includes(ref)}
                      onChange={() => toggleReferential(ref)}
                    />
                    {ref}
                  </label>
                ))}
              </div>
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
