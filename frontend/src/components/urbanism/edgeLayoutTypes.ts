/** Tracé manuel des relations — waypoints verrouillés. */

export type LayoutPoint = { x: number; y: number };

export type EdgeLayoutOverride = {
  mode: "manual";
  locked: boolean;
  pathType?: "custom";
  waypoints: LayoutPoint[];
  sourceHandle: string;
  targetHandle: string;
  labelPosition?: number;
  labelOffsetX?: number;
  labelOffsetY?: number;
};

/** Lien en mode manuel (verrouillé) — compatibilité ancien format locked seul. */
export function isManualLayout(layout: unknown): layout is EdgeLayoutOverride {
  if (!layout || typeof layout !== "object") return false;
  const l = layout as EdgeLayoutOverride;
  const manual = l.mode === "manual" || l.locked === true;
  return manual && Array.isArray(l.waypoints);
}

/** @deprecated Utiliser isManualLayout */
export const isLockedLayout = isManualLayout;
