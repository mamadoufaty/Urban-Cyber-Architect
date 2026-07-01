import { Link } from "react-router-dom";
import { useActiveProject } from "../../context/ActiveProjectContext";

export default function ActiveProjectBar() {
  const { activeProject, clearActiveProject } = useActiveProject();

  if (!activeProject) {
    return null;
  }

  return (
    <div className="active-project-bar">
      <span className="active-project-label">Projet actif</span>
      <Link to={`/projects/${activeProject.id}`} className="active-project-link">
        <strong>{activeProject.name}</strong>
        {activeProject.code && <span className="active-project-code">{activeProject.code}</span>}
      </Link>
      <button
        type="button"
        className="active-project-clear"
        onClick={clearActiveProject}
        title="Désélectionner le projet actif"
      >
        ×
      </button>
    </div>
  );
}
