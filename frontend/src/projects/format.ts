export function formatDateTime(value: string | null | undefined): string {
  if (!value) return "—";
  try {
    return new Date(value).toLocaleString("fr-FR", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return value;
  }
}

/** Extrait YYYY-MM-DD pour les champs input type="date". */
export function toDateInputValue(value: string | null | undefined): string {
  if (!value) return "";
  const match = /^(\d{4}-\d{2}-\d{2})/.exec(value);
  return match ? match[1] : "";
}

/** Affiche une date ISO en DD/MM/YYYY (sans décalage fuseau horaire). */
export function formatDateOnly(value: string | null | undefined): string {
  if (!value) return "—";
  const match = /^(\d{4})-(\d{2})-(\d{2})/.exec(value);
  if (match) {
    return `${match[3]}/${match[2]}/${match[1]}`;
  }
  try {
    return new Date(value).toLocaleDateString("fr-FR");
  } catch {
    return value;
  }
}

/** Valide l'ordre des dates projet (format YYYY-MM-DD). */
export function validateProjectDateRange(
  startDate: string,
  endDate: string,
): string | null {
  if (!startDate || !endDate) return null;
  if (endDate < startDate) {
    return "La date de fin doit être postérieure à la date de début.";
  }
  return null;
}

export function parseTagsInput(input: string): string[] {
  return input
    .split(",")
    .map((t) => t.trim())
    .filter(Boolean);
}

export function tagsToInput(tags: string[] | undefined): string {
  return (tags ?? []).join(", ");
}
