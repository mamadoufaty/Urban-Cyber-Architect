import { useMemo } from "react";
import type { PtrTimeline, TimelineScale } from "./types";

type Props = {
  timeline: PtrTimeline | null;
  scale: TimelineScale;
  onScaleChange: (scale: TimelineScale) => void;
};

function parseDate(value: string): Date | null {
  if (!value) return null;
  const iso = value.slice(0, 10);
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? null : d;
}

function priorityClass(priority: string): string {
  const map: Record<string, string> = {
    Critique: "ptr-priority-critical",
    Élevée: "ptr-priority-high",
    Moyenne: "ptr-priority-medium",
    Faible: "ptr-priority-low",
  };
  return map[priority] ?? "ptr-priority-medium";
}

export default function PtrTimelineView({ timeline, scale, onScaleChange }: Props) {
  const reference = useMemo(() => {
    if (!timeline?.reference_date) return new Date();
    return new Date(timeline.reference_date);
  }, [timeline]);

  const rangeDays = scale === "today" ? 1 : scale === "week" ? 7 : 30;
  const rangeEnd = new Date(reference);
  rangeEnd.setDate(rangeEnd.getDate() + rangeDays);

  const visibleItems = useMemo(() => {
    if (!timeline) return [];
    return timeline.items.filter((item) => {
      const due = parseDate(item.due_date);
      if (!due) return scale === "month";
      return due >= reference && due <= rangeEnd;
    });
  }, [timeline, reference, rangeEnd, scale]);

  if (!timeline) return null;

  return (
    <section className="ptr-timeline" aria-label="Vue chronologique PTR">
      <div className="ptr-timeline-toolbar">
        <h2>Timeline</h2>
        <div className="ptr-timeline-scales" role="tablist">
          {(
            [
              ["today", "Aujourd'hui"],
              ["week", "Semaine"],
              ["month", "Mois"],
            ] as const
          ).map(([key, label]) => (
            <button
              key={key}
              type="button"
              role="tab"
              aria-selected={scale === key}
              className={`ptr-btn ptr-btn-ghost${scale === key ? " ptr-scale-active" : ""}`}
              onClick={() => onScaleChange(key)}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {(timeline.overdue.length > 0 || timeline.due_soon.length > 0) && (
        <div className="ptr-timeline-alerts">
          {timeline.overdue.length > 0 && (
            <div className="ptr-alert ptr-alert-overdue">
              <strong>Retards ({timeline.overdue.length})</strong>
              <ul>
                {timeline.overdue.slice(0, 5).map((item) => (
                  <li key={item.ptr_id}>
                    {item.label} — {item.responsible} — {item.due_date || "sans échéance"}
                  </li>
                ))}
              </ul>
            </div>
          )}
          {timeline.due_soon.length > 0 && (
            <div className="ptr-alert ptr-alert-soon">
              <strong>Échéances proches ({timeline.due_soon.length})</strong>
              <ul>
                {timeline.due_soon.slice(0, 5).map((item) => (
                  <li key={item.ptr_id}>
                    {item.label} — {item.due_date}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      <div className="ptr-gantt">
        <div className="ptr-gantt-header">
          <span>Action</span>
          <span>Échéance</span>
          <span>Avancement</span>
        </div>
        {visibleItems.length === 0 && (
          <div className="ptr-empty ptr-gantt-empty">Aucune action sur cette période.</div>
        )}
        {visibleItems.map((item) => {
          const due = parseDate(item.due_date);
          const offset = due
            ? Math.min(100, Math.max(0, ((due.getTime() - reference.getTime()) / (rangeDays * 86400000)) * 100))
            : 50;
          return (
            <div key={item.ptr_id} className={`ptr-gantt-row${item.overdue ? " ptr-gantt-overdue" : ""}`}>
              <div className="ptr-gantt-label">
                <span className={`ptr-badge ${priorityClass(item.priority)}`}>{item.priority}</span>
                <span>{item.label}</span>
                <small>{item.responsible}</small>
              </div>
              <div className="ptr-gantt-track">
                <div
                  className="ptr-gantt-marker"
                  style={{ left: `${offset}%` }}
                  title={item.due_date || "—"}
                />
                <div
                  className="ptr-gantt-bar"
                  style={{ width: `${item.progress_percent}%` }}
                />
              </div>
              <div className="ptr-gantt-meta">
                <span>{item.due_date || "—"}</span>
                <span>{item.progress_percent}%</span>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
