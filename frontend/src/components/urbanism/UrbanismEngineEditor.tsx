import { useCallback, useEffect, useMemo, useState } from "react";
import {
  createUrbanismEntity,
  deleteUrbanismEntity,
  deleteUrbanismRelation,
  getMetamodel,
  listUrbanismEntities,
  listUrbanismRelations,
} from "../../api";
import type { CreationGuideItem, Metamodel, UrbanismEntity, UrbanismRelation } from "./metamodel";

interface Props {
  projectId: string;
  onSaved: () => void;
}

interface RelationDraft {
  relation_type: string;
  target_id?: string;
  source_id?: string;
}

function guideKey(g: CreationGuideItem) {
  return `${g.relation_id}-${g.direction}-${g.peer_type}-${g.relation_type}`;
}

export default function UrbanismEngineEditor({ projectId, onSaved }: Props) {
  const [metamodel, setMetamodel] = useState<Metamodel | null>(null);
  const [entities, setEntities] = useState<UrbanismEntity[]>([]);
  const [relations, setRelations] = useState<UrbanismRelation[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [entityType, setEntityType] = useState("metier");
  const [label, setLabel] = useState("");
  const [selectedRelations, setSelectedRelations] = useState<RelationDraft[]>([]);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [mm, ents, rels] = await Promise.all([
        getMetamodel(),
        listUrbanismEntities(projectId),
        listUrbanismRelations(projectId),
      ]);
      setMetamodel(mm);
      setEntities(ents);
      setRelations(rels);
      if (mm.entity_types.length) setEntityType(mm.entity_types[0].id);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erreur");
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    load();
  }, [load]);

  const creationGuide = useMemo(
    () => metamodel?.creation_guides?.[entityType] ?? [],
    [metamodel, entityType],
  );

  const outgoingGuide = creationGuide.filter((g) => g.direction === "outgoing");
  const incomingGuide = creationGuide.filter((g) => g.direction === "incoming");

  const entityTypeLabel = (id: string) =>
    metamodel?.entity_types.find((t) => t.id === id)?.label ?? id;

  const peersForGuide = (guide: CreationGuideItem) =>
    entities.filter((e) => e.entity_type === guide.peer_type);

  const isGuideChecked = (guide: CreationGuideItem, peerId: string) => {
    if (guide.direction === "outgoing") {
      return selectedRelations.some(
        (r) => r.relation_type === guide.relation_type && r.target_id === peerId,
      );
    }
    return selectedRelations.some(
      (r) => r.relation_type === guide.relation_type && r.source_id === peerId,
    );
  };

  const toggleGuideRelation = (guide: CreationGuideItem, peerId: string) => {
    setSelectedRelations((prev) => {
      const match = (r: RelationDraft) =>
        guide.direction === "outgoing"
          ? r.relation_type === guide.relation_type && r.target_id === peerId
          : r.relation_type === guide.relation_type && r.source_id === peerId;

      if (prev.some(match)) {
        return prev.filter((r) => !match(r));
      }

      const draft: RelationDraft =
        guide.direction === "outgoing"
          ? { relation_type: guide.relation_type, target_id: peerId }
          : { relation_type: guide.relation_type, source_id: peerId };

      return [...prev, draft];
    });
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!label.trim()) return;
    setSaving(true);
    setError(null);
    try {
      await createUrbanismEntity(projectId, {
        entity_type: entityType,
        label: label.trim(),
        relations: selectedRelations,
      });
      setLabel("");
      setSelectedRelations([]);
      setShowForm(false);
      await load();
      onSaved();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erreur création");
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteEntity = async (id: string) => {
    if (!confirm("Supprimer cet objet et ses relations ?")) return;
    await deleteUrbanismEntity(projectId, id);
    await load();
    onSaved();
  };

  const handleDeleteRelation = async (id: string) => {
    await deleteUrbanismRelation(projectId, id);
    await load();
    onSaved();
  };

  const entityLabel = (id: string) => entities.find((e) => e.id === id)?.label ?? id.slice(0, 8);

  const renderGuideBlock = (guide: CreationGuideItem) => {
    const peers = peersForGuide(guide);
    const peerLabel = entityTypeLabel(guide.peer_type);
    const arrow =
      guide.direction === "outgoing"
        ? `→ ${guide.label} → ${peerLabel}`
        : `← ${guide.label} ← ${peerLabel}`;

    return (
      <div key={guideKey(guide)} className="relation-rule-block">
        <span className="relation-rule-label">
          <code className="relation-id-tag">{guide.relation_id}</code> {arrow}
        </span>
        {peers.length === 0 ? (
          <span className="zone-item-empty">
            Aucun(e) {peerLabel} disponible — créez-en un(e) d&apos;abord
          </span>
        ) : (
          <div className="relation-targets">
            {peers.map((t) => (
              <label key={t.id} className="relation-checkbox">
                <input
                  type="checkbox"
                  checked={isGuideChecked(guide, t.id)}
                  onChange={() => toggleGuideRelation(guide, t.id)}
                />
                {t.label}
              </label>
            ))}
          </div>
        )}
      </div>
    );
  };

  if (loading) return <div className="card club-urba-editor ua-panel">Chargement du moteur d&apos;urbanisme…</div>;

  return (
    <div className="card club-urba-editor ua-panel">
      <div className="club-urba-editor-header">
        <h3>Moteur d&apos;urbanisme</h3>
        <button type="button" className="btn btn-primary btn-sm" onClick={() => setShowForm(!showForm)}>
          {showForm ? "Fermer" : "+ Objet"}
        </button>
      </div>
      <p className="club-urba-editor-hint">
        Le moteur vous guide selon le métamodèle Club Urba (R01–R30). Choisissez un type d&apos;objet :
        seules les relations conformes au schéma sont proposées.
      </p>

      {error && <div className="project-error" style={{ marginBottom: "0.75rem" }}>{error}</div>}

      {showForm && metamodel && (
        <form className="entity-create-form" onSubmit={handleCreate}>
          <div className="form-group">
            <label>Type d&apos;objet</label>
            <select
              value={entityType}
              onChange={(e) => {
                setEntityType(e.target.value);
                setSelectedRelations([]);
              }}
            >
              {metamodel.couches.map((c) => (
                <optgroup key={c.id} label={c.label}>
                  {metamodel.entity_types.filter((t) => t.couche === c.id).map((t) => (
                    <option key={t.id} value={t.id}>{t.label}</option>
                  ))}
                </optgroup>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label>Nom</label>
            <input
              value={label}
              onChange={(e) => setLabel(e.target.value)}
              placeholder="Ex. Supervision du métro"
              required
            />
          </div>

          {creationGuide.length === 0 ? (
            <p className="zone-item-empty creation-guide-empty">
              Aucune relation requise à la création — cet objet peut exister seul (ex. Métier).
            </p>
          ) : (
            <div className="form-group">
              <label>Relations suggérées (métamodèle Club Urba)</label>
              {incomingGuide.length > 0 && (
                <div className="relation-guide-section">
                  <h5 className="relation-guide-heading">Dépendances entrantes</h5>
                  {incomingGuide.map(renderGuideBlock)}
                </div>
              )}
              {outgoingGuide.length > 0 && (
                <div className="relation-guide-section">
                  <h5 className="relation-guide-heading">Dépendances sortantes</h5>
                  {outgoingGuide.map(renderGuideBlock)}
                </div>
              )}
            </div>
          )}

          <button type="submit" className="btn btn-primary" disabled={saving}>
            {saving ? "Création…" : "Créer l'objet"}
          </button>
        </form>
      )}

      <div className="entity-list">
        {entities.length === 0 && (
          <p className="zone-item-empty">Aucun objet — commencez par créer un Métier.</p>
        )}
        {metamodel?.couches.map((couche) => {
          const coucheEntities = entities.filter((e) => e.couche === couche.id);
          if (!coucheEntities.length) return null;
          return (
            <div key={couche.id} className="entity-couche-group">
              <h4 style={{ color: couche.color }}>{couche.label}</h4>
              {coucheEntities.map((ent) => {
                const entRels = relations.filter((r) => r.source_id === ent.id || r.target_id === ent.id);
                return (
                  <div key={ent.id} className="entity-card">
                    <div className="entity-card-header">
                      <strong>{ent.label}</strong>
                      <span className="entity-type-tag">{ent.entity_type}</span>
                      <button type="button" className="btn btn-danger btn-sm" onClick={() => handleDeleteEntity(ent.id)}>
                        ×
                      </button>
                    </div>
                    {entRels.length > 0 && (
                      <ul className="entity-relations-list">
                        {entRels.map((r) => (
                          <li key={r.id}>
                            {r.source_id === ent.id ? (
                              <span>→ <em>{r.relation_type}</em> → {entityLabel(r.target_id)}</span>
                            ) : (
                              <span>← <em>{r.relation_type}</em> ← {entityLabel(r.source_id)}</span>
                            )}
                            {r.criticite && <span className="crit-tag">{r.criticite}</span>}
                            <button type="button" className="btn btn-secondary btn-sm" onClick={() => handleDeleteRelation(r.id)}>×</button>
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                );
              })}
            </div>
          );
        })}
      </div>
    </div>
  );
}
