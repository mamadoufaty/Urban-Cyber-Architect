import type { EbiosWorkshop } from "./types";
import { WORKSHOP_STATUS_LABELS } from "./constants";

type Props = {
  workshops: EbiosWorkshop[];
  overallPercent: number;
};

export default function EbiosProgressBar({ workshops, overallPercent }: Props) {
  return (
    <div className="eb-panel eb-progress">
      <div className="eb-progress-header">
        <strong>Progression EBIOS RM</strong>
        <span className="eb-progress-percent">{overallPercent}%</span>
      </div>
      <div className="eb-progress-track">
        <div className="eb-progress-fill" style={{ width: `${overallPercent}%` }} />
      </div>
      <ul className="eb-progress-steps">
        {workshops.map((w) => (
          <li key={w.id} className={`eb-progress-step status-${w.status}`}>
            <span className="eb-step-num">{w.workshop_number}</span>
            <span className="eb-step-label">{w.summary?.label as string ?? `Atelier ${w.workshop_number}`}</span>
            <span className="eb-step-status">{WORKSHOP_STATUS_LABELS[w.status] ?? w.status}</span>
            <span className="eb-step-pct">{w.progress_percent}%</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
