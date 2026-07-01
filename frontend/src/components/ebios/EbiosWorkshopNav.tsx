import type { EbiosWorkshopSpec } from "./types";

type Props = {
  workshops: EbiosWorkshopSpec[];
  activeWorkshop: number;
  onSelect: (number: number) => void;
  workshopStatuses: Map<number, string>;
};

export default function EbiosWorkshopNav({ workshops, activeWorkshop, onSelect, workshopStatuses }: Props) {
  return (
    <nav className="eb-workshop-nav" aria-label="Ateliers EBIOS RM">
      {workshops.map((w) => {
        const status = workshopStatuses.get(w.number) ?? "locked";
        const isActive = w.number === activeWorkshop;
        const isLocked = status === "locked";
        return (
          <button
            key={w.number}
            type="button"
            className={`eb-workshop-nav-item${isActive ? " active" : ""} status-${status}`}
            onClick={() => onSelect(w.number)}
            disabled={isLocked}
            aria-current={isActive ? "step" : undefined}
            title={isLocked ? "Atelier verrouillé — complétez l'atelier précédent" : undefined}
          >
            <span className="eb-workshop-nav-num">{w.number}</span>
            <span className="eb-workshop-nav-label">{w.short_label}</span>
          </button>
        );
      })}
    </nav>
  );
}
