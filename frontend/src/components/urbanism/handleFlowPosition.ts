import { NODE_H, NODE_W } from "./exteriorEdgeRouting";
import type { LayoutPoint } from "./edgeLayoutTypes";

const HANDLE_ANCHOR: Record<string, { dx: number; dy: number }> = {
  "source-left": { dx: 0, dy: 0.5 },
  "source-right": { dx: 1, dy: 0.5 },
  "source-top": { dx: 0.5, dy: 0 },
  "source-bottom": { dx: 0.5, dy: 1 },
  "target-left": { dx: 0, dy: 0.5 },
  "target-right": { dx: 1, dy: 0.5 },
  "target-top": { dx: 0.5, dy: 0 },
  "target-bottom": { dx: 0.5, dy: 1 },
};

export function handleFlowPosition(
  nodePosition: { x: number; y: number },
  handleId: string | null | undefined
): LayoutPoint {
  const key = handleId ?? "source-right";
  const anchor = HANDLE_ANCHOR[key] ?? { dx: 1, dy: 0.5 };
  return {
    x: nodePosition.x + NODE_W * anchor.dx,
    y: nodePosition.y + NODE_H * anchor.dy,
  };
}
