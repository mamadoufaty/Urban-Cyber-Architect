import { useCallback, useEffect, useState } from "react";
import {
  type AdminOrganization,
  activateAdminOrganization,
  createAdminOrganization,
  deactivateAdminOrganization,
  deleteAdminOrganization,
  listAdminOrganizations,
  updateAdminOrganization,
} from "../../api";
import OrganizationFormModal, {
  type OrganizationFormValues,
} from "../../components/admin/OrganizationFormModal";
import "../../styles/administration.css";

function formatDate(value: string | null | undefined): string {
  if (!value) return "—";
  try {
    return new Date(value).toLocaleString("fr-FR");
  } catch {
    return value;
  }
}

function statusLabel(status: string): string {
  if (status === "active") return "Actif";
  if (status === "archived") return "Archivé";
  return status;
}

function parseApiError(err: unknown): string {
  if (!(err instanceof Error)) return "Une erreur est survenue.";
  try {
    const parsed = JSON.parse(err.message) as { detail?: string };
    if (typeof parsed.detail === "string") return parsed.detail;
  } catch {
    /* message brut */
  }
  return err.message || "Une erreur est survenue.";
}

export default function AdminOrganizations() {
  const [organizations, setOrganizations] = useState<AdminOrganization[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [formOpen, setFormOpen] = useState(false);
  const [formMode, setFormMode] = useState<"create" | "edit">("create");
  const [editingOrg, setEditingOrg] = useState<AdminOrganization | null>(null);
  const [formError, setFormError] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await listAdminOrganizations();
      setOrganizations(response.items);
    } catch (e) {
      setError(parseApiError(e));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  function openCreate() {
    setFormMode("create");
    setEditingOrg(null);
    setFormError(null);
    setFormOpen(true);
  }

  function openEdit(org: AdminOrganization) {
    setFormMode("edit");
    setEditingOrg(org);
    setFormError(null);
    setFormOpen(true);
  }

  async function handleFormSubmit(values: OrganizationFormValues) {
    setSaving(true);
    setFormError(null);
    try {
      if (formMode === "create") {
        await createAdminOrganization({
          name: values.name.trim(),
          code: values.code.trim(),
          description: values.description || undefined,
          status: values.status,
        });
      } else if (editingOrg) {
        await updateAdminOrganization(editingOrg.id, {
          name: values.name.trim(),
          description: values.description || undefined,
          status: values.status,
        });
      }
      setFormOpen(false);
      await loadData();
    } catch (e) {
      setFormError(parseApiError(e));
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(org: AdminOrganization) {
    if (!confirm(`Supprimer l'organisation « ${org.name} » ?`)) return;
    try {
      await deleteAdminOrganization(org.id);
      await loadData();
    } catch (e) {
      setError(parseApiError(e));
    }
  }

  async function handleDeactivate(org: AdminOrganization) {
    try {
      await deactivateAdminOrganization(org.id);
      await loadData();
    } catch (e) {
      setError(parseApiError(e));
    }
  }

  async function handleActivate(org: AdminOrganization) {
    try {
      await activateAdminOrganization(org.id);
      await loadData();
    } catch (e) {
      setError(parseApiError(e));
    }
  }

  return (
    <div className="admin-users-page">
      <div className="admin-users-header">
        <div>
          <h2>Organisations</h2>
          <p>Gestion des organisations et rattachements</p>
        </div>
        <button type="button" className="btn btn-primary" onClick={openCreate}>
          + Nouvelle organisation
        </button>
      </div>

      {error && (
        <div className="admin-users-error" role="alert">
          {error}
          <button
            type="button"
            className="btn btn-secondary btn-sm"
            style={{ marginLeft: "0.75rem" }}
            onClick={() => setError(null)}
          >
            Fermer
          </button>
        </div>
      )}

      {loading ? (
        <div className="card">Chargement des organisations…</div>
      ) : (
        <div className="card admin-users-table-wrapper">
          <table className="admin-users-table">
            <thead>
              <tr>
                <th>Nom</th>
                <th>Code</th>
                <th>Description</th>
                <th>Statut</th>
                <th>Date création</th>
                <th>Date modification</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {organizations.length === 0 ? (
                <tr>
                  <td colSpan={7} style={{ color: "var(--muted)", textAlign: "center" }}>
                    Aucune organisation
                  </td>
                </tr>
              ) : (
                organizations.map((org) => (
                  <tr key={org.id}>
                    <td>
                      <strong>{org.name}</strong>
                    </td>
                    <td>{org.code}</td>
                    <td>{org.description || "—"}</td>
                    <td>
                      <span
                        className={`admin-status-badge ${
                          org.status === "active" ? "active" : "disabled"
                        }`}
                      >
                        {statusLabel(org.status)}
                      </span>
                    </td>
                    <td>{formatDate(org.created_at)}</td>
                    <td>{formatDate(org.updated_at)}</td>
                    <td>
                      <div className="admin-users-actions">
                        <button
                          type="button"
                          className="btn btn-secondary btn-sm"
                          onClick={() => openEdit(org)}
                        >
                          Modifier
                        </button>
                        {org.status === "active" ? (
                          <button
                            type="button"
                            className="btn btn-secondary btn-sm"
                            onClick={() => handleDeactivate(org)}
                          >
                            Désactiver
                          </button>
                        ) : (
                          <button
                            type="button"
                            className="btn btn-secondary btn-sm"
                            onClick={() => handleActivate(org)}
                          >
                            Activer
                          </button>
                        )}
                        <button
                          type="button"
                          className="btn btn-danger btn-sm"
                          onClick={() => handleDelete(org)}
                        >
                          Supprimer
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}

      <OrganizationFormModal
        open={formOpen}
        mode={formMode}
        organization={editingOrg}
        saving={saving}
        error={formError}
        onClose={() => setFormOpen(false)}
        onSubmit={handleFormSubmit}
      />
    </div>
  );
}
