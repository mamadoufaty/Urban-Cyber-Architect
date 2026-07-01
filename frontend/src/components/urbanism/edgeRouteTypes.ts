export interface EdgeRoute {
  sourceHandle: string;
  targetHandle: string;
  pathType: "bezier" | "smoothstep" | "straight" | "exterior";
  curvature: number;
  labelPosition: number;
  labelOffsetX: number;
  labelOffsetY: number;
  ruleId?: string;
  routeOffset?: number;
  routeCenterX?: number;
  routeCenterY?: number;
  routeStepPosition?: number;
}

export type GraphBounds = {
  xMin: number;
  xMax: number;
  yMin: number;
  yMax: number;
};

export type EdgeRouteContext = {
  sourcePos: { x: number; y: number };
  targetPos: { x: number; y: number };
  bounds: GraphBounds;
  laneIndex?: number;
  isDerived?: boolean;
};
