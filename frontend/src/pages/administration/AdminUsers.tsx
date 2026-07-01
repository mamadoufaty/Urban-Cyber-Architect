import { useCallback, useEffect, useState } from "react";
import {
  type AdminOrganization,
  type AdminRole,
  type AdminUser,
  createAdminUser,
  deleteAdminUser,
  disableAdminUser,
  enableAdminUser,
  listAdminOrganizations,
  listAdminRoles,
  listAdminUsers,
  resetAdminUserPassword,
  updateAdminUser,
} from "../../api";
import ResetPasswordModal from "../../components/admin/ResetPasswordModal";
import UserFormModal, { type UserFormValues } from "../../components/admin/UserFormModal";
import "../../styles/administration.css";

function formatDate(value: string | null): string {
  if (!value) return "—";
  try {
    return new Date(value).toLocaleString("fr-FR");
  } catch {
    return value;
  }
}

function statusLabel(status: string): string {
  return status === "active" ? "Actif" : status === "disabled" ? "Désactivé" : status;
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

export default function AdminUsers() {
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [roles, setRoles] = useState<AdminRole[]>([]);
  const [organizations, setOrganizations] = useState<AdminOrganization[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [formOpen, setFormOpen] = useState(false);
  const [formMode, setFormMode] = useState<"create" | "edit">("create");
  const [editingUser, setEditingUser] = useState<AdminUser | null>(null);
  const [formError, setFormError] = useState<string | null>(null);
  const [resetUser, setResetUser] = useState<AdminUser | null>(null);
  const [resetError, setResetError] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [usersRes, rolesRes, orgsRes] = await Promise.all([
        listAdminUsers(),
        listAdminRoles(),
        listAdminOrganizations(),
      ]);
      setUsers(usersRes.items);
      setRoles(rolesRes.items);
      setOrganizations(orgsRes.items);
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
    setEditingUser(null);
    setFormError(null);
    setFormOpen(true);
  }

  function openEdit(user: AdminUser) {
    setFormMode("edit");
    setEditingUser(user);
    setFormError(null);
    setFormOpen(true);
  }

  async function handleFormSubmit(values: UserFormValues) {
    setSaving(true);
    setFormError(null);
    try {
      if (formMode === "create") {
        await createAdminUser({
          username: values.username.trim(),
          password: values.password,
          first_name: values.first_name || undefined,
          last_name: values.last_name || undefined,
          email: values.email || undefined,
          phone: values.phone || undefined,
          organization_id: values.organization_id || undefined,
          function: values.function || undefined,
          role_id: values.role_id || undefined,
          status: values.status,
        });
      } else if (editingUser) {
        await updateAdminUser(editingUser.id, {
          first_name: values.first_name || undefined,
          last_name: values.last_name || undefined,
          email: values.email || undefined,
          phone: values.phone || undefined,
          organization_id: values.organization_id || null,
          function: values.function || undefined,
          role_id: values.role_id || null,
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

  async function handleDisable(user: AdminUser) {
    if (!confirm(`Désactiver le compte « ${user.username} » ?`)) return;
    try {
      await disableAdminUser(user.id);
      await loadData();
    } catch (e) {
      setError(parseApiError(e));
    }
  }

  async function handleEnable(user: AdminUser) {
    try {
      await enableAdminUser(user.id);
      await loadData();
    } catch (e) {
      setError(parseApiError(e));
    }
  }

  async function handleDelete(user: AdminUser) {
    if (!confirm(`Supprimer définitivement « ${user.username} » ?`)) return;
    try {
      await deleteAdminUser(user.id);
      await loadData();
    } catch (e) {
      setError(parseApiError(e));
    }
  }

  async function handleResetPassword(password: string) {
    if (!resetUser) return;
    setSaving(true);
    setResetError(null);
    try {
      await resetAdminUserPassword(resetUser.id, password);
      setResetUser(null);
    } catch (e) {
      setResetError(parseApiError(e));
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="admin-users-page">
      <div className="admin-users-header">
        <div>
          <h2>Utilisateurs</h2>
          <p>Gestion des comptes, rôles et organisations</p>
        </div>
        <button type="button" className="btn btn-primary" onClick={openCreate}>
          + Nouvel utilisateur
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
        <div className="card">Chargement des utilisateurs…</div>
      ) : (
        <div className="card admin-users-table-wrapper">
          <table className="admin-users-table">
            <thead>
              <tr>
                <th>Nom</th>
                <th>Prénom</th>
                <th>Username</th>
                <th>Email</th>
                <th>Téléphone</th>
                <th>Organisation</th>
                <th>Fonction</th>
                <th>Rôle</th>
                <th>Statut</th>
                <th>Dernière connexion</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.length === 0 ? (
                <tr>
                  <td colSpan={11} style={{ color: "var(--muted)", textAlign: "center" }}>
                    Aucun utilisateur
                  </td>
                </tr>
              ) : (
                users.map((user) => (
                  <tr key={user.id}>
                    <td>{user.last_name || "—"}</td>
                    <td>{user.first_name || "—"}</td>
                    <td>
                      <strong>{user.username}</strong>
                    </td>
                    <td>{user.email || "—"}</td>
                    <td>{user.phone || "—"}</td>
                    <td>{user.organization_name || "—"}</td>
                    <td>{user.function || "—"}</td>
                    <td>{user.role_code || "—"}</td>
                    <td>
                      <span
                        className={`admin-status-badge ${user.status === "active" ? "active" : "disabled"}`}
                      >
                        {statusLabel(user.status)}
                      </span>
                    </td>
                    <td>{formatDate(user.last_login_at)}</td>
                    <td>
                      <div className="admin-users-actions">
                        <button
                          type="button"
                          className="btn btn-secondary btn-sm"
                          onClick={() => openEdit(user)}
                        >
                          Modifier
                        </button>
                        {user.status === "active" ? (
                          <button
                            type="button"
                            className="btn btn-secondary btn-sm"
                            onClick={() => handleDisable(user)}
                          >
                            Désactiver
                          </button>
                        ) : (
                          <button
                            type="button"
                            className="btn btn-secondary btn-sm"
                            onClick={() => handleEnable(user)}
                          >
                            Réactiver
                          </button>
                        )}
                        <button
                          type="button"
                          className="btn btn-secondary btn-sm"
                          onClick={() => {
                            setResetError(null);
                            setResetUser(user);
                          }}
                        >
                          Réinit. MDP
                        </button>
                        <button
                          type="button"
                          className="btn btn-danger btn-sm"
                          onClick={() => handleDelete(user)}
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

      <UserFormModal
        open={formOpen}
        mode={formMode}
        user={editingUser}
        roles={roles}
        organizations={organizations}
        saving={saving}
        error={formError}
        onClose={() => setFormOpen(false)}
        onSubmit={handleFormSubmit}
      />

      <ResetPasswordModal
        open={resetUser !== null}
        user={resetUser}
        saving={saving}
        error={resetError}
        onClose={() => setResetUser(null)}
        onSubmit={handleResetPassword}
      />
    </div>
  );
}
