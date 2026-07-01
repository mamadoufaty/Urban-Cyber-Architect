import { createContext, useContext } from "react";
import type { LayoutPoint } from "./edgeLayoutTypes";

export type EdgeEditActions = {
  editMode: boolean;
  onWaypointDrag: (edgeId: string, index: number, point: LayoutPoint) => void;
  onWaypointDragEnd: (edgeId: string) => void;
  clientToFlow: (clientX: number, clientY: number) => LayoutPoint;
  activeWaypointIndex: number | null;
  setActiveWaypointIndex: (index: number | null) => void;
};

export const EdgeEditContext = createContext<EdgeEditActions | null>(null);

export function useEdgeEdit(): EdgeEditActions | null {
  return useContext(EdgeEditContext);
}
