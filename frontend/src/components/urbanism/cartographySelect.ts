import type { Cartography, CartographyStatus, CartographyVersion } from "../../api";

export const CARTOGRAPHY_STATUS_LABELS: Record<CartographyStatus, string> = {
  draft: "Brouillon",
  in_validation: "En validation",
  validated: "Validée",
  archived: "Archivée",
};

export function cartographyStatusLabel(status: string): string {
  return CARTOGRAPHY_STATUS_LABELS[status as CartographyStatus] ?? status;
}

/** Tri alphabétique, cartographies archivées reléguées en fin de liste. */
export function sortCartographies(list: Cartography[]): Cartography[] {
  return [...list].sort((a, b) => {
    if (a.is_archived !== b.is_archived) return a.is_archived ? 1 : -1;
    return a.name.localeCompare(b.name, "fr", { sensitivity: "base" });
  });
}

/** Cartographie sélectionnée par défaut : conserve la sélection courante si elle
 * existe toujours, sinon la cartographie active du projet, sinon la première
 * disponible (non archivée en priorité). */
export function resolveDefaultCartographyId(
  list: Cartography[],
  previousId: string | null | undefined
): string | null {
  if (!list.length) return null;
  if (previousId && list.some((c) => c.id === previousId)) return previousId;
  const active = list.find((c) => c.is_active);
  if (active) return active.id;
  const nonArchived = list.find((c) => !c.is_archived);
  return (nonArchived ?? list[0]).id;
}

/** Version sélectionnée par défaut : conserve la sélection si elle existe
 * toujours dans la nouvelle liste, sinon la version courante. */
export function resolveDefaultVersionId(
  versions: CartographyVersion[],
  previousVersionId: string | null | undefined
): string | null {
  if (!versions.length) return null;
  if (previousVersionId && versions.some((v) => v.id === previousVersionId)) {
    return previousVersionId;
  }
  const current = versions.find((v) => v.is_current);
  return (current ?? versions[0]).id;
}

export function formatVersionLabel(version: Pick<CartographyVersion, "version">): string {
  return `v${version.version}`;
}

/** Une version consultée qui n'est pas la version courante est un instantané en
 * lecture seule (il faut la restaurer pour pouvoir la modifier). */
export function isHistoricalVersionSelected(
  versions: CartographyVersion[],
  selectedVersionId: string | null | undefined
): boolean {
  if (!selectedVersionId) return false;
  const version = versions.find((v) => v.id === selectedVersionId);
  return Boolean(version && !version.is_current);
}

export function isCartographyEditable(cartography: Pick<Cartography, "is_archived"> | null | undefined): boolean {
  if (!cartography) return false;
  return !cartography.is_archived;
}

export interface CartographyCreateInput {
  name: string;
  type: string;
  description?: string;
}

export function validateCartographyCreateInput(input: CartographyCreateInput): string | null {
  if (!input.name || !input.name.trim()) {
    return "Le nom de la cartographie est obligatoire.";
  }
  if (input.name.trim().length > 255) {
    return "Le nom de la cartographie est trop long (255 caractères maximum).";
  }
  if (!input.type) {
    return "Le type de cartographie est obligatoire.";
  }
  return null;
}

export function validateDuplicateName(name: string, existingNames: string[]): string | null {
  const trimmed = name.trim();
  if (!trimmed) return "Le nom de la nouvelle cartographie est obligatoire.";
  if (existingNames.some((n) => n.trim().toLowerCase() === trimmed.toLowerCase())) {
    return "Une cartographie porte déjà ce nom dans ce projet.";
  }
  return null;
}
