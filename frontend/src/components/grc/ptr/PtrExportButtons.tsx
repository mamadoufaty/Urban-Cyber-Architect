type Props = {
  disabled?: boolean;
  exporting: string | null;
  onExport: (format: "csv" | "xlsx" | "pdf") => void;
};

const FORMATS: { format: "csv" | "xlsx" | "pdf"; label: string }[] = [
  { format: "csv", label: "Exporter CSV" },
  { format: "xlsx", label: "Exporter Excel" },
  { format: "pdf", label: "Exporter PDF" },
];

export default function PtrExportButtons({ disabled, exporting, onExport }: Props) {
  return (
    <div className="ptr-exports">
      {FORMATS.map(({ format, label }) => (
        <button
          key={format}
          type="button"
          className="ptr-btn ptr-btn-export"
          disabled={disabled || !!exporting}
          onClick={() => onExport(format)}
        >
          {exporting === format ? "Export…" : label}
        </button>
      ))}
    </div>
  );
}
