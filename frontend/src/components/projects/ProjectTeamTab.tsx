import { useCallback, useEffect, useState } from "react";
import {
  addProjectMember,
  listAdminUsers,
  listProjectMembers,
  removeProjectMember,
  type AdminUser,
  type ProjectMember,
} from "../../api";
import { PROJECT_ROLES, projectRoleLabel } from "../../projects/constants";
import { formatDateTime } from "../../projects/format";

type Props = {
  projectId: string;
};

function userLabel(user: AdminUser): string {
  const name = [user.first_name, user.last_name].filter(Boolean).join(" ");
  return name ? `${name} (${user.username})` : user.username;
}

export default function ProjectTeamTab({ projectId }: Props) {
  const [members, setMembers] = useState<ProjectMember[]>([]);
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [userId, setUserId] = useState("");
  const [projectRole, setProjectRole] = useState<string>(PROJECT_ROLES[0].value);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const userMap = new Map(users.map((u) => [u.id, u]));

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [membersRes, usersRes] = await Promise.all([
        listProjectMembers(projectId),
        listAdminUsers(),
      ]);
      setMembers(membersRes);
      setUsers(usersRes.items.filter((u) => u.status === "active"));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erreur de chargement");
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    load();
  }, [load]);

  async function handleAdd(e: React.FormEvent) {
    e.preventDefault();
    if (!userId) return;
    setSaving(true);
    setError(null);
    try {
      await addProjectMember(projectId, { user_id: userId, project_role: projectRole });
      setUserId("");
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erreur lors de l'ajout");
    } finally {
      setSaving(false);
    }
  }

  async function handleRemove(member: ProjectMember) {
    if (!confirm("Retirer ce membre du projet ?")) return;
    setError(null);
    try {
      await removeProjectMember(projectId, member.id);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erreur lors de la suppression");
    }
  }

  if (loading) {
    return <div className="card">Chargement de l'équipe…</div>;
  }

  return (
    <div className="project-tab-panel">
      {error && (
        <div className="card project-error" role="alert">
          {error}
        </div>
      )}

      <div className="card project-team-form">
        <h4>Ajouter un membre</h4>
        <form className="project-team-add" onSubmit={handleAdd}>
          <select value={userId} onChange={(e) => setUserId(e.target.value)} required>
            <option value="">Sélectionner un utilisateur</option>
            {users.map((user) => (
              <option key={user.id} value={user.id}>
                {userLabel(user)}
              </option>
            ))}
          </select>
          <select value={projectRole} onChange={(e) => setProjectRole(e.target.value)}>
            {PROJECT_ROLES.map((role) => (
              <option key={role.value} value={role.value}>
                {role.label}
              </option>
            ))}
          </select>
          <button type="submit" className="btn btn-primary" disabled={saving}>
            Ajouter
          </button>
        </form>
      </div>

      <div className="projects-table-wrapper card">
        <table className="projects-table">
          <thead>
            <tr>
              <th>Utilisateur</th>
              <th>Rôle projet</th>
              <th>Ajouté le</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {members.length === 0 ? (
              <tr>
                <td colSpan={4} style={{ color: "var(--muted)" }}>
                  Aucun membre pour ce projet.
                </td>
              </tr>
            ) : (
              members.map((member) => {
                const user = userMap.get(member.user_id);
                return (
                  <tr key={member.id}>
                    <td>{user ? userLabel(user) : member.user_id}</td>
                    <td>
                      <span className="status-badge">{projectRoleLabel(member.project_role)}</span>
                    </td>
                    <td>{formatDateTime(member.created_at)}</td>
                    <td>
                      <button
                        type="button"
                        className="btn btn-danger btn-sm"
                        onClick={() => handleRemove(member)}
                      >
                        Retirer
                      </button>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
