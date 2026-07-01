import type { EdgeRoute } from "./edgeRouteTypes";
import type { EdgeLayoutOverride, LayoutPoint } from "./edgeLayoutTypes";

export function roundedPolyline(points: LayoutPoint[], radius = 10): string {
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

export function buildCustomEdgePath(
  sourceX: number,
  sourceY: number,
  targetX: number,
  targetY: number,
  waypoints: LayoutPoint[]
): string {
  return roundedPolyline(
    [{ x: sourceX, y: sourceY }, ...waypoints, { x: targetX, y: targetY }],
    10
  );
}

export function labelOnPolyline(points: LayoutPoint[], t: number): LayoutPoint {
  if (points.length < 2) return points[0] ?? { x: 0, y: 0 };
  const segments: { a: LayoutPoint; b: LayoutPoint; len: number }[] = [];
  let total = 0;
  for (let i = 0; i < points.length - 1; i++) {
    const a = points[i];
    const b = points[i + 1];
    const len = Math.hypot(b.x - a.x, b.y - a.y);
    segments.push({ a, b, len });
    total += len;
  }
  if (total === 0) return points[0];
  let dist = Math.max(0, Math.min(1, t)) * total;
  for (const seg of segments) {
    if (dist <= seg.len) {
      const r = seg.len === 0 ? 0 : dist / seg.len;
      return { x: seg.a.x + (seg.b.x - seg.a.x) * r, y: seg.a.y + (seg.b.y - seg.a.y) * r };
    }
    dist -= seg.len;
  }
  return points[points.length - 1];
}

export function inferWaypointsFromAutoRoute(
  sourceX: number,
  sourceY: number,
  targetX: number,
  targetY: number,
  route: EdgeRoute
): LayoutPoint[] {
  if (route.pathType === "exterior" && route.routeCenterX !== undefined) {
    return [
      { x: route.routeCenterX, y: sourceY },
      { x: route.routeCenterX, y: targetY },
    ];
  }
  if (route.pathType === "smoothstep") {
    const midX = route.routeCenterX ?? (sourceX + targetX) / 2;
    return [
      { x: midX, y: sourceY },
      { x: midX, y: targetY },
    ];
  }
  if (route.pathType === "straight") return [];
  const midX = (sourceX + targetX) / 2;
  const midY = (sourceY + targetY) / 2;
  return [{ x: midX, y: midY }];
}

export function layoutToEdgeData(layout: EdgeLayoutOverride) {
  return {
    pathType: "custom" as const,
    waypoints: layout.waypoints,
    sourceHandle: layout.sourceHandle,
    targetHandle: layout.targetHandle,
    labelPosition: layout.labelPosition ?? 0.5,
    labelOffsetX: layout.labelOffsetX ?? 0,
    labelOffsetY: layout.labelOffsetY ?? -12,
    layoutMode: "manual" as const,
    layoutLocked: true,
  };
}

/** Insère un point sur le segment le plus proche du clic. */
export function insertWaypointAtClick(
  sourceX: number,
  sourceY: number,
  targetX: number,
  targetY: number,
  waypoints: LayoutPoint[],
  click: LayoutPoint
): { waypoints: LayoutPoint[]; index: number } {
  const chain = [{ x: sourceX, y: sourceY }, ...waypoints, { x: targetX, y: targetY }];
  let bestDist = Infinity;
  let bestIndex = 0;
  let bestPoint = click;

  for (let i = 0; i < chain.length - 1; i++) {
    const a = chain[i];
    const b = chain[i + 1];
    const dx = b.x - a.x;
    const dy = b.y - a.y;
    const len2 = dx * dx + dy * dy;
    const t = len2 === 0 ? 0 : Math.max(0, Math.min(1, ((click.x - a.x) * dx + (click.y - a.y) * dy) / len2));
    const proj = { x: a.x + dx * t, y: a.y + dy * t };
    const d = Math.hypot(click.x - proj.x, click.y - proj.y);
    if (d < bestDist) {
      bestDist = d;
      bestIndex = i;
      bestPoint = proj;
    }
  }

  const next = [...waypoints];
  next.splice(bestIndex, 0, bestPoint);
  return { waypoints: next, index: bestIndex };
}

export function toLayoutPayload(
  waypoints: LayoutPoint[],
  sourceHandle: string,
  targetHandle: string,
  labelPosition = 0.5,
  labelOffsetX = 0,
  labelOffsetY = -12
): EdgeLayoutOverride {
  return {
    mode: "manual",
    locked: true,
    pathType: "custom",
    waypoints,
    sourceHandle,
    targetHandle,
    labelPosition,
    labelOffsetX,
    labelOffsetY,
  };
}
