/**
 * Layout canonique Club Urba — bandes horizontales par couche.
 * Métier → Organisation → Fonctionnel → Applicatif → Technique.
 */

import { COUCHE_ORDER, resolveEntityCouche, type CoucheId } from "./clubUrbaConfig";
import {
  buildDirectCrossLayerRoute,
  buildExteriorRoute,
  EXTERIOR_MARGIN,
  isCrossCoucheEdge,
  shouldUseExteriorRouting,
} from "./exteriorEdgeRouting";
import type { EdgeRoute, EdgeRouteContext } from "./edgeRouteTypes";
import type { UrbanismGraph } from "./metamodel";

export type { EdgeRoute, EdgeRouteContext, GraphBounds } from "./edgeRouteTypes";

export const SLOT_COL_WIDTH = 250;
export const SLOT_ROW_HEIGHT = 100;
export const HORIZONTAL_NODE_OFFSET = 220;
export const BAND_PAD_TOP = 44;
export const BAND_PAD_LEFT = 168;
export const BAND_MIN_HEIGHT = 240;
export const BAND_GAP = 32;
export const NODE_VISUAL_HEIGHT = 72;
export const BAND_BOTTOM_PAD = 24;

/** @deprecated Utilisé uniquement en secours — préférer le routage extérieur. */
export const LEFT_CORRIDOR_X = BAND_PAD_LEFT - 24;

/** Grille canonique : col 0 = gauche, col 1 = centre, col 2 = droite ; row 0 = haut. */
export const CANONICAL_SLOTS: Record<CoucheId, Record<string, { col: number; row: number }>> = {
  metier: {
    metier: { col: 1, row: 0 },
    client: { col: 0, row: 0 },
    objectif: { col: 0, row: 1 },
    processus: { col: 2, row: 1 },
    evenement: { col: 0, row: 2 },
    activite: { col: 2, row: 2 },
    resultat: { col: 1, row: 2 },
    classe: { col: 1, row: 3 },
  },
  organisation: {
    organisation: { col: 1, row: 0 },
    acteur: { col: 0, row: 1 },
    procedure: { col: 1, row: 1 },
    operation: { col: 1, row: 2 },
  },
  fonctionnel: {
    ilot_fonctionnel: { col: 0, row: 1 },
    quartier_fonctionnel: { col: 1, row: 1 },
    zone_fonctionnelle: { col: 2, row: 1 },
  },
  applicatif: {
    ilot_applicatif: { col: 0, row: 1 },
    quartier_applicatif: { col: 1, row: 1 },
    zone_applicative: { col: 2, row: 1 },
  },
  technique: {
    poste_travail: { col: 0, row: 1 },
    byod: { col: 1, row: 1 },
    serveur: { col: 0, row: 2 },
    reseau: { col: 1, row: 2 },
    site: { col: 2, row: 2 },
  },
  transverse: {
    systeme_information: { col: 1, row: 1 },
  },
};

export const BAND_HEIGHT_BY_COUCHE: Record<CoucheId, number> = {
  metier: 380,
  organisation: 300,
  fonctionnel: 220,
  applicatif: 220,
  technique: 300,
  transverse: 200,
};

type GraphNode = UrbanismGraph["nodes"][number];

export function coucheBandIndex(couche: CoucheId): number {
  return COUCHE_ORDER.indexOf(couche);
}

export function computeBandYOffset(
  bandIndex: number,
  bandHeights?: Record<CoucheId, number>,
): number {
  const heights = bandHeights ?? BAND_HEIGHT_BY_COUCHE;
  let y = 0;
  for (let i = 0; i < bandIndex; i++) {
    y += (heights[COUCHE_ORDER[i]] ?? BAND_MIN_HEIGHT) + BAND_GAP;
  }
  return y;
}

function defaultBandHeights(): Record<CoucheId, number> {
  return { ...BAND_HEIGHT_BY_COUCHE };
}

