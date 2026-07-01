export type RegisterKpiKey = "total" | "critical" | "high" | "moderate" | "low";

interface Props {
  total: number;
  critical: number;
  high: number;
  moderate: number;
  low: number;
  ptrOpen: number | string;
  activeKpi: RegisterKpiKey | null;
  onKpiClick: (key: RegisterKpiKey) => void;
}

const ITEMS: {
  key: RegisterKpiKey | "ptr";
  label: string;
  value: (p: Omit<Props, "activeKpi" | "onKpiClick">) => number | string;
  accent: string;
  clickable: boolean;
}[] = [
  { key: "total", label: "Total risques", value: (p) => p.total, accent: "neutral", clickable: true },
  { key: "critical", label: "Critiques", value: (p) => p.critical, accent: "critical", clickable: true },
  { key: "high", label: "Élevés", value: (p) => p.high, accent: "high", clickable: true },
  { key: "moderate", label: "Modérés", value: (p) => p.moderate, accent: "medium", clickable: true },
  { key: "low", label: "Faibles", value: (p) => p.low, accent: "low", clickable: true },
  { key: "ptr", label: "Actions PTR ouvertes", value: (p) => p.ptrOpen, accent: "ptr", clickable: false },
];

export default function RegisterKpiCards({
  activeKpi,
  onKpiClick,
  ...stats
}: Props) {
  return (
    <div className="grc-dash-kpi-grid grc-register-kpi-grid" role="group" aria-label="Indicateurs cliquables">
      {ITEMS.map(({ key, label, value, accent, clickable }) => {
        const isActive = clickable && activeKpi === key;
        const className = [
          "grc-register-kpi-card",
          `grc-register-kpi-${accent}`,
          isActive ? "grc-register-kpi-active" : "",
        ]
          .filter(Boolean)
          .join(" ");

        const content = (
          <>
            <span className="grc-register-kpi-label">{label}</span>
            <strong className="grc-register-kpi-value">{value(stats)}</strong>
          </>
        );

        if (!clickable) {
          return (
            <article key={key} className={className} aria-disabled="true">
              {content}
            </article>
          );
        }

        return (
          <button
            key={key}
            type="button"
            className={className}
            aria-pressed={isActive}
            onClick={() => onKpiClick(key as RegisterKpiKey)}
          >
            {content}
          </button>
        );
      })}
    </div>
  );
}
