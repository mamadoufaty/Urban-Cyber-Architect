import { useEffect, useRef, useState } from "react";
import type { Cartography, CartographyVersion, Project } from "../../api";
import { cartographyStatusLabel, formatVersionLabel, sortCartographies } from "./cartographySelect";

type CartographyBannerProps = {
  projects: Project[];
  selectedProjectId: string;
  onProjectChange: (id: string) => void;

  cartographies: Cartography[];
  selectedCartographyId: string | null;
  onCartographyChange: (id: string) => void;

  versions: CartographyVersion[];
  selectedVersionId: string | null;
  onVersionChange: (id: string) => void;

  currentCartography: Cartography | null;
  isHistoricalVersion: boolean;
  canManage: boolean;
  busy?: boolean;

  onNewCartography: () => void;
  onSaveAs: () => void;
  onDuplicate: () => void;
  onNewVersion: () => void;
  onOpenHistory: () => void;
  onSubmitForValidation: () => void;
  onValidate: () => void;
  onArchiveToggle: () => void;
};

export default function CartographyBanner({
  projects,
  selectedProjectId,
  onProjectChange,
  cartographies,
  selectedCartographyId,
  onCartographyChange,
  versions,
  selectedVersionId,
  onVersionChange,
  currentCartography,
  isHistoricalVersion,
  canManage,
  busy,
  onNewCartography,
  onSaveAs,
  onDuplicate,
  onNewVersion,
  onOpenHistory,
  onSubmitForValidation,
  onValidate,
  onArchiveToggle,
}: CartographyBannerProps) {
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!menuOpen) return;
    function onPointerDown(e: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) setMenuOpen(false);
    }
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") setMenuOpen(false);
    }
    document.addEventListener("mousedown", onPointerDown);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onPointerDown);
      document.removeEventListener("keydown", onKey);
    };
  }, [menuOpen]);

  const sortedCartographies = sortCartographies(cartographies);
  const status = currentCartography?.status;

  function runAction(action: () => void) {
    setMenuOpen(false);
    action();
  }

  return (
    <div className="cartography-banner" data-testid="cartography-banner">
      <label className="cartography-banner-field">
        <span className="cartography-banner-label">Projet</span>
        <select
          className="ua-select"
          value={selectedProjectId}
          onChange={(e) => onProjectChange(e.target.value)}
        >
          {projects.map((p) => (
            <option key={p.id} value={p.id}>
              {p.name}
            </option>
          ))}
        </select>
      </label>

      <label className="cartography-banner-field">
        <span className="cartography-banner-label">Cartographie</span>
        <select
          className="ua-select"
          value={selectedCartographyId ?? ""}
          onChange={(e) => onCartographyChange(e.target.value)}
          disabled={!sortedCartographies.length}
        >
          {sortedCartographies.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
              {c.is_archived ? " (archivée)" : ""}
            </option>
          ))}
        </select>
      </label>

      <label className="cartography-banner-field">
        <span className="cartography-banner-label">Version</span>
        <select
          className="ua-select"
          value={selectedVersionId ?? ""}
          onChange={(e) => onVersionChange(e.target.value)}
          disabled={!versions.length}
        >
          {versions.map((v) => (
            <option key={v.id} value={v.id}>
              {formatVersionLabel(v)} — {cartographyStatusLabel(v.status)}
              {v.is_current ? "" : " (historique)"}
            </option>
          ))}
        </select>
      </label>

      {status && (
        <span className={`cartography-status-badge cartography-status-${status}`}>
          {cartographyStatusLabel(status)}
        </span>
      )}

      {isHistoricalVersion && (
        <span className="cartography-status-badge cartography-status-readonly">
          Lecture seule — version archivée du fil
        </span>
      )}

      <button type="button" className="ua-btn ua-btn-primary" onClick={onNewCartography} disabled={busy}>
        + Nouvelle cartographie
      </button>

      {canManage && currentCartography && (
        <div className="cartography-actions-menu" ref={menuRef}>
          <button
            type="button"
            className="ua-btn"
            onClick={() => setMenuOpen((o) => !o)}
            aria-haspopup="menu"
            aria-expanded={menuOpen}
            disabled={busy}
          >
            Actions ▾
          </button>
          {menuOpen && (
            <div className="cartography-actions-popup" role="menu">
              <button type="button" role="menuitem" onClick={() => runAction(onOpenHistory)}>
                Historique
              </button>
              <button type="button" role="menuitem" onClick={() => runAction(onSaveAs)}>
                Enregistrer sous…
              </button>
              <button type="button" role="menuitem" onClick={() => runAction(onNewVersion)}>
                Créer une nouvelle version
              </button>
              <button type="button" role="menuitem" onClick={() => runAction(onDuplicate)}>
                Dupliquer la cartographie
              </button>
              <div className="cartography-actions-sep" />
              {status === "draft" && (
                <button type="button" role="menuitem" onClick={() => runAction(onSubmitForValidation)}>
                  Soumettre pour validation
                </button>
              )}
              {(status === "in_validation" || status === "draft") && (
                <button type="button" role="menuitem" onClick={() => runAction(onValidate)}>
                  Valider cette version
                </button>
              )}
              <button type="button" role="menuitem" onClick={() => runAction(onArchiveToggle)}>
                {currentCartography.is_archived ? "Désarchiver" : "Archiver"}
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
