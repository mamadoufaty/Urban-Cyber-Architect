import type { TimelineItem } from "../../projects/dashboardMetrics";
import { formatDateTime } from "../../projects/format";

type Props = {
  items: TimelineItem[];
};

export default function ProjectTimeline({ items }: Props) {
  return (
    <div className="card project-timeline">
      <h4>Timeline projet</h4>
      <ol className="project-timeline-list">
        {items.map((item) => (
          <li
            key={item.id}
            className={`project-timeline-item project-timeline-${item.kind}`}
          >
            <div className="project-timeline-marker" aria-hidden />
            <div className="project-timeline-content">
              <div className="project-timeline-header">
                <strong>{item.label}</strong>
                {item.kind === "past" ? (
                  <time dateTime={item.date}>{formatDateTime(item.date)}</time>
                ) : (
                  <span className="project-timeline-future-label">À venir</span>
                )}
              </div>
              {item.details && <p>{item.details}</p>}
            </div>
          </li>
        ))}
      </ol>
    </div>
  );
}