export function getBandHeight(couche: CoucheId): number {
  return BAND_HEIGHT_BY_COUCHE[couche] ?? BAND_MIN_HEIGHT;
}

/** Lignes alignées horizontalement dans la couche métier. */
export const METIER_ALIGNED_ROWS = new Set([1, 2]);

export function computeCanonicalPositions(
  nodes: GraphNode[],
  bandHeights: Record<CoucheId, number> = defaultBandHeights(),
): Map<string, { x: number; y: number }> {
  const byCouche = new Map<CoucheId, GraphNode[]>();

  for (const node of nodes) {
    const c = resolveEntityCouche(node.entity_type, node.couche);
    const list = byCouche.get(c) ?? [];
    list.push({ ...node, couche: c });
    byCouche.set(c, list);
  }

  const positions = new Map<string, { x: number; y: number }>();
  for (const couche of COUCHE_ORDER) {
    const coucheNodes = byCouche.get(couche) ?? [];
    const slots = CANONICAL_SLOTS[couche];
    if (!slots || coucheNodes.length === 0) continue;

    const bandIndex = coucheBandIndex(couche);
    const baseY = computeBandYOffset(bandIndex, bandHeights) + BAND_PAD_TOP;
    const baseX = BAND_PAD_LEFT;

    const byType = new Map<string, GraphNode[]>();
    for (const node of coucheNodes) {
      const list = byType.get(node.entity_type) ?? [];
      list.push(node);
      byType.set(node.entity_type, list);
    }

    for (const [entityType, typedNodes] of byType) {
      const slot = slots[entityType] ?? { col: 1, row: 4 };
      const rowY = baseY + slot.row * SLOT_ROW_HEIGHT;
      const sorted = [...typedNodes].sort((a, b) => a.label.localeCompare(b.label));

      sorted.forEach((node, index) => {
        positions.set(node.id, {
          x: baseX + slot.col * SLOT_COL_WIDTH + index * HORIZONTAL_NODE_OFFSET,
          y: rowY,
        });
      });
    }

    if (couche === "metier") {
      for (const row of METIER_ALIGNED_ROWS) {
        const rowY = baseY + row * SLOT_ROW_HEIGHT;
        for (const node of coucheNodes) {
          const slot = slots[node.entity_type];
          if (!slot || slot.row !== row) continue;
          const pos = positions.get(node.id);
          if (!pos) continue;
          positions.set(node.id, { x: pos.x, y: rowY });
        }
      }
    }
  }

  return positions;
}

export function computeBandHeightsForNodes(nodes: GraphNode[]): Record<CoucheId, number> {
  let heights = defaultBandHeights();
  for (let pass = 0; pass < 5; pass++) {
    const positions = computeCanonicalPositions(nodes, heights);
    let changed = false;
    const next = { ...heights };
    const byCouche = new Map<CoucheId, GraphNode[]>();
    for (const node of nodes) {
      const c = resolveEntityCouche(node.entity_type, node.couche);
      const list = byCouche.get(c) ?? [];
      list.push(node);
      byCouche.set(c, list);
    }
    for (const couche of COUCHE_ORDER) {
      const coucheNodes = byCouche.get(couche) ?? [];
      if (!coucheNodes.length) continue;
      const bandStart = computeBandYOffset(coucheBandIndex(couche), heights);
      let maxBottom = bandStart;
      for (const node of coucheNodes) {
        const pos = positions.get(node.id);
        if (!pos) continue;
        maxBottom = Math.max(maxBottom, pos.y + NODE_VISUAL_HEIGHT);
      }
      const needed = Math.ceil(maxBottom - bandStart + BAND_BOTTOM_PAD);
      if (needed > next[couche]) {
        next[couche] = needed;
        changed = true;
      }
    }
    heights = next;
    if (!changed) break;
  }
  return heights;
}

