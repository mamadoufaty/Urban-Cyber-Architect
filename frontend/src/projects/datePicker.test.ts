import { describe, expect, it } from "vitest";
import {
  addMonths,
  buildCalendarWeeks,
  daysInMonth,
  displayToIso,
  initialVisibleMonth,
  isValidIso,
  isoToDisplay,
  todayIso,
} from "./datePicker";

describe("datePicker helpers", () => {
  it("converts ISO to display (JJ/MM/AAAA)", () => {
    expect(isoToDisplay("2025-06-15")).toBe("15/06/2025");
    expect(isoToDisplay("")).toBe("");
    expect(isoToDisplay("2025-13-01")).toBe("");
    expect(isoToDisplay("not-a-date")).toBe("");
  });

  it("converts display to ISO and rejects invalid calendar dates", () => {
    expect(displayToIso("15/06/2025")).toBe("2025-06-15");
    expect(displayToIso(" 01/01/2030 ")).toBe("2030-01-01");
    expect(displayToIso("31/02/2025")).toBe(""); // 31 février n'existe pas
    expect(displayToIso("00/01/2025")).toBe("");
    expect(displayToIso("aa/bb/cccc")).toBe("");
  });

  it("validates ISO strings", () => {
    expect(isValidIso("2024-02-29")).toBe(true); // année bissextile
    expect(isValidIso("2025-02-29")).toBe(false);
    expect(isValidIso("2025-04-31")).toBe(false);
  });

  it("computes days in month", () => {
    expect(daysInMonth(2025, 1)).toBe(28); // février 2025
    expect(daysInMonth(2024, 1)).toBe(29); // février 2024
    expect(daysInMonth(2025, 5)).toBe(30); // juin
  });

  it("navigates months across year boundaries", () => {
    expect(addMonths(2025, 0, -1)).toEqual({ year: 2024, month: 11 });
    expect(addMonths(2025, 11, 1)).toEqual({ year: 2026, month: 0 });
    expect(addMonths(2025, 5, 12)).toEqual({ year: 2026, month: 5 });
  });

  it("builds a Monday-first 6x7 calendar grid", () => {
    // Juin 2025 : le 1er est un dimanche → 6 cellules du mois précédent en tête.
    const weeks = buildCalendarWeeks(2025, 5);
    expect(weeks).toHaveLength(6);
    weeks.forEach((week) => expect(week).toHaveLength(7));

    const firstOfMonth = weeks[0][6];
    expect(firstOfMonth.iso).toBe("2025-06-01");
    expect(firstOfMonth.inCurrentMonth).toBe(true);

    // Les 6 premières cellules appartiennent à mai (hors mois courant).
    for (let i = 0; i < 6; i += 1) {
      expect(weeks[0][i].inCurrentMonth).toBe(false);
    }

    const currentMonthDays = weeks.flat().filter((c) => c.inCurrentMonth);
    expect(currentMonthDays).toHaveLength(30);
  });

  it("produces a valid today ISO and initial visible month", () => {
    const iso = todayIso();
    expect(iso).toMatch(/^\d{4}-\d{2}-\d{2}$/);
    expect(isValidIso(iso)).toBe(true);

    expect(initialVisibleMonth("2023-03-10")).toEqual({ year: 2023, month: 2 });
    // Valeur vide → mois courant (dérivé de todayIso).
    const fallback = initialVisibleMonth("");
    expect(fallback.month).toBeGreaterThanOrEqual(0);
    expect(fallback.month).toBeLessThanOrEqual(11);
  });
});
