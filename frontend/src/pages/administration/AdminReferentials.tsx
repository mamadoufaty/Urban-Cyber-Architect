import { useCallback, useEffect, useState } from "react";
import {
  activateReferential,
  createReferential,
  deactivateReferential,
  deleteReferential,
  listReferentials,
  updateReferential,
  type Referential,
} from "../../api";
import ReferentialFormModal, {
  type ReferentialFormValues,
} from "../../components/admin/ReferentialFormModal";
import "../../styles/administration.css";

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

export default function AdminReferentials() {
  const [referentials, setReferentials] = useState<Referential[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [formOpen, setFormOpen] = useState(false);
  const [formMode, setFormMode] = useState<"create" | "edit">("create");
  const [editing, setEditing] = useState<Referential | null>(null);
  const [formError, setFormError] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await listReferentials();
      setReferentials(response.items);
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
    setEditing(null);
    setFormError(null);
    setFormOpen(true);
  }

  function openEdit(ref: Referential) {
    setFormMode("edit");
    setEditing(ref);
    setFormError(null);
    setFormOpen(true);
  }

  async function handleFormSubmit(values: ReferentialFormValues) {
    setSaving(true);
    setFormError(null);
    try {
      if (formMode === "create") {
        await createReferential({
          label: values.label.trim(),
          category: values.category || undefined,
          description: values.description || undefined,
          status: values.status,
        });
      } else if (editing) {
        await updateReferential(editing.id, {
          label: values.label.trim(),
          category: values.category || undefined,
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

  async function handleDelete(ref: Referential) {
    if (!confirm(`Supprimer le référentiel « ${ref.label} » ?`)) return;
    try {
      await deleteReferential(ref.id);
      await loadData();
    } catch (e) {
      setError(parseApiError(e));
    }
  }

  async function handleToggleStatus(ref: Referential) {
    try {
      if (ref.status === "active") {
        await deactivateReferential(ref.id);
      } else {
        await activateReferential(ref.id);
      }
      await loadData();
    } catch (e) {
      setError(parseApiError(e));
    }
  }

  return (
    <div className="admin-users-page">
      <div className="admin-users-header">
        <div>
          <h2>Référentiels</h2>
          <p>Catalogue des référentiels de conformité proposés aux projets</p>
        </div>
        <button type="button" className="btn btn-primary" onClick={openCreate}>
          + Nouveau référentiel
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
        <div className="card">Chargement des référentiels…</div>
      ) : (
        <div className="card admin-users-table-wrapper">
          <table className="admin-users-table">
            <thead>
              <tr>
                <th>Libellé</th>
                <th>Code</th>
                <th>Catégorie</th>
                <th>Statut</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {referentials.length === 0 ? (
                <tr>
                  <td colSpan={5} style={{ color: "var(--muted)", textAlign: "center" }}>
                    Aucun référentiel
                  </td>
                </tr>
              ) : (
                referentials.map((ref) => (
                  <tr key={ref.id}>
                    <td>
                      <strong>{ref.label}</strong>
                    </td>
                    <td>
                      <code className="project-code-cell">{ref.code}</code>
                    </td>
                    <td>{ref.category || "—"}</td>
                    <td>
                      <span
                        className={`admin-status-badge ${
                          ref.status === "active" ? "active" : "disabled"
                        }`}
                      >
                        {statusLabel(ref.status)}
                      </span>
                    </td>
                    <td>
                      <div className="admin-users-actions">
                        <button
                          type="button"
                          className="btn btn-secondary btn-sm"
                          onClick={() => openEdit(ref)}
                        >
                          Modifier
                        </button>
                        <button
                          type="button"
                          className="btn btn-secondary btn-sm"
                          onClick={() => handleToggleStatus(ref)}
                        >
                          {ref.status === "active" ? "Désactiver" : "Activer"}
                        </button>
                        <button
                          type="button"
                          className="btn btn-danger btn-sm"
                          onClick={() => handleDelete(ref)}
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

      <ReferentialFormModal
        open={formOpen}
        mode={formMode}
        referential={editing}
        saving={saving}
        error={formError}
        onClose={() => setFormOpen(false)}
        onSubmit={handleFormSubmit}
      />
    </div>
  );
}