export function resolveEdgeRoute(
  sourceType: string,
  targetType: string,
  relationType: string,
  context?: EdgeRouteContext,
): EdgeRoute {
  const key = `${sourceType}|${relationType}|${targetType}`;

  const staticRoutes: Record<string, EdgeRoute> = {
    "metier|définit|objectif": {
      sourceHandle: "source-bottom",
      targetHandle: "target-top",
      pathType: "bezier",
      curvature: 0.15,
      labelPosition: 0.48,
      labelOffsetX: -28,
      labelOffsetY: 0,
      ruleId: "R02",
    },
    "metier|pilote|processus": {
      sourceHandle: "source-bottom",
      targetHandle: "target-top",
      pathType: "bezier",
      curvature: 0.5,
      labelPosition: 0.62,
      labelOffsetX: 42,
      labelOffsetY: -8,
      ruleId: "R03",
    },
    "objectif|est pris en compte dans|processus": {
      sourceHandle: "source-right",
      targetHandle: "target-left",
      pathType: "straight",
      curvature: 0,
      labelPosition: 0.5,
      labelOffsetX: 0,
      labelOffsetY: -18,
      ruleId: "R05",
    },
    "evenement|déclenche|processus": {
      sourceHandle: "source-right",
      targetHandle: "target-bottom",
      pathType: "smoothstep",
      curvature: 0,
      labelPosition: 0.5,
      labelOffsetX: 0,
      labelOffsetY: 14,
    },
    "procedure|s'organise en|processus": {
      sourceHandle: "source-left",
      targetHandle: "target-right",
      pathType: "smoothstep",
      curvature: 0,
      labelPosition: 0.5,
      labelOffsetX: 0,
      labelOffsetY: -12,
    },
    "processus|se décompose en|activite": {
      sourceHandle: "source-bottom",
      targetHandle: "target-top",
      pathType: "bezier",
      curvature: 0.2,
      labelPosition: 0.52,
      labelOffsetX: 24,
      labelOffsetY: 0,
    },
    "activite|manipule|classe": {
      sourceHandle: "source-left",
      targetHandle: "target-right",
      pathType: "smoothstep",
      curvature: 0,
      labelPosition: 0.5,
      labelOffsetX: 0,
      labelOffsetY: -14,
    },
    "metier|décide de|organisation": {
      sourceHandle: "source-bottom",
      targetHandle: "target-top",
      pathType: "bezier",
      curvature: 0.12,
      labelPosition: 0.5,
      labelOffsetX: 56,
      labelOffsetY: 0,
      ruleId: "R01",
    },
    "organisation|est déclinée en|procedure": {
      sourceHandle: "source-bottom",
      targetHandle: "target-top",
      pathType: "bezier",
      curvature: 0.15,
      labelPosition: 0.5,
      labelOffsetX: 0,
      labelOffsetY: 0,
    },
    "procedure|se décompose en|operation": {
      sourceHandle: "source-bottom",
      targetHandle: "target-top",
      pathType: "bezier",
      curvature: 0.15,
      labelPosition: 0.5,
      labelOffsetX: 0,
      labelOffsetY: 0,
    },
    "acteur|pilote|procedure": {
      sourceHandle: "source-right",
      targetHandle: "target-left",
      pathType: "smoothstep",
      curvature: 0,
      labelPosition: 0.5,
      labelOffsetX: 0,
      labelOffsetY: -12,
      ruleId: "R31",
    },
    "acteur|réalise|operation": {
      sourceHandle: "source-right",
      targetHandle: "target-left",
      pathType: "smoothstep",
      curvature: 0,
      labelPosition: 0.5,
      labelOffsetX: 0,
      labelOffsetY: -12,
    },
    "operation|produit|resultat": {
      sourceHandle: "source-top",
      targetHandle: "target-bottom",
      pathType: "bezier",
      curvature: 0.2,
      labelPosition: 0.5,
      labelOffsetX: 0,
      labelOffsetY: 0,
    },
    "classe|donne lieu à|ilot_fonctionnel": {
      sourceHandle: "source-bottom",
      targetHandle: "target-top",
      pathType: "bezier",
      curvature: 0.18,
      labelPosition: 0.5,
      labelOffsetX: -48,
      labelOffsetY: 0,
    },
    "ilot_fonctionnel|se regroupe dans|quartier_fonctionnel": {
      sourceHandle: "source-right",
      targetHandle: "target-left",
      pathType: "smoothstep",
      curvature: 0,
      labelPosition: 0.5,
      labelOffsetX: 0,
      labelOffsetY: -12,
    },
    "quartier_fonctionnel|compose|zone_fonctionnelle": {
      sourceHandle: "source-right",
      targetHandle: "target-left",
      pathType: "smoothstep",
      curvature: 0,
      labelPosition: 0.5,
      labelOffsetX: 0,
      labelOffsetY: -12,
    },
    "ilot_fonctionnel|est mis en œuvre par|ilot_applicatif": {
      sourceHandle: "source-bottom",
      targetHandle: "target-top",
      pathType: "bezier",
      curvature: 0.12,
      labelPosition: 0.5,
      labelOffsetX: -36,
      labelOffsetY: 0,
    },
    "ilot_applicatif|compose|quartier_applicatif": {
      sourceHandle: "source-right",
      targetHandle: "target-left",
      pathType: "smoothstep",
      curvature: 0,
      labelPosition: 0.5,
      labelOffsetX: 0,
      labelOffsetY: -12,
    },
    "quartier_applicatif|compose|zone_applicative": {
      sourceHandle: "source-right",
      targetHandle: "target-left",
      pathType: "smoothstep",
      curvature: 0,
      labelPosition: 0.5,
      labelOffsetX: 0,
      labelOffsetY: -12,
    },
    "client|génère|evenement": {
      sourceHandle: "source-bottom",
      targetHandle: "target-top",
      pathType: "bezier",
      curvature: 0.15,
      labelPosition: 0.5,
      labelOffsetX: 0,
      labelOffsetY: 0,
    },
    "resultat|satisfait|client": {
      sourceHandle: "source-left",
      targetHandle: "target-right",
      pathType: "smoothstep",
      curvature: 0,
      labelPosition: 0.5,
      labelOffsetX: 0,
      labelOffsetY: -12,
    },
  };

  const preset = staticRoutes[key];
  if (preset) return preset;

  if (context && isCrossCoucheEdge(sourceType, targetType)) {
    if (shouldUseExteriorRouting(sourceType, targetType)) {
      return buildExteriorRoute(context.sourcePos, context.targetPos, context.bounds, {
        isDerived: context.isDerived,
        laneIndex: context.laneIndex,
      });
    }
    return buildDirectCrossLayerRoute(sourceType, targetType);
  }

  return {
    sourceHandle: "source-right",
    targetHandle: "target-left",
    pathType: "smoothstep",
    curvature: 0.1,
    labelPosition: 0.5,
    labelOffsetX: 0,
    labelOffsetY: -12,
  };
}

export function maxCanonicalWidth(nodes: GraphNode[]): number {
  let maxCol = 2;
  for (const node of nodes) {
    const slots = CANONICAL_SLOTS[resolveEntityCouche(node.entity_type, node.couche)];
    const slot = slots?.[node.entity_type];
    if (slot) maxCol = Math.max(maxCol, slot.col);
  }
  return BAND_PAD_LEFT + (maxCol + 1) * SLOT_COL_WIDTH + 120 + EXTERIOR_MARGIN * 2;
}

export function totalCanvasHeightFromBands(
  visibleCouches: Set<CoucheId>,
  bandHeights?: Record<CoucheId, number>,
): number {
  let h = 0;
  COUCHE_ORDER.forEach((c, i) => {
    if (!visibleCouches.has(c)) return;
    h += (bandHeights?.[c] ?? getBandHeight(c)) + (i < COUCHE_ORDER.length - 1 ? BAND_GAP : 0);
  });
  return h + 40;
}
