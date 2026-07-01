import type { CoucheId } from "./clubUrbaConfig";

export interface ZoneDef {
  key: string;
  label: string;
}

export interface CoucheDef {
  id: CoucheId;
  label: string;
  color: string;
  zones: ZoneDef[];
}

/** Définition des zones Club Urba — miroir du modèle backend. */
export const CLUB_URBA_DEFINITIONS: CoucheDef[] = [
  {
    id: "metier",
    label: "Couche Métier",
    color: "#00d4aa",
    zones: [
      { key: "objectifs", label: "Objectifs" },
      { key: "processus", label: "Processus" },
      { key: "activites", label: "Activités" },
      { key: "resultats", label: "Résultats" },
    ],
  },
  {
    id: "organisation",
    label: "Couche Organisation",
    color: "#3b82f6",
    zones: [
      { key: "organisation", label: "Organisation" },
      { key: "procedures", label: "Procédures" },
      { key: "operations", label: "Opérations" },
      { key: "acteurs", label: "Acteurs" },
    ],
  },
  {
    id: "fonctionnel",
    label: "Couche Fonctionnelle",
    color: "#8b5cf6",
    zones: [
      { key: "ilots", label: "Îlots fonctionnels" },
      { key: "quartiers", label: "Quartiers fonctionnels" },
      { key: "zones", label: "Zones fonctionnelles" },
    ],
  },
  {
    id: "applicatif",
    label: "Couche Applicative",
    color: "#f59e0b",
    zones: [
      { key: "ilots", label: "Îlots applicatifs" },
      { key: "quartiers", label: "Quartiers applicatifs" },
      { key: "zones", label: "Zones applicatives" },
    ],
  },
  {
    id: "technique",
    label: "Couche Technique",
    color: "#06b6d4",
    zones: [
      { key: "postes", label: "Postes de travail" },
      { key: "serveurs", label: "Serveurs" },
      { key: "reseaux", label: "Réseaux" },
      { key: "sites", label: "Sites" },
    ],
  },
];

export type ClubUrbaData = Record<CoucheId, Record<string, string[]>>;

export function emptyClubUrba(): ClubUrbaData {
  const data = {} as ClubUrbaData;
  for (const couche of CLUB_URBA_DEFINITIONS) {
    data[couche.id] = {};
    for (const zone of couche.zones) {
      data[couche.id][zone.key] = [];
    }
  }
  return data;
}

export function parseClubUrba(urbanism: Record<string, unknown> | undefined): ClubUrbaData {
  const base = emptyClubUrba();
  const club = urbanism?.club_urba;
  if (!club || typeof club !== "object") return base;

  for (const couche of CLUB_URBA_DEFINITIONS) {
    const zones = (club as Record<string, unknown>)[couche.id];
    if (!zones || typeof zones !== "object") continue;
    for (const zone of couche.zones) {
      const items = (zones as Record<string, unknown>)[zone.key];
      if (Array.isArray(items)) {
        base[couche.id][zone.key] = items.map(String).filter((s) => s.trim());
      }
    }
  }
  return base;
}

export function serializeClubUrba(data: ClubUrbaData): Record<string, unknown> {
  return { club_urba: data };
}
