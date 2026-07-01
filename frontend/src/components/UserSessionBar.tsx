import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

type UserSessionBarProps = {
  variant?: "sidebar" | "header";
};

export default function UserSessionBar({ variant = "sidebar" }: UserSessionBarProps) {
  const { user, isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();

  if (!isAuthenticated || !user) {
    return null;
  }

  const handleLogout = () => {
    logout();
    navigate("/login", { replace: true });
  };

  if (variant === "header") {
    return (
      <div className="app-user-bar">
        <div className="app-user-bar-text">
          <span className="app-user-name">{user.displayName}</span>
          <span className="app-user-role">{user.role}</span>
        </div>
        <button type="button" className="app-logout-btn" onClick={handleLogout}>
          Déconnexion
        </button>
      </div>
    );
  }

  return (
    <div className="sidebar-user">
      <div className="sidebar-user-info">
        <strong className="sidebar-user-name">{user.displayName}</strong>
        <span className="sidebar-user-role">{user.role}</span>
      </div>
      <button type="button" className="sidebar-logout-btn" onClick={handleLogout}>
        Déconnexion
      </button>
    </div>
  );
}
