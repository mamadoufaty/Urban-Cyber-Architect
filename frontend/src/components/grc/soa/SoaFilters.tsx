import type { SoaFilterOptions } from "./types";

type Props = {
  search: string;
  isoReference: string;
  applicable: string;
  implemented: string;
  responsible: string;
  status: string;
  filterOptions: SoaFilterOptions | undefined;
  onSearchChange: (value: string) => void;
  onIsoReferenceChange: (value: string) => void;
  onApplicableChange: (value: string) => void;
  onImplementedChange: (value: string) => void;
  onResponsibleChange: (value: string) => void;
  onStatusChange: (value: string) => void;
  onReset: () => void;
};

export default function SoaFilters({
  search,
  isoReference,
  applicable,
  implemented,
  responsible,
  status,
  filterOptions,
  onSearchChange,
  onIsoReferenceChange,
  onApplicableChange,
  onImplementedChange,
  onResponsibleChange,
  onStatusChange,
  onReset,
}: Props) {
  return (
    <div className="soa-filters">
      <input
        type="search"
        className="soa-field soa-search"
        placeholder="Recherche"
        aria-label="Recherche"
        value={search}
        onChange={(e) => onSearchChange(e.target.value)}
      />
      <select
        className="soa-field"
        aria-label="Référence ISO"
        value={isoReference}
        onChange={(e) => onIsoReferenceChange(e.target.value)}
      >
        <option value="">Référence ISO</option>
        {filterOptions?.iso_references.map((ref) => (
          <option key={ref} value={ref}>
            {ref}
          </option>
        ))}
      </select>
      <select
        className="soa-field"
        aria-label="Applicable"
        value={applicable}
        onChange={(e) => onApplicableChange(e.target.value)}
      >
        <option value="">Applicable</option>
        <option value="Oui">Oui</option>
        <option value="Non">Non</option>
      </select>
      <select
        className="soa-field"
        aria-label="Implémenté"
        value={implemented}
        onChange={(e) => onImplementedChange(e.target.value)}
      >
        <option value="">Implémenté</option>
        <option value="Oui">Oui</option>
        <option value="Non">Non</option>
      </select>
      <select
        className="soa-field"
        aria-label="Responsable"
        value={responsible}
        onChange={(e) => onResponsibleChange(e.target.value)}
      >
        <option value="">Responsable</option>
        {filterOptions?.responsibles.map((r) => (
          <option key={r} value={r}>
            {r}
          </option>
        ))}
      </select>
      <select
        className="soa-field"
        aria-label="Statut"
        value={status}
        onChange={(e) => onStatusChange(e.target.value)}
      >
        <option value="">Statut</option>
        {filterOptions?.statuses.map((s) => (
          <option key={s} value={s}>
            {s}
          </option>
        ))}
      </select>
      <button type="button" className="soa-btn soa-btn-ghost" onClick={onReset}>
        Réinitialiser
      </button>
    </div>
  );
}
