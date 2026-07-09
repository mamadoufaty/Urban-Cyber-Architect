import { useEffect, useMemo, useRef, useState } from "react";
import {
  MONTH_LABELS_FR,
  WEEKDAY_LABELS_FR,
  addMonths,
  buildCalendarWeeks,
  displayToIso,
  initialVisibleMonth,
  isoToDisplay,
  todayIso,
} from "../../projects/datePicker";

type DatePickerProps = {
  id?: string;
  value: string;
  onChange: (iso: string) => void;
  /** Borne minimale ISO (les jours antérieurs sont désactivés). */
  min?: string;
  disabled?: boolean;
  ariaLabel?: string;
};

const YEAR_RANGE = 12;

export default function DatePicker({
  id,
  value,
  onChange,
  min,
  disabled,
  ariaLabel,
}: DatePickerProps) {
  const [open, setOpen] = useState(false);
  const [text, setText] = useState(() => isoToDisplay(value));
  const [visible, setVisible] = useState(() => initialVisibleMonth(value));
  const containerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    setText(isoToDisplay(value));
  }, [value]);

  useEffect(() => {
    if (open) setVisible(initialVisibleMonth(value));
  }, [open, value]);

  useEffect(() => {
    if (!open) return;
    function onPointerDown(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") setOpen(false);
    }
    document.addEventListener("mousedown", onPointerDown);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onPointerDown);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  const weeks = useMemo(
    () => buildCalendarWeeks(visible.year, visible.month),
    [visible.year, visible.month],
  );

  const years = useMemo(() => {
    const base = visible.year;
    const start = base - YEAR_RANGE;
    return Array.from({ length: YEAR_RANGE * 2 + 1 }, (_, i) => start + i);
  }, [visible.year]);

  function commitText(next: string) {
    setText(next);
    const iso = displayToIso(next);
    if (iso) {
      onChange(iso);
    } else if (next.trim() === "") {
      onChange("");
    }
  }

  function selectDay(iso: string) {
    if (min && iso < min) return;
    onChange(iso);
    setText(isoToDisplay(iso));
    setOpen(false);
  }

  function goToToday() {
    const iso = todayIso();
    if (min && iso < min) {
      // Aujourd'hui est antérieur à la borne : on se contente d'afficher le mois.
      setVisible(initialVisibleMonth(iso));
      return;
    }
    selectDay(iso);
  }

  function shiftMonth(delta: number) {
    setVisible((prev) => addMonths(prev.year, prev.month, delta));
  }

  return (
    <div className="uca-datepicker" ref={containerRef}>
      <div className="uca-datepicker-field">
        <input
          id={id}
          type="text"
          inputMode="numeric"
          className="uca-datepicker-input"
          placeholder="JJ/MM/AAAA"
          value={text}
          disabled={disabled}
          aria-label={ariaLabel}
          autoComplete="off"
          onChange={(e) => commitText(e.target.value)}
          onFocus={() => !disabled && setOpen(true)}
          onClick={() => !disabled && setOpen(true)}
        />
        <button
          type="button"
          className="uca-datepicker-toggle"
          disabled={disabled}
          aria-label="Ouvrir le calendrier"
          aria-haspopup="dialog"
          aria-expanded={open}
          onClick={() => !disabled && setOpen((o) => !o)}
        >
          📅
        </button>
      </div>

      {open && !disabled && (
        <div className="uca-datepicker-popup" role="dialog" aria-label="Calendrier">
          <div className="uca-datepicker-nav">
            <button
              type="button"
              className="uca-datepicker-navbtn"
              aria-label="Mois précédent"
              onClick={() => shiftMonth(-1)}
            >
              ‹
            </button>
            <div className="uca-datepicker-selectors">
              <select
                aria-label="Mois"
                value={visible.month}
                onChange={(e) => setVisible((p) => ({ ...p, month: Number(e.target.value) }))}
              >
                {MONTH_LABELS_FR.map((label, index) => (
                  <option key={label} value={index}>
                    {label}
                  </option>
                ))}
              </select>
              <select
                aria-label="Année"
                value={visible.year}
                onChange={(e) => setVisible((p) => ({ ...p, year: Number(e.target.value) }))}
              >
                {years.map((year) => (
                  <option key={year} value={year}>
                    {year}
                  </option>
                ))}
              </select>
            </div>
            <button
              type="button"
              className="uca-datepicker-navbtn"
              aria-label="Mois suivant"
              onClick={() => shiftMonth(1)}
            >
              ›
            </button>
          </div>

          <div className="uca-datepicker-grid" role="grid">
            <div className="uca-datepicker-weekdays" role="row">
              {WEEKDAY_LABELS_FR.map((label) => (
                <span key={label} className="uca-datepicker-weekday" role="columnheader">
                  {label}
                </span>
              ))}
            </div>
            {weeks.map((week, wi) => (
              <div key={wi} className="uca-datepicker-week" role="row">
                {week.map((cell) => {
                  const isSelected = cell.iso === value;
                  const isToday = cell.iso === todayIso();
                  const isDisabled = Boolean(min && cell.iso < min);
                  const classes = [
                    "uca-datepicker-day",
                    cell.inCurrentMonth ? "" : "is-outside",
                    isSelected ? "is-selected" : "",
                    isToday ? "is-today" : "",
                    isDisabled ? "is-disabled" : "",
                  ]
                    .filter(Boolean)
                    .join(" ");
                  return (
                    <button
                      key={cell.iso}
                      type="button"
                      role="gridcell"
                      className={classes}
                      disabled={isDisabled}
                      aria-selected={isSelected}
                      onClick={() => selectDay(cell.iso)}
                    >
                      {cell.day}
                    </button>
                  );
                })}
              </div>
            ))}
          </div>

          <div className="uca-datepicker-footer">
            <button type="button" className="uca-datepicker-today" onClick={goToToday}>
              Aujourd'hui
            </button>
            {value && (
              <button
                type="button"
                className="uca-datepicker-clear"
                onClick={() => {
                  onChange("");
                  setText("");
                  setOpen(false);
                }}
              >
                Effacer
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
