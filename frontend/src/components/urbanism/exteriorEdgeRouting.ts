/** Routage extérieur — relations inter-couches longues uniquement. */

import type { EdgeRoute, GraphBounds } from "./edgeRouteTypes";
import { COUCHE_ORDER, ENTITY_COUCHE_BY_TYPE } from "./clubUrbaConfig";

export const NODE_W = 200;
export const NODE_H = 72;
export const EXTERIOR_MARGIN = 88;
export const CORRIDOR_LANE_STEP = 18;

export type Point = { x: number; y: number };

export type { GraphBounds } from "./edgeRouteTypes";

export function computeGraphBounds(
  nodes: Array<{ position: { x: number; y: number } }>
): GraphBounds {
  let xMin = Infinity;
  let xMax = -Infinity;
  let yMin = Infinity;
  let yMax = -Infinity;
  for (const n of nodes) {
    xMin = Math.min(xMin, n.position.x);
    xMax = Math.max(xMax, n.position.x + NODE_W);
    yMin = Math.min(yMin, n.position.y);
    yMax = Math.max(yMax, n.position.y + NODE_H);
  }
  if (!Number.isFinite(xMin)) {
    return { xMin: 0, xMax: 800, yMin: 0, yMax: 600 };
  }
  return { xMin, xMax, yMin, yMax };
}

export function isCrossCoucheEdge(sourceType: string, targetType: string): boolean {
  const sc = ENTITY_COUCHE_BY_TYPE[sourceType];
  const tc = ENTITY_COUCHE_BY_TYPE[targetType];
  return Boolean(sc && tc && sc !== tc);
}

/** Nombre de couches traversées entre source et cible (1 = adjacentes). */
export function coucheLayerGap(sourceType: string, targetType: string): number {
  const sc = ENTITY_COUCHE_BY_TYPE[sourceType];
  const tc = ENTITY_COUCHE_BY_TYPE[targetType];
  if (!sc || !tc) return 0;
  return Math.abs(COUCHE_ORDER.indexOf(sc) - COUCHE_ORDER.indexOf(tc));
}

/** Route courte verticale entre couches voisines ou proches (≤ 2 sauts). */
export function buildDirectCrossLayerRoute(
  sourceType: string,
  targetType: string,
  options: { ruleId?: string; labelOffsetX?: number; curvature?: number } = {}
): EdgeRoute {
  const sc = ENTITY_COUCHE_BY_TYPE[sourceType];
  const tc = ENTITY_COUCHE_BY_TYPE[targetType];
  const si = sc ? COUCHE_ORDER.indexOf(sc) : 0;
  const ti = tc ? COUCHE_ORDER.indexOf(tc) : 0;
  const downward = ti > si;

  return {
    sourceHandle: downward ? "source-bottom" : "source-top",
    targetHandle: downward ? "target-top" : "target-bottom",
    pathType: "bezier",
    curvature: options.curvature ?? 0.15,
    labelPosition: 0.5,
    labelOffsetX: options.labelOffsetX ?? 0,
    labelOffsetY: 0,
    ruleId: options.ruleId,
  };
}

/** Routage extérieur uniquement si plus de 2 couches séparent source et cible. */
export function shouldUseExteriorRouting(sourceType: string, targetType: string): boolean {
  if (!isCrossCoucheEdge(sourceType, targetType)) return false;
  return coucheLayerGap(sourceType, targetType) > 2;
}

function roundedPolyline(points: Point[], radius: number): string {
  if (points.length < 2) return "";
  if (radius <= 0 || points.length === 2) {
    return points.map((p, i) => `${i === 0 ? "M" : "L"} ${p.x} ${p.y}`).join(" ");
  }

  let d = `M ${points[0].x} ${points[0].y}`;
  for (let i = 1; i < points.length - 1; i++) {
    const prev = points[i - 1];
    const curr = points[i];
    const next = points[i + 1];
    const v1 = { x: curr.x - prev.x, y: curr.y - prev.y };
    const v2 = { x: next.x - curr.x, y: next.y - curr.y };
    const len1 = Math.hypot(v1.x, v1.y) || 1;
    const len2 = Math.hypot(v2.x, v2.y) || 1;
    const r = Math.min(radius, len1 / 2, len2 / 2);
    const p1 = { x: curr.x - (v1.x / len1) * r, y: curr.y - (v1.y / len1) * r };
    const p2 = { x: curr.x + (v2.x / len2) * r, y: curr.y + (v2.y / len2) * r };
    d += ` L ${p1.x} ${p1.y} Q ${curr.x} ${curr.y} ${p2.x} ${p2.y}`;
  }
  const last = points[points.length - 1];
  d += ` L ${last.x} ${last.y}`;
  return d;
}

/** Tracé orthogonal extérieur (4 segments max, coins arrondis). */
export function buildExteriorOrthogonalPath(
  sourceX: number,
  sourceY: number,
  targetX: number,
  targetY: number,
  corridorX: number,
  borderRadius = 12
): [path: string, labelX: number, labelY: number] {
  const points: Point[] = [
    { x: sourceX, y: sourceY },
    { x: corridorX, y: sourceY },
    { x: corridorX, y: targetY },
    { x: targetX, y: targetY },
  ];
  return [roundedPolyline(points, borderRadius), corridorX, (sourceY + targetY) / 2];
}

export type ExteriorRouteOptions = {
  ruleId?: string;
  isDerived?: boolean;
  laneIndex?: number;
};

export function buildExteriorRoute(
  sourcePos: Point,
  targetPos: Point,
  bounds: GraphBounds,
  options: ExteriorRouteOptions = {}
): EdgeRoute {
  const leftOutside = bounds.xMin - EXTERIOR_MARGIN;
  const rightOutside = bounds.xMax + EXTERIOR_MARGIN;

  const srcLeft = sourcePos.x;
  const srcRight = sourcePos.x + NODE_W;
  const tgtLeft = targetPos.x;
  const tgtRight = targetPos.x + NODE_W;
  const srcCy = sourcePos.y + NODE_H / 2;
  const tgtCy = targetPos.y + NODE_H / 2;

  const costLeft =
    Math.abs(srcLeft - leftOutside) + Math.abs(tgtLeft - leftOutside) + Math.abs(srcCy - tgtCy) * 0.02;
  const costRight =
    Math.abs(srcRight - rightOutside) + Math.abs(tgtRight - rightOutside) + Math.abs(srcCy - tgtCy) * 0.02;
  const useLeft = costLeft <= costRight;

  const lane = (options.laneIndex ?? 0) * CORRIDOR_LANE_STEP;
  const corridorX = useLeft ? leftOutside - lane : rightOutside + lane;

  const downward = tgtCy >= srcCy;
  const sourceHandle = useLeft ? "source-left" : "source-right";
  const targetHandle = useLeft
    ? downward
      ? "target-left"
      : "target-left"
    : downward
      ? "target-right"
      : "target-right";

  return {
    sourceHandle,
    targetHandle,
    pathType: "exterior",
    curvature: 0,
    routeOffset: 0,
    routeCenterX: corridorX,
    routeCenterY: (srcCy + tgtCy) / 2,
    routeStepPosition: 0.5,
    labelPosition: 0.5,
    labelOffsetX: useLeft ? -40 : 40,
    labelOffsetY: 0,
    ruleId: options.ruleId,
  };
}
