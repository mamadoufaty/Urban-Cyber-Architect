import { useEffect, useMemo, useRef, useState } from "react";
import type { AdminOrganization } from "../../api";
import { filterOrganizations, organizationLabelById } from "../../projects/organizationSelect";

type OrganizationComboboxProps = {
  id?: string;
  organizations: AdminOrganization[];
  value: string;
  onChange: (organizationId: string) => void;
  onCreateNew?: () => void;
  disabled?: boolean;
  allowClear?: boolean;
};

export default function OrganizationCombobox({
  id,
  organizations,
  value,
  onChange,
  onCreateNew,
  disabled,
  allowClear = true,
}: OrganizationComboboxProps) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const containerRef = useRef<HTMLDivElement | null>(null);
  const inputRef = useRef<HTMLInputElement | null>(null);

  const selectedLabel = organizationLabelById(organizations, value);
  const results = useMemo(
    () => filterOrganizations(organizations, query),
    [organizations, query],
  );
  const hasOrganizations = organizations.length > 0;

  useEffect(() => {
    if (!open) return;
    setQuery("");
    const timer = window.setTimeout(() => inputRef.current?.focus(), 0);
    return () => window.clearTimeout(timer);
  }, [open]);

  useEffect(() => {
    if (!open) return;
    function onPointerDown(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") setOpen(false);
    }
    document.addEventListener("mousedown", onPointerDown);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onPointerDown);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  function select(organizationId: string) {
    onChange(organizationId);
    setOpen(false);
  }

  return (
    <div className="uca-combobox" ref={containerRef}>
      <button
        type="button"
        id={id}
        className={`uca-combobox-control${selectedLabel ? "" : " is-placeholder"}`}
        disabled={disabled}
        aria-haspopup="listbox"
        aria-expanded={open}
        onClick={() => !disabled && setOpen((o) => !o)}
      >
        <span className="uca-combobox-value">
          {selectedLabel || "— Sélectionner une organisation —"}
        </span>
        <span className="uca-combobox-caret" aria-hidden="true">
          ▾
        </span>
      </button>

      {open && !disabled && (
        <div className="uca-combobox-popup" role="dialog" aria-label="Sélection d'organisation">
          <input
            ref={inputRef}
            type="text"
            className="uca-combobox-search"
            placeholder="Rechercher une organisation…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            aria-label="Rechercher une organisation"
          />

          <ul className="uca-combobox-list" role="listbox">
            {allowClear && (
              <li>
                <button
                  type="button"
                  className={`uca-combobox-option${value === "" ? " is-selected" : ""}`}
                  role="option"
                  aria-selected={value === ""}
                  onClick={() => select("")}
                >
                  — Non renseigné —
                </button>
              </li>
            )}
            {!hasOrganizations ? (
              <li className="uca-combobox-empty">
                Aucune organisation active. Créez-en une pour continuer.
              </li>
            ) : results.length === 0 ? (
              <li className="uca-combobox-empty">Aucun résultat pour « {query} ».</li>
            ) : (
              results.map((org) => (
                <li key={org.id}>
                  <button
                    type="button"
                    className={`uca-combobox-option${org.id === value ? " is-selected" : ""}`}
                    role="option"
                    aria-selected={org.id === value}
                    onClick={() => select(org.id)}
                  >
                    <span>{org.name}</span>
                    <span className="uca-combobox-option-code">{org.code}</span>
                  </button>
                </li>
              ))
            )}
          </ul>

          {onCreateNew && (
            <button
              type="button"
              className="uca-combobox-create"
              onClick={() => {
                setOpen(false);
                onCreateNew();
              }}
            >
              + Créer une organisation
            </button>
          )}
        </div>
      )}
    </div>
  );
}
