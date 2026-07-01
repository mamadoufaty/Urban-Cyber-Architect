import type { Node } from "@xyflow/react";
import { NODE_H, NODE_W } from "./exteriorEdgeRouting";
import type { CoucheId } from "./clubUrbaConfig";
import { toManualNodeLayout, type NodeLayoutOverride } from "./nodeLayoutTypes";
import type { UrbanismNodeData } from "./layoutGraph";

export type BandRect = { x: number; y: number; width: number; height: number };

export function urbanismObjectNodes(nodes: Node[]): Node[] {
  return nodes.filter((n) => n.type === "urbanism");
}

export function bandRectsFromNodes(nodes: Node[]): Map<CoucheId, BandRect> {
  const map = new Map<CoucheId, BandRect>();
  for (const n of nodes) {
    if (n.type !== "layerBand" || !n.id.startsWith("band-")) continue;
    const couche = n.id.replace("band-", "") as CoucheId;
    map.set(couche, {
      x: n.position.x,
      y: n.position.y,
      width: (n.data as { width: number }).width,
      height: (n.data as { height: number }).height,
    });
  }
  return map;
}

function withPosition(node: Node, x: number, y: number): Node {
  const data = node.data as UrbanismNodeData;
  return {
    ...node,
    position: { x, y },
    data: { ...data, layoutMode: "manual", layoutLocked: true },
  };
}

export function alignNodesHorizontally(selected: Node[]): Node[] {
  if (selected.length < 2) return selected;
  const y = selected.reduce((s, n) => s + n.position.y, 0) / selected.length;
  return selected.map((n) => withPosition(n, n.position.x, y));
}

export function alignNodesVertically(selected: Node[]): Node[] {
  if (selected.length < 2) return selected;
  const x = selected.reduce((s, n) => s + n.position.x, 0) / selected.length;
  return selected.map((n) => withPosition(n, x, n.position.y));
}

export function distributeNodesHorizontally(selected: Node[]): Node[] {
  if (selected.length < 3) return selected;
  const sorted = [...selected].sort((a, b) => a.position.x - b.position.x);
  const first = sorted[0].position.x;
  const last = sorted[sorted.length - 1].position.x;
  const step = (last - first) / (sorted.length - 1);
  return sorted.map((n, i) => withPosition(n, first + step * i, n.position.y));
}

export function distributeNodesVertically(selected: Node[]): Node[] {
  if (selected.length < 3) return selected;
  const sorted = [...selected].sort((a, b) => a.position.y - b.position.y);
  const first = sorted[0].position.y;
  const last = sorted[sorted.length - 1].position.y;
  const step = (last - first) / (sorted.length - 1);
  return sorted.map((n, i) => withPosition(n, n.position.x, first + step * i));
}

export function centerNodeInBand(node: Node, band: BandRect): Node {
  const x = band.x + (band.width - NODE_W) / 2;
  const y = band.y + (band.height - NODE_H) / 2;
  return withPosition(node, x, y);
}

export function layoutsFromNodes(nodes: Node[]): Array<{ entity_id: string; layout: NodeLayoutOverride }> {
  return urbanismObjectNodes(nodes).map((n) => ({
    entity_id: n.id,
    layout: toManualNodeLayout(n.position.x, n.position.y),
  }));
}
