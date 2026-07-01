interface Props {
  title: string;
  layer: string;
}

export default function ModulePlaceholder({ title, layer }: Props) {
  return (
    <>
      <div className="page-header">
        <h2>{title}</h2>
        <p>Module {layer} — enrichissement prévu en V2</p>
      </div>
      <div className="card">
        <p style={{ color: "var(--muted)" }}>
          Ce module sera connecté au Context Builder et au Knowledge Graph projet.
          Les données saisies ici alimenteront les prompts multi-LLM.
        </p>
      </div>
    </>
  );
}
