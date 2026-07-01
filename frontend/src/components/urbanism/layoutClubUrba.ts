import type { Edge, Node } from "@xyflow/react";
import { COUCHE_ORDER, COUCHE_COLORS, type CoucheId, type SchemaEdge, type SchemaNode } from "./clubUrbaConfig";
import { CLUB_URBA_DEFINITIONS } from "./clubUrbaZones";
export const BAND_HEIGHT = 200;
export const BAND_GAP = 24;
export const ZONE_WIDTH = 230;
export const NODE_HEIGHT = 72;
export const NODE_GAP = 12;
export const BAND_LABEL_WIDTH = 160;
export const BAND_PADDING_X = 24;

export type UrbanismNodeData = {
  label: string;
  zoneLabel: string;
  couche: CoucheId;
  coucheLabel: string;
  coucheColor: string;
};

export type LayerBandData = {
  label: string;
  color: string;
  width: number;
  height: number;
};

function zoneIndex(couche: CoucheId, zone: string, schemaNodes: SchemaNode[]): number {
  const zones = [...new Set(schemaNodes.filter((n) => n.couche === couche).map((n) => n.zone))];
  return zones.indexOf(zone);
}

export function computeLayout(nodes: SchemaNode[]): { flowNodes: Node[]; width: number } {
  const contentNodes = nodes.filter((n) => n.type === "urbanism");
  const bandNodes: Node[] = [];
  const objectNodes: Node[] = [];

  const maxZones = Math.max(
    ...CLUB_URBA_DEFINITIONS.map((d) => d.zones.length),
    ...COUCHE_ORDER.map((c) => new Set(contentNodes.filter((n) => n.couche === c).map((n) => n.zone)).size),
    1
  );
  const mapWidth = BAND_LABEL_WIDTH + BAND_PADDING_X + maxZones * ZONE_WIDTH + 40;

  COUCHE_ORDER.forEach((coucheId, bandIndex) => {
    const bandY = bandIndex * (BAND_HEIGHT + BAND_GAP);
    const coucheNodes = contentNodes.filter((n) => n.couche === coucheId);
    const def = CLUB_URBA_DEFINITIONS.find((d) => d.id === coucheId);
    const color = coucheNodes[0]?.couche_color ?? def?.color ?? COUCHE_COLORS[coucheId];
    const label = coucheNodes[0]?.couche_label ?? def?.label ?? coucheId;
    bandNodes.push({
      id: `band-${coucheId}`,
      type: "layerBand",
      position: { x: 0, y: bandY },
      data: { label, color, width: mapWidth, height: BAND_HEIGHT } satisfies LayerBandData,
      draggable: false,
      selectable: false,
      focusable: false,
      zIndex: -1,
    });

    const byZone = new Map<string, SchemaNode[]>();
    for (const n of coucheNodes) {
      const list = byZone.get(n.zone) ?? [];
      list.push(n);
      byZone.set(n.zone, list);
    }

    for (const [zone, zoneNodes] of byZone) {
      const zIdx = zoneIndex(coucheId, zone, contentNodes);
      const x = BAND_LABEL_WIDTH + BAND_PADDING_X + zIdx * ZONE_WIDTH;
      const stackHeight = zoneNodes.length * NODE_HEIGHT + (zoneNodes.length - 1) * NODE_GAP;
      const yOffset = bandY + (BAND_HEIGHT - stackHeight) / 2;

      zoneNodes.forEach((n, rowIndex) => {
        objectNodes.push({
          id: n.id,
          type: "urbanism",
          position: { x, y: yOffset + rowIndex * (NODE_HEIGHT + NODE_GAP) },
          data: {
            label: n.label,
            zoneLabel: n.zone_label,
            couche: n.couche,
            coucheLabel: n.couche_label,
            coucheColor: n.couche_color,
          } satisfies UrbanismNodeData,
          zIndex: 1,
        });
      });
    }
  });

  return { flowNodes: [...bandNodes, ...objectNodes], width: mapWidth };
}

export function schemaToFlow(
  apiNodes: SchemaNode[],
  apiEdges: SchemaEdge[],
  visibleCouches: Set<CoucheId>
): { nodes: Node[]; edges: Edge[] } {
  const filtered = apiNodes.filter((n) => visibleCouches.has(n.couche));
  const visibleIds = new Set(filtered.map((n) => n.id));
  const { flowNodes } = computeLayout(filtered);

  const edges: Edge[] = apiEdges
    .filter((e) => visibleIds.has(e.source) && visibleIds.has(e.target))
    .map((e) => ({
      id: e.id,
      source: e.source,
      target: e.target,
      label: e.relation,
      animated: false,
      style: { stroke: "#5a6a82", strokeWidth: 1.5 },
      labelStyle: { fill: "#8896ab", fontSize: 9 },
    }));

  return { nodes: flowNodes, edges };
}

export function autoLayoutFromSchema(
  apiNodes: SchemaNode[],
  visibleCouches: Set<CoucheId>
): Node[] {
  const filtered = apiNodes.filter((n) => visibleCouches.has(n.couche));
  return computeLayout(filtered).flowNodes;
}
