import type { AdminOrganization } from "../api";

/** Normalise pour une recherche insensible à la casse et aux accents. */
export function normalizeText(value: string): string {
  return value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .trim();
}

/** Tri alphabétique stable par nom (locale FR). */
export function sortOrganizations(orgs: AdminOrganization[]): AdminOrganization[] {
  return [...orgs].sort((a, b) => a.name.localeCompare(b.name, "fr", { sensitivity: "base" }));
}

/** Organisations actives uniquement, triées alphabétiquement. */
export function activeOrganizations(orgs: AdminOrganization[]): AdminOrganization[] {
  return sortOrganizations(orgs.filter((o) => o.status === "active"));
}

/** Filtre par requête (nom ou code), insensible casse/accents, résultat trié. */
export function filterOrganizations(
  orgs: AdminOrganization[],
  query: string,
): AdminOrganization[] {
  const needle = normalizeText(query);
  const base = sortOrganizations(orgs);
  if (!needle) return base;
  return base.filter((o) => {
    const haystack = `${normalizeText(o.name)} ${normalizeText(o.code)}`;
    return haystack.includes(needle);
  });
}

/**
 * Insère ou remplace une organisation dans une liste (par id) puis retrie.
 * Utilisé pour faire apparaître immédiatement une organisation créée.
 */
export function upsertOrganization(
  list: AdminOrganization[],
  org: AdminOrganization,
): AdminOrganization[] {
  const others = list.filter((o) => o.id !== org.id);
  return sortOrganizations([...others, org]);
}

export function organizationLabelById(
  orgs: AdminOrganization[],
  id: string | null | undefined,
): string {
  if (!id) return "";
  return orgs.find((o) => o.id === id)?.name ?? "";
}
