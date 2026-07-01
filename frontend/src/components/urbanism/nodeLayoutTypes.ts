/** Placement manuel des objets — verrouillage par entité. */

export type NodeLayoutOverride = {
  mode: "manual";
  locked: boolean;
  x: number;
  y: number;
};

export type NodeLayoutState = NodeLayoutOverride | {
  mode: "auto";
  locked: false;
  x?: number;
  y?: number;
};

export function isManualNodeLayout(layout: unknown): layout is NodeLayoutOverride {
  if (!layout || typeof layout !== "object") return false;
  const l = layout as NodeLayoutOverride;
  return (l.mode === "manual" || l.locked === true) && typeof l.x === "number" && typeof l.y === "number";
}

export function toManualNodeLayout(x: number, y: number): NodeLayoutOverride {
  return { mode: "manual", locked: true, x, y };
}
