import type { Referential } from "../api";
import { normalizeText } from "./organizationSelect";

/** Tri stable — ordre d'affichage backend (sort_order) puis libellé (locale FR). */
export function sortReferentials(refs: Referential[]): Referential[] {
  return [...refs].sort((a, b) => {
    if (a.sort_order !== b.sort_order) return a.sort_order - b.sort_order;
    return a.label.localeCompare(b.label, "fr", { sensitivity: "base" });
  });
}

/**
 * Insère ou remplace un référentiel dans une liste (par id) puis retrie.
 * Utilisé pour faire apparaître immédiatement un référentiel créé.
 */
export function upsertReferential(list: Referential[], ref: Referential): Referential[] {
  const others = list.filter((r) => r.id !== ref.id);
  return sortReferentials([...others, ref]);
}

/** Vrai si un référentiel de la liste porte déjà ce code (insensible à la casse). */
export function isDuplicateReferentialCode(list: Referential[], code: string): boolean {
  const needle = normalizeText(code);
  if (!needle) return false;
  return list.some((r) => normalizeText(r.code) === needle);
}

/** Ajoute un libellé à la sélection courante s'il n'y est pas déjà (pré-cochage). */
export function withReferentialPreselected(labels: string[], label: string): string[] {
  return labels.includes(label) ? labels : [...labels, label];
}

export type QuickAddReferentialValues = {
  label: string;
  code: string;
  description: string;
  status: string;
};

/**
 * Valide le formulaire d'ajout rapide d'un référentiel.
 * Renvoie un message d'erreur clair, ou null si valide.
 */
export function validateQuickAddReferential(
  values: QuickAddReferentialValues,
  existing: Referential[],
): string | null {
  if (!values.label.trim()) {
    return "Le nom du référentiel est obligatoire.";
  }
  if (!values.code.trim()) {
    return "Le code du référentiel est obligatoire.";
  }
  if (isDuplicateReferentialCode(existing, values.code)) {
    return `Un référentiel avec le code « ${values.code.trim()} » existe déjà.`;
  }
  return null;
}
