import type { AppModule } from "../auth/permissions";

export type NavItem = {
  path: string;
  label: string;
  module: AppModule;
};

export type NavSection = {
  id: string;
  title: string;
  module: AppModule;
  items: NavItem[];
};

export const PRINCIPAL_NAV: NavSection = {
  id: "principal",
  title: "Principal",
  module: "dashboard",
  items: [
    { path: "/", label: "Dashboard", module: "dashboard" },
    { path: "/projects", label: "Projets", module: "projects" },
  ],
};

export const URBANISM_NAV: NavSection = {
  id: "urbanism",
  title: "Urbanisme",
  module: "urbanism",
  items: [
    { path: "/schema-urbanisme", label: "Moteur d'urbanisme", module: "urbanism" },
    { path: "/validation-metamodele", label: "Validation métamodèle", module: "urbanism" },
    { path: "/objectifs", label: "Objectifs", module: "urbanism" },
    { path: "/metiers", label: "Métiers", module: "urbanism" },
    { path: "/processus", label: "Processus", module: "urbanism" },
    { path: "/fonctionnel", label: "Fonctionnel", module: "urbanism" },
    { path: "/applicatif", label: "Applicatif", module: "urbanism" },
    { path: "/technique", label: "Technique", module: "urbanism" },
  ],
};

export const SOC_NAV: NavSection = {
  id: "soc",
  title: "SOC",
  module: "soc",
  items: [
    { path: "/soc/wazuh", label: "Wazuh", module: "soc" },
    { path: "/soc/correlations", label: "Corrélations", module: "soc" },
  ],
};

export const SETTINGS_NAV: NavSection = {
  id: "settings",
  title: "Paramètres",
  module: "settings",
  items: [{ path: "/parametres/connecteurs/wazuh", label: "Connecteur Wazuh", module: "settings" }],
};

export const CYBER_NAV: NavSection = {
  id: "grc",
  title: "Cybersécurité",
  module: "grc",
  items: [
    { path: "/ebios", label: "EBIOS RM", module: "grc" },
    { path: "/registre-risques", label: "Registre des risques", module: "grc" },
    { path: "/dashboard-rssi", label: "Dashboard RSSI", module: "grc" },
    { path: "/declaration-applicabilite", label: "Déclaration d'applicabilité", module: "grc" },
    { path: "/plan-traitement-risques", label: "Plan de traitement des risques", module: "grc" },
    { path: "/architecture", label: "Architecture Cyber", module: "grc" },
    { path: "/livrables", label: "Livrables", module: "grc" },
  ],
};

export const AI_NAV: NavSection = {
  id: "ai",
  title: "IA & Connaissances",
  module: "ai",
  items: [
    { path: "/ai-governance", label: "AI Governance", module: "ai" },
    { path: "/prompt-studio", label: "Prompt Studio", module: "ai" },
    { path: "/knowledge-base", label: "Knowledge Base", module: "ai" },
  ],
};

export const ADMIN_NAV: NavSection = {
  id: "administration",
  title: "Administration",
  module: "administration",
  items: [{ path: "/administration/users", label: "Utilisateurs", module: "administration" }],
};

export const NAV_SECTIONS: NavSection[] = [
  PRINCIPAL_NAV,
  URBANISM_NAV,
  SOC_NAV,
  SETTINGS_NAV,
  CYBER_NAV,
  AI_NAV,
  ADMIN_NAV,
];

export const URBANISM_MODULES = URBANISM_NAV.items;
export const SOC_MODULES = SOC_NAV.items;
export const SETTINGS_MODULES = SETTINGS_NAV.items;
export const CYBER_MODULES = CYBER_NAV.items;
