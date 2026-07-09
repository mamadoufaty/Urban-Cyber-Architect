/**
 * Helpers purs (sans dépendance au DOM) pour le composant DatePicker.
 *
 * Contrats :
 * - Stockage ISO : "YYYY-MM-DD".
 * - Affichage utilisateur : "JJ/MM/AAAA".
 * - Toutes les opérations sont indépendantes du fuseau horaire (aucune
 *   conversion via Date.parse d'une chaîne ISO).
 */

export const MONTH_LABELS_FR = [
  "Janvier",
  "Février",
  "Mars",
  "Avril",
  "Mai",
  "Juin",
  "Juillet",
  "Août",
  "Septembre",
  "Octobre",
  "Novembre",
  "Décembre",
] as const;

// Semaine commençant le lundi (convention française).
export const WEEKDAY_LABELS_FR = ["Lu", "Ma", "Me", "Je", "Ve", "Sa", "Di"] as const;

export type ParsedDate = { year: number; month: number; day: number };

export type CalendarDay = {
  iso: string;
  day: number;
  inCurrentMonth: boolean;
};

const ISO_RE = /^(\d{4})-(\d{2})-(\d{2})$/;
const DISPLAY_RE = /^(\d{2})\/(\d{2})\/(\d{4})$/;

function pad2(value: number): string {
  return String(value).padStart(2, "0");
}

/** Nombre de jours dans un mois (month 0-indexé). */
export function daysInMonth(year: number, month: number): number {
  return new Date(year, month + 1, 0).getDate();
}

/** Vrai si le triplet (année, mois, jour) forme une date calendaire réelle. */
export function isValidYmd(year: number, month: number, day: number): boolean {
  if (month < 0 || month > 11) return false;
  if (day < 1) return false;
  return day <= daysInMonth(year, month);
}

/** Analyse une chaîne ISO "YYYY-MM-DD". Renvoie null si invalide. */
export function parseIso(iso: string | null | undefined): ParsedDate | null {
  if (!iso) return null;
  const match = ISO_RE.exec(iso);
  if (!match) return null;
  const year = Number(match[1]);
  const month = Number(match[2]) - 1;
  const day = Number(match[3]);
  if (!isValidYmd(year, month, day)) return null;
  return { year, month, day };
}

export function isValidIso(iso: string | null | undefined): boolean {
  return parseIso(iso) !== null;
}

export function toIso(year: number, month: number, day: number): string {
  return `${year}-${pad2(month + 1)}-${pad2(day)}`;
}

/** "YYYY-MM-DD" → "JJ/MM/AAAA" (chaîne vide si invalide). */
export function isoToDisplay(iso: string | null | undefined): string {
  const parsed = parseIso(iso);
  if (!parsed) return "";
  return `${pad2(parsed.day)}/${pad2(parsed.month + 1)}/${parsed.year}`;
}

/** "JJ/MM/AAAA" → "YYYY-MM-DD" (chaîne vide si invalide). */
export function displayToIso(display: string | null | undefined): string {
  if (!display) return "";
  const match = DISPLAY_RE.exec(display.trim());
  if (!match) return "";
  const day = Number(match[1]);
  const month = Number(match[2]) - 1;
  const year = Number(match[3]);
  if (!isValidYmd(year, month, day)) return "";
  return toIso(year, month, day);
}

/** Date du jour au format ISO (heure locale). */
export function todayIso(): string {
  const now = new Date();
  return toIso(now.getFullYear(), now.getMonth(), now.getDate());
}

/** Décale (année, mois) de `delta` mois en gérant les débordements. */
export function addMonths(
  year: number,
  month: number,
  delta: number,
): { year: number; month: number } {
  const total = year * 12 + month + delta;
  return { year: Math.floor(total / 12), month: ((total % 12) + 12) % 12 };
}

/** Indice lundi=0 … dimanche=6 pour le 1er du mois. */
function mondayFirstOffset(year: number, month: number): number {
  const jsDay = new Date(year, month, 1).getDay(); // 0=dimanche
  return (jsDay + 6) % 7;
}

/**
 * Construit une grille calendaire 6×7 (semaines de 7 jours), incluant les jours
 * débordants des mois adjacents pour un affichage complet.
 */
export function buildCalendarWeeks(year: number, month: number): CalendarDay[][] {
  const offset = mondayFirstOffset(year, month);
  const totalDays = daysInMonth(year, month);
  const cells: CalendarDay[] = [];

  // Jours du mois précédent (remplissage de tête).
  const prev = addMonths(year, month, -1);
  const prevDays = daysInMonth(prev.year, prev.month);
  for (let i = offset - 1; i >= 0; i -= 1) {
    const day = prevDays - i;
    cells.push({ iso: toIso(prev.year, prev.month, day), day, inCurrentMonth: false });
  }

  // Jours du mois courant.
  for (let day = 1; day <= totalDays; day += 1) {
    cells.push({ iso: toIso(year, month, day), day, inCurrentMonth: true });
  }

  // Jours du mois suivant (remplissage de queue jusqu'à 42 cellules).
  const next = addMonths(year, month, 1);
  let nextDay = 1;
  while (cells.length < 42) {
    cells.push({ iso: toIso(next.year, next.month, nextDay), day: nextDay, inCurrentMonth: false });
    nextDay += 1;
  }

  const weeks: CalendarDay[][] = [];
  for (let i = 0; i < cells.length; i += 7) {
    weeks.push(cells.slice(i, i + 7));
  }
  return weeks;
}

/** Mois/année à afficher initialement à l'ouverture du calendrier. */
export function initialVisibleMonth(iso: string | null | undefined): {
  year: number;
  month: number;
} {
  const parsed = parseIso(iso);
  if (parsed) return { year: parsed.year, month: parsed.month };
  const today = parseIso(todayIso());
  // todayIso() est toujours valide.
  return { year: today!.year, month: today!.month };
}
