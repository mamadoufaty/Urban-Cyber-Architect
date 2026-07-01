import type { PtrSummary } from "./types";

type Props = {
  summary: PtrSummary | null;
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

export default function PtrHeader({ summary, projectName }: Props) {
  return (
    <header className="ptr-header">
      <h1>Plan de traitement des risques</h1>
      <dl className="ptr-header-meta">
        <div className="ptr-header-meta-row">
          <dt>Projet</dt>
          <dd>{projectName}</dd>
        </div>
        <div className="ptr-header-meta-row">
          <dt>Généré le</dt>
          <dd>
            <time dateTime={summary?.generated_at}>{formatDate(summary?.generated_at)}</time>
          </dd>
        </div>
      </dl>
      <p className="ptr-banner">
        Pilotage PTR — alimenté par EBIOS RM Atelier 5. Édition limitée des actions de traitement.
      </p>
    </header>
  );
}
