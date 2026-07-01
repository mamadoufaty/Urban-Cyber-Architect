export const COUCHE_ORDER = ["metier", "organisation", "fonctionnel", "applicatif", "technique", "transverse"] as const;

export type CoucheId = (typeof COUCHE_ORDER)[number];

export const COUCHE_COLORS: Record<CoucheId, string> = {
  metier: "#00d4aa",
  organisation: "#3b82f6",
  fonctionnel: "#8b5cf6",
  applicatif: "#f59e0b",
  technique: "#06b6d4",
  transverse: "#64748b",
};

/** Couche canonique par type d'entité (filet de sécurité si couche API incorrecte). */
export const ENTITY_COUCHE_BY_TYPE: Record<string, CoucheId> = {
  metier: "metier",
  objectif: "metier",
  processus: "metier",
  activite: "metier",
  classe: "metier",
  resultat: "metier",
  client: "metier",
  evenement: "metier",
  organisation: "organisation",
  procedure: "organisation",
  operation: "organisation",
  acteur: "organisation",
  ilot_fonctionnel: "fonctionnel",
  quartier_fonctionnel: "fonctionnel",
  zone_fonctionnelle: "fonctionnel",
  ilot_applicatif: "applicatif",
  quartier_applicatif: "applicatif",
  zone_applicative: "applicatif",
  poste_travail: "technique",
  byod: "technique",
  serveur: "technique",
  reseau: "technique",
  site: "technique",
  systeme_information: "transverse",
};

export function resolveEntityCouche(entityType: string, couche?: string): CoucheId {
  const fromType = ENTITY_COUCHE_BY_TYPE[entityType];
  if (fromType) return fromType;
  if (couche && (COUCHE_ORDER as readonly string[]).includes(couche)) {
    return couche as CoucheId;
  }
  return "metier";
}

export interface SchemaNode {
  id: string;
  type: string;
  couche: CoucheId;
  couche_label: string;
  couche_color: string;
  zone: string;
  zone_label: string;
  label: string;
}

export interface SchemaEdge {
  id: string;
  source: string;
  target: string;
  relation: string;
  couche: string;
}

export interface MetaLayer {
  id: CoucheId;
  label: string;
  color: string;
  object_count: number;
  zones: Array<{ key: string; label: string; count: number }>;
}

export interface ClubUrbaSchema {
  project_id: string;
  project_name: string;
  organization: Record<string, string>;
  author: string;
  generated_at: string;
  model: string;
  nodes: SchemaNode[];
  edges: SchemaEdge[];
  meta_layers: MetaLayer[];
  stats: {
    total_objects: number;
    total_relations: number;
    by_couche: Record<string, number>;
  };
}
