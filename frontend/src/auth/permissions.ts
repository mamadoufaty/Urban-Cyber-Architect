export type UserRole = "admin" | "rssi" | "consultant" | "soc" | "metier";

export type AppModule =
  | "dashboard"
  | "projects"
  | "urbanism"
  | "soc"
  | "settings"
  | "grc"
  | "ai"
  | "administration";

export const ALL_MODULES: AppModule[] = [
  "dashboard",
  "projects",
  "urbanism",
  "soc",
  "settings",
  "grc",
  "ai",
  "administration",
];

/** Matrice RBAC — modules autorisés par rôle. */
export const ROLE_PERMISSIONS: Record<UserRole, readonly AppModule[]> = {
  admin: ALL_MODULES,
  rssi: ["dashboard", "projects", "urbanism", "soc", "grc", "ai", "settings"],
  consultant: ["dashboard", "projects", "urbanism", "grc", "ai"],
  soc: ["dashboard", "projects", "soc", "settings"],
  metier: ["dashboard", "urbanism"],
};

export function isUserRole(role: string): role is UserRole {
  return role in ROLE_PERMISSIONS;
}

export function hasPermission(role: string | undefined | null, module: AppModule): boolean {
  if (!role || !isUserRole(role)) {
    return false;
  }
  return ROLE_PERMISSIONS[role].includes(module);
}

const PATH_MODULE_MAP: Record<string, AppModule> = {
  "/": "dashboard",
  "/projects": "projects",
  "/schema-urbanisme": "urbanism",
  "/validation-metamodele": "urbanism",
  "/objectifs": "urbanism",
  "/metiers": "urbanism",
  "/processus": "urbanism",
  "/fonctionnel": "urbanism",
  "/applicatif": "urbanism",
  "/technique": "urbanism",
  "/soc/wazuh": "soc",
  "/soc/correlations": "soc",
  "/parametres/connecteurs/wazuh": "settings",
  "/ebios": "grc",
  "/registre-risques": "grc",
  "/dashboard-rssi": "grc",
  "/declaration-applicabilite": "grc",
  "/plan-traitement-risques": "grc",
  "/architecture": "grc",
  "/livrables": "grc",
  "/ai-governance": "ai",
  "/prompt-studio": "ai",
  "/knowledge-base": "ai",
  "/administration/users": "administration",
};

export function moduleForPath(pathname: string): AppModule | null {
  const normalized = pathname.replace(/\/+$/, "") || "/";
  return PATH_MODULE_MAP[normalized] ?? null;
}

export function canAccessPath(role: string | undefined | null, pathname: string): boolean {
  const module = moduleForPath(pathname);
  if (!module) {
    return false;
  }
  return hasPermission(role, module);
}
