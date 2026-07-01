import type { ExposureItem } from "./dashboardTypes";

interface Props {
  title: string;
  items: ExposureItem[];
}

function ExposureBars({ items }: { items: ExposureItem[] }) {
  const max = Math.max(...items.map((i) => i.count), 1);
  return (
    <ul className="grc-dash-exposure-list">
      {items.map((item) => (
        <li key={item.label}>
          <div className="grc-dash-exposure-row">
            <span className="grc-dash-exposure-label" title={item.label}>
              {item.label}
            </span>
            <span className="grc-dash-exposure-count">{item.count}</span>
          </div>
          <div className="grc-dash-exposure-bar-track">
            <div
              className="grc-dash-exposure-bar-fill"
              style={{ width: `${(item.count / max) * 100}%` }}
            />
            {item.critical_count > 0 && (
              <div
                className="grc-dash-exposure-bar-critical"
                style={{ width: `${(item.critical_count / max) * 100}%` }}
                title={`${item.critical_count} critique(s)`}
              />
            )}
          </div>
        </li>
      ))}
    </ul>
  );
}

export default function ExposurePanel({ title, items }: Props) {
  return (
    <section className="grc-dash-panel grc-dash-panel-compact">
      <header className="grc-dash-panel-header">
        <h2>{title}</h2>
      </header>
      {!items.length ? (
        <p className="grc-dash-empty">Aucune donnée.</p>
      ) : (
        <ExposureBars items={items} />
      )}
    </section>
  );
}
