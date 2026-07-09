import { useCallback, useEffect, useMemo, useState } from "react";
import {
  assistantCreate,
  assistantLink,
  getAssistantFormSchema,
  getMetamodel,
  getUrbanismProgress,
  listUrbanismEntities,
} from "../../api";
import type {
  AssistedFormField,
  AssistedFormSchema,
  Metamodel,
  UrbanismAnalysis,
  UrbanismEntity,
  UrbanismProgress,
} from "./metamodel";
import UrbanismAnalysisPanel from "./UrbanismAnalysisPanel";
import UrbanismProgressBar from "./UrbanismProgressBar";

interface Props {
  projectId: string;
  cartographyId?: string;
  readOnly?: boolean;
  onSaved: (analysis?: UrbanismAnalysis) => void;
  liveAnalysis?: UrbanismAnalysis | null;
  hideDeduplicateButton?: boolean;
}

type Tab = "create" | "link";

function bindingsFromSchema(schema: AssistedFormSchema): Record<string, string[]> {
  const bindings: Record<string, string[]> = {};
  for (const field of schema.fields) {
    if (field.selected.length) {
      bindings[field.field_id] = [...field.selected];
    } else {
      bindings[field.field_id] = [];
    }
  }
  return bindings;
}

export default function UrbanismAssistant({
  projectId,
  cartographyId,
  readOnly,
  onSaved,
  liveAnalysis,
  hideDeduplicateButton,
}: Props) {
  const [metamodel, setMetamodel] = useState<Metamodel | null>(null);
  const [entities, setEntities] = useState<UrbanismEntity[]>([]);
  const [progress, setProgress] = useState<UrbanismProgress | null>(null);
  const [tab, setTab] = useState<Tab>("create");
  const [entityType, setEntityType] = useState("metier");
  const [schema, setSchema] = useState<AssistedFormSchema | null>(null);
  const [label, setLabel] = useState("");
  const [bindings, setBindings] = useState<Record<string, string[]>>({});
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [localAnalysis, setLocalAnalysis] = useState<UrbanismAnalysis | null>(null);

  // Link tab state
  const [linkRuleId, setLinkRuleId] = useState("");
  const [linkSourceId, setLinkSourceId] = useState("");
  const [linkTargetId, setLinkTargetId] = useState("");
  const [linkAction, setLinkAction] = useState<"add" | "replace" | "remove">("add");

  const refreshMeta = useCallback(async () => {
    const [mm, ents, prog] = await Promise.all([
      getMetamodel(),
      listUrbanismEntities(projectId, cartographyId),
      getUrbanismProgress(projectId, cartographyId),
    ]);
    setMetamodel(mm);
    setEntities(ents);
    setProgress(prog);
  }, [projectId, cartographyId]);

  const loadSchema = useCallback(async (type: string) => {
    const s = await getAssistantFormSchema(projectId, type, cartographyId);
    setSchema(s);
    setBindings(bindingsFromSchema(s));
  }, [projectId, cartographyId]);

  useEffect(() => {
    refreshMeta().catch((e) => setError(e instanceof Error ? e.message : "Erreur"));
  }, [refreshMeta]);

  useEffect(() => {
    if (tab !== "create") return;
    setError(null);
    loadSchema(entityType).catch((e) => setError(e instanceof Error ? e.message : "Erreur schéma"));
  }, [entityType, tab, loadSchema]);

  const entityTypesOrdered = useMemo(() => {
    if (!metamodel) return [];
    const profiles = metamodel.entity_profiles ?? {};
    return [...metamodel.entity_types].sort((a, b) => {
      const oa = profiles[a.id]?.creation_order ?? 99;
      const ob = profiles[b.id]?.creation_order ?? 99;
      return oa - ob;
    });
  }, [metamodel]);

  const entityTypeLabel = (id: string) =>
    metamodel?.entity_types.find((t) => t.id === id)?.label ?? id;

  const applicableRules = useMemo(() => {
    if (!metamodel || !linkSourceId) return [];
    const source = entities.find((e) => e.id === linkSourceId);
    if (!source) return [];
    return metamodel.relation_rules.filter((r) => r.source === source.entity_type);
  }, [metamodel, linkSourceId, entities]);

  const linkTargetOptions = useMemo(() => {
    if (!linkRuleId || !metamodel) return [];
    const rule = metamodel.relation_rules.find((r) => r.id === linkRuleId);
    if (!rule) return [];
    return entities.filter((e) => e.entity_type === rule.target);
  }, [linkRuleId, metamodel, entities]);

  const setBinding = (field: AssistedFormField, values: string[]) => {
    setBindings((prev) => ({ ...prev, [field.field_id]: values }));
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!label.trim()) return;
    setSaving(true);
    setError(null);
    try {
      const result = await assistantCreate(
        projectId,
        {
          entity_type: entityType,
          label: label.trim(),
          bindings,
        },
        cartographyId
      );
      setLabel("");
      setLocalAnalysis(result.analysis);
      await refreshMeta();
      await loadSchema(entityType);
      onSaved(result.analysis);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erreur création");
    } finally {
      setSaving(false);
    }
  };

  const handleLink = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!linkRuleId || !linkSourceId || !linkTargetId) return;
    setSaving(true);
    setError(null);
    try {
      const result = await assistantLink(
        projectId,
        {
          action: linkAction,
          rule_id: linkRuleId,
          source_id: linkSourceId,
          target_id: linkTargetId,
        },
        cartographyId
      );
      setLocalAnalysis(result.analysis);
      await refreshMeta();
      onSaved(result.analysis);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erreur liaison");
    } finally {
      setSaving(false);
    }
  };

  const analysis = liveAnalysis ?? localAnalysis;

  return (
    <div className="urbanism-assistant">
      <UrbanismProgressBar progress={progress} />

      <div className="card club-urba-editor ua-panel">
        <div className="club-urba-editor-header">
          <h3>Assistant d&apos;urbanisme</h3>
        </div>

        <div className="assistant-tabs" role="tablist" aria-label="Actions assistant">
          <button
            type="button"
            role="tab"
            aria-selected={tab === "create"}
            className={`assistant-tab ${tab === "create" ? "active" : ""}`}
            onClick={() => setTab("create")}
          >
            Créer un objet
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={tab === "link"}
            className={`assistant-tab ${tab === "link" ? "active" : ""}`}
            onClick={() => setTab("link")}
          >
            Lier des objets
          </button>
        </div>

        <p className="club-urba-editor-hint">
          Répondez aux questions — le moteur crée automatiquement les objets et relations Club Urba (R01–R30).
        </p>

        {readOnly && (
          <p className="cartography-readonly-hint">
            Version consultée en lecture seule — restaurez-la pour pouvoir la modifier.
          </p>
        )}

        {error && <div className="project-error" style={{ marginBottom: "0.75rem" }}>{error}</div>}

        {!readOnly && tab === "create" && schema && (
          <form className="entity-create-form" onSubmit={handleCreate}>
            <div className="form-group">
              <label>Type d&apos;objet</label>
              <select value={entityType} onChange={(e) => setEntityType(e.target.value)}>
                {metamodel?.couches.map((c) => (
                  <optgroup key={c.id} label={c.label}>
                    {entityTypesOrdered
                      .filter((t) => t.couche === c.id)
                      .map((t) => (
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
                placeholder={schema.label_field.placeholder}
                required
              />
            </div>

            {schema.hints.map((hint) => (
              <p key={hint} className="assistant-hint">{hint}</p>
            ))}

            {schema.fields.map((field) => (
              <div key={field.field_id} className="form-group">
                <label>
                  {field.label}
                  {field.required && <span className="required-mark"> *</span>}
                  <code className="relation-id-tag">{field.rule_id}</code>
                </label>
                {field.widget === "select" ? (
                  <select
                    value={bindings[field.field_id]?.[0] ?? ""}
                    onChange={(e) => setBinding(field, e.target.value ? [e.target.value] : [])}
                    required={field.required}
                  >
                    <option value="">— Sélectionner —</option>
                    {field.options.map((opt) => (
                      <option key={opt.entity_id} value={opt.entity_id}>{opt.label}</option>
                    ))}
                  </select>
                ) : (
                  <div className="relation-targets">
                    {field.options.map((opt) => (
                      <label key={opt.entity_id} className="relation-checkbox">
                        <input
                          type="checkbox"
                          checked={bindings[field.field_id]?.includes(opt.entity_id) ?? false}
                          onChange={() => {
                            const current = bindings[field.field_id] ?? [];
                            const next = current.includes(opt.entity_id)
                              ? current.filter((id) => id !== opt.entity_id)
                              : [...current, opt.entity_id];
                            setBinding(field, next);
                          }}
                        />
                        {opt.label}
                      </label>
                    ))}
                  </div>
                )}
              </div>
            ))}

            {schema.fields.length === 0 && (
              <p className="zone-item-empty">Aucune dépendance — saisissez le nom et validez.</p>
            )}

            <button type="submit" className="btn btn-primary" disabled={saving}>
              {saving ? "Création…" : "Créer et mettre à jour le graphe"}
            </button>
          </form>
        )}

        {!readOnly && tab === "link" && !metamodel && (
          <p className="zone-item-empty">Chargement du métamodèle…</p>
        )}

        {!readOnly && tab === "link" && metamodel && (
          <form className="entity-create-form" onSubmit={handleLink}>
            <div className="form-group">
              <label>Objet source</label>
              <select
                value={linkSourceId}
                onChange={(e) => {
                  setLinkSourceId(e.target.value);
                  setLinkRuleId("");
                  setLinkTargetId("");
                }}
                required
              >
                <option value="">— Sélectionner —</option>
                {entities.map((ent) => (
                  <option key={ent.id} value={ent.id}>{ent.label} ({ent.entity_type})</option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label>Relation (R01–R30)</label>
              <select
                value={linkRuleId}
                onChange={(e) => {
                  setLinkRuleId(e.target.value);
                  setLinkTargetId("");
                }}
                required
                disabled={!linkSourceId}
              >
                <option value="">— Sélectionner —</option>
                {applicableRules.map((r) => (
                  <option key={r.id} value={r.id}>
                    {r.id} — {entityTypeLabel(r.source)} {r.type} {entityTypeLabel(r.target)}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label>Objet cible</label>
              <select
                value={linkTargetId}
                onChange={(e) => setLinkTargetId(e.target.value)}
                required
                disabled={!linkRuleId}
              >
                <option value="">— Sélectionner —</option>
                {linkTargetOptions.map((ent) => (
                  <option key={ent.id} value={ent.id}>{ent.label}</option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label>Action</label>
              <select value={linkAction} onChange={(e) => setLinkAction(e.target.value as typeof linkAction)}>
                <option value="add">Ajouter</option>
                <option value="replace">Remplacer (même source + type)</option>
                <option value="remove">Supprimer</option>
              </select>
            </div>

            <button type="submit" className="btn btn-primary" disabled={saving || entities.length < 2}>
              {saving ? "Application…" : "Appliquer la liaison"}
            </button>
          </form>
        )}

        <UrbanismAnalysisPanel
          projectId={projectId}
          cartographyId={cartographyId}
          analysis={analysis}
          hideDeduplicateButton={hideDeduplicateButton || readOnly}
          onDeduplicated={(next) => {
            setLocalAnalysis(next);
            onSaved(next);
          }}
        />
      </div>
    </div>
  );
}
