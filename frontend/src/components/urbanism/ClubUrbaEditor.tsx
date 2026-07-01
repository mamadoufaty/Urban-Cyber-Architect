import { useCallback, useEffect, useState } from "react";
import { getProject, updateProject } from "../../api";
import {
  CLUB_URBA_DEFINITIONS,
  type ClubUrbaData,
  emptyClubUrba,
  parseClubUrba,
  serializeClubUrba,
} from "./clubUrbaZones";

interface Props {
  projectId: string;
  onSaved: () => void;
}

function ZoneEditor({
  coucheId,
  zoneKey,
  zoneLabel,
  color,
  items,
  onChange,
  disabled,
}: {
  coucheId: string;
  zoneKey: string;
  zoneLabel: string;
  color: string;
  items: string[];
  onChange: (items: string[]) => void;
  disabled: boolean;
}) {
  const [draft, setDraft] = useState("");
  const [editingIndex, setEditingIndex] = useState<number | null>(null);
  const [editValue, setEditValue] = useState("");

  const addItem = () => {
    const label = draft.trim();
    if (!label) return;
    onChange([...items, label]);
    setDraft("");
  };

  const removeItem = (index: number) => {
    onChange(items.filter((_, i) => i !== index));
  };

  const startEdit = (index: number) => {
    setEditingIndex(index);
    setEditValue(items[index]);
  };

  const saveEdit = () => {
    if (editingIndex === null) return;
    const label = editValue.trim();
    if (!label) {
      removeItem(editingIndex);
    } else {
      const next = [...items];
      next[editingIndex] = label;
      onChange(next);
    }
    setEditingIndex(null);
    setEditValue("");
  };

  return (
    <div className="zone-editor" style={{ borderLeftColor: color }}>
      <div className="zone-editor-header">
        <span className="zone-editor-title" style={{ color }}>
          {zoneLabel}
        </span>
        <span className="zone-editor-count">{items.length}</span>
      </div>

      <div className="zone-editor-add">
        <input
          type="text"
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), addItem())}
          placeholder={`Ajouter — ${zoneLabel.toLowerCase()}`}
          disabled={disabled}
        />
        <button type="button" className="btn btn-primary btn-sm" onClick={addItem} disabled={disabled || !draft.trim()}>
          +
        </button>
      </div>

      <ul className="zone-item-list">
        {items.length === 0 && (
          <li className="zone-item-empty">Aucun élément — saisissez votre premier objet.</li>
        )}
        {items.map((item, index) => (
          <li key={`${coucheId}-${zoneKey}-${index}`} className="zone-item">
            {editingIndex === index ? (
              <>
                <input
                  className="zone-item-edit-input"
                  value={editValue}
                  onChange={(e) => setEditValue(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") saveEdit();
                    if (e.key === "Escape") setEditingIndex(null);
                  }}
                  autoFocus
                />
                <button type="button" className="btn btn-primary btn-sm" onClick={saveEdit}>
                  OK
                </button>
              </>
            ) : (
              <>
                <span className="zone-item-label">{item}</span>
                <div className="zone-item-actions">
                  <button type="button" className="btn btn-secondary btn-sm" onClick={() => startEdit(index)} disabled={disabled}>
                    Modifier
                  </button>
                  <button type="button" className="btn btn-danger btn-sm" onClick={() => removeItem(index)} disabled={disabled}>
                    Supprimer
                  </button>
                </div>
              </>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}

export default function ClubUrbaEditor({ projectId, onSaved }: Props) {
  const [data, setData] = useState<ClubUrbaData>(emptyClubUrba);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [openCouche, setOpenCouche] = useState<string | null>("metier");

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const project = await getProject(projectId);
      setData(parseClubUrba(project.urbanism));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erreur chargement");
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    load();
  }, [load]);

  const persistZone = async (coucheId: keyof ClubUrbaData, zoneKey: string, items: string[]) => {
    const next: ClubUrbaData = {
      ...data,
      [coucheId]: { ...data[coucheId], [zoneKey]: items },
    };
    setData(next);
    setSaving(true);
    setError(null);
    try {
      await updateProject(projectId, { urbanism: serializeClubUrba(next) });
      onSaved();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erreur enregistrement");
      await load();
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <div className="card club-urba-editor">Chargement de l'éditeur…</div>;
  }

  return (
    <div className="card club-urba-editor">
      <div className="club-urba-editor-header">
        <h3>Saisie Club Urba</h3>
        {saving && <span className="status-badge">Enregistrement…</span>}
      </div>
      <p className="club-urba-editor-hint">
        Construisez votre cartographie couche par couche. Chaque ajout ou modification met à jour le schéma en direct.
      </p>

      {error && <div className="project-error" style={{ marginBottom: "0.75rem" }}>{error}</div>}

      {CLUB_URBA_DEFINITIONS.map((couche) => (
        <div key={couche.id} className="couche-accordion">
          <button
            type="button"
            className="couche-accordion-trigger"
            style={{ borderColor: `${couche.color}44` }}
            onClick={() => setOpenCouche(openCouche === couche.id ? null : couche.id)}
          >
            <span style={{ color: couche.color }}>{couche.label}</span>
            <span className="couche-accordion-meta">
              {couche.zones.reduce((n, z) => n + (data[couche.id][z.key]?.length ?? 0), 0)} objets
            </span>
          </button>
          {openCouche === couche.id && (
            <div className="couche-accordion-body">
              {couche.zones.map((zone) => (
                <ZoneEditor
                  key={`${couche.id}-${zone.key}`}
                  coucheId={couche.id}
                  zoneKey={zone.key}
                  zoneLabel={zone.label}
                  color={couche.color}
                  items={data[couche.id][zone.key] ?? []}
                  onChange={(items) => persistZone(couche.id, zone.key, items)}
                  disabled={saving}
                />
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
