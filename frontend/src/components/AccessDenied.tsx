import { Link } from "react-router-dom";
import type { AppModule } from "../auth/permissions";

type AccessDeniedProps = {
  module?: AppModule;
};

const MODULE_LABELS: Record<AppModule, string> = {
  dashboard: "Dashboard",
  projects: "Projets",
  urbanism: "Urbanisme",
  soc: "SOC",
  settings: "Paramètres",
  grc: "Cybersécurité / GRC",
  ai: "IA & Connaissances",
  administration: "Administration",
};

export default function AccessDenied({ module }: AccessDeniedProps) {
  const label = module ? MODULE_LABELS[module] : "cette section";

  return (
    <div className="access-denied">
      <div className="access-denied-card">
        <h1>Accès refusé</h1>
        <p>
          Votre rôle ne vous permet pas d&apos;accéder au module <strong>{label}</strong>.
        </p>
        <Link to="/" className="access-denied-link">
          Retour au dashboard
        </Link>
      </div>
    </div>
  );
}
