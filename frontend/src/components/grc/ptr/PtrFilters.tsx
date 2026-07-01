import type { PtrFilterOptions } from "./types";

type Props = {
  search: string;
  responsible: string;
  organization: string;
  priority: string;
  status: string;
  treatmentDecision: string;
  dueFilter: string;
  filterOptions: PtrFilterOptions | undefined;
  onSearchChange: (value: string) => void;
  onResponsibleChange: (value: string) => void;
  onOrganizationChange: (value: string) => void;
  onPriorityChange: (value: string) => void;
  onStatusChange: (value: string) => void;
  onTreatmentDecisionChange: (value: string) => void;
  onDueFilterChange: (value: string) => void;
  onReset: () => void;
};

export default function PtrFilters({
  search,
  responsible,
  organization,
  priority,
  status,
  treatmentDecision,
  dueFilter,
  filterOptions,
  onSearchChange,
  onResponsibleChange,
  onOrganizationChange,
  onPriorityChange,
  onStatusChange,
  onTreatmentDecisionChange,
  onDueFilterChange,
  onReset,
}: Props) {
  return (
    <div className="ptr-filters">
      <input
        type="search"
        className="ptr-field ptr-search"
        placeholder="Recherche"
        aria-label="Recherche"
        value={search}
        onChange={(e) => onSearchChange(e.target.value)}
      />
      <select
        className="ptr-field"
        aria-label="Responsable"
        value={responsible}
        onChange={(e) => onResponsibleChange(e.target.value)}
      >
        <option value="">Responsable</option>
        {filterOptions?.responsibles.map((r) => (
          <option key={r} value={r}>{r}</option>
        ))}
      </select>
      <select
        className="ptr-field"
        aria-label="Organisation"
        value={organization}
        onChange={(e) => onOrganizationChange(e.target.value)}
      >
        <option value="">Organisation</option>
        {filterOptions?.organizations.map((o) => (
          <option key={o} value={o}>{o}</option>
        ))}
      </select>
      <select
        className="ptr-field"
        aria-label="Priorité"
        value={priority}
        onChange={(e) => onPriorityChange(e.target.value)}
      >
        <option value="">Priorité</option>
        {filterOptions?.priorities.map((p) => (
          <option key={p} value={p}>{p}</option>
        ))}
      </select>
      <select
        className="ptr-field"
        aria-label="Statut"
        value={status}
        onChange={(e) => onStatusChange(e.target.value)}
      >
        <option value="">Statut</option>
        {filterOptions?.statuses.map((s) => (
          <option key={s} value={s}>{s}</option>
        ))}
      </select>
      <select
        className="ptr-field"
        aria-label="Décision"
        value={treatmentDecision}
        onChange={(e) => onTreatmentDecisionChange(e.target.value)}
      >
        <option value="">Décision</option>
        {filterOptions?.treatment_decisions.map((d) => (
          <option key={d} value={d}>{d}</option>
        ))}
      </select>
      <select
        className="ptr-field"
        aria-label="Échéance"
        value={dueFilter}
        onChange={(e) => onDueFilterChange(e.target.value)}
      >
        <option value="">Échéance</option>
        <option value="overdue">En retard</option>
        <option value="due_soon">Échéance proche</option>
        <option value="this_week">Cette semaine</option>
        <option value="this_month">Ce mois</option>
      </select>
      <button type="button" className="ptr-btn ptr-btn-ghost" onClick={onReset}>
        Réinitialiser
      </button>
    </div>
  );
}
