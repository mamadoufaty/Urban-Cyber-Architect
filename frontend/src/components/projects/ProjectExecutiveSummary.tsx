type Props = {
  summary: string;
};

export default function ProjectExecutiveSummary({ summary }: Props) {
  return (
    <div className="card project-executive-summary">
      <h4>Synthèse exécutive</h4>
      <p>{summary}</p>
    </div>
  );
}
