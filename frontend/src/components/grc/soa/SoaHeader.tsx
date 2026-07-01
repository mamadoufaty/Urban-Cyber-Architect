import type { SoaSummary } from "./types";

type Props = {
  summary: SoaSummary | null;
  projectName: string;
};

function formatDate(iso: string | undefined): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleString("fr-FR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function SoaHeader({ summary, projectName }: Props) {
  return (
    <header className="soa-header">
      <h1>Déclaration d&apos;applicabilité</h1>
      <dl className="soa-header-meta">
        <div className="soa-header-meta-row">
          <dt>Version SoA</dt>
          <dd>{summary?.soa_version ?? "ISO/IEC 27001:2022"}</dd>
        </div>
        <div className="soa-header-meta-row">
          <dt>Projet</dt>
          <dd>{projectName}</dd>
        </div>
        <div className="soa-header-meta-row">
          <dt>Date génération</dt>
          <dd>
            <time dateTime={summary?.generated_at}>{formatDate(summary?.generated_at)}</time>
          </dd>
        </div>
      </dl>
      <p className="soa-readonly-banner">
        Document généré automatiquement depuis EBIOS RM — Atelier 5. Lecture seule.
      </p>
    </header>
  );
}
