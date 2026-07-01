import type { Edge, Node } from "@xyflow/react";

import { Position } from "@xyflow/react";

import { CLUB_URBA_DEFINITIONS } from "./clubUrbaZones";

import {
  BAND_BOTTOM_PAD,
  computeBandHeightsForNodes,
  computeBandYOffset,
  computeCanonicalPositions,
  coucheBandIndex,
  getBandHeight,
  maxCanonicalWidth,
  NODE_VISUAL_HEIGHT,
  resolveEdgeRoute,
  totalCanvasHeightFromBands,
} from "./clubUrbaCanonicalLayout";

import { COUCHE_ORDER, COUCHE_COLORS, resolveEntityCouche, type CoucheId } from "./clubUrbaConfig";

import { computeGraphBounds, shouldUseExteriorRouting } from "./exteriorEdgeRouting";

import { isManualLayout } from "./edgeLayoutTypes";
import { isManualNodeLayout } from "./nodeLayoutTypes";

import { layoutToEdgeData } from "./edgeLayoutUtils";

import type { UrbanismGraph } from "./metamodel";



export type UrbanismNodeData = {

  label: string;

  zoneLabel: string;

  entityType: string;

  couche: CoucheId;

  coucheLabel: string;

  coucheColor: string;

  layoutMode?: "auto" | "manual";

  layoutLocked?: boolean;

};



export type UrbanismEdgeData = {

  relationType: string;

  curvature: number;

  pathType: "bezier" | "smoothstep" | "straight" | "exterior" | "custom";

  labelPosition: number;

  labelOffsetX: number;

  labelOffsetY: number;

  ruleId?: string;

  derived?: boolean;

  routeOffset?: number;

  routeCenterX?: number;

  routeCenterY?: number;

  routeStepPosition?: number;

  waypoints?: Array<{ x: number; y: number }>;

  layoutMode?: "auto" | "manual";

  layoutLocked?: boolean;

};



export type LayerBandData = {

  label: string;

  color: string;

  width: number;

  height: number;

};



type GraphNode = UrbanismGraph["nodes"][number] & { layout?: unknown };



function extendBandHeightsForManualNodes(

  bandHeights: Record<CoucheId, number>,

  manualNodes: Array<{ id: string; couche: CoucheId; layout: { x: number; y: number } }>

): Record<CoucheId, number> {

  const next = { ...bandHeights };

  for (const node of manualNodes) {

    const bandStart = computeBandYOffset(coucheBandIndex(node.couche), next);

    const needed = Math.ceil(node.layout.y + NODE_VISUAL_HEIGHT + BAND_BOTTOM_PAD - bandStart);

    if (needed > (next[node.couche] ?? getBandHeight(node.couche))) {

      next[node.couche] = needed;

    }

  }

  return next;

}



function resolveNodePosition(

  n: GraphNode,

  canonicalPositions: Map<string, { x: number; y: number }>

): { position: { x: number; y: number }; layoutMode: "auto" | "manual"; layoutLocked: boolean } {

  const graphLayout = (n as { layout?: unknown }).layout;

  if (isManualNodeLayout(graphLayout)) {

    return {

      position: { x: graphLayout.x, y: graphLayout.y },

      layoutMode: "manual",

      layoutLocked: true,

    };

  }

  const position = canonicalPositions.get(n.id) ?? { x: 0, y: 0 };

  return { position, layoutMode: "auto", layoutLocked: false };

}



const EDGE_RENDER_ORDER: Record<string, number> = {

  définit: 1,

  pilote: 2,

  "est pris en compte dans": 3,

};



const MANDATORY_METIER_RELATIONS = new Set(["définit", "pilote", "est pris en compte dans"]);



function bandNodesForGraph(

  graph: UrbanismGraph,

  visibleCouches: Set<CoucheId>,

  bandHeights: Record<CoucheId, number>

): Node[] {

  const resolvedNodes = graph.nodes.map((n) => ({

    ...n,

    couche: resolveEntityCouche(n.entity_type, n.couche),

  }));

  const maxX = maxCanonicalWidth(resolvedNodes);

  const bands: Node[] = [];



  COUCHE_ORDER.forEach((coucheId, bandIndex) => {

    if (!visibleCouches.has(coucheId)) return;

    const layer = graph.meta_layers.find((l) => l.id === coucheId);

    const def = CLUB_URBA_DEFINITIONS.find((d) => d.id === coucheId);

    bands.push({

      id: `band-${coucheId}`,

      type: "layerBand",

      position: { x: 0, y: computeBandYOffset(bandIndex, bandHeights) },

      data: {

        label: layer?.label ?? def?.label ?? coucheId,

        color: layer?.color ?? COUCHE_COLORS[coucheId],

        width: maxX,

        height: bandHeights[coucheId] ?? getBandHeight(coucheId),

      } satisfies LayerBandData,

      draggable: false,

      selectable: false,

      focusable: false,

      zIndex: -1,

    });

  });

  return bands;

}



function nodeTypeMap(nodes: GraphNode[]): Map<string, string> {

  return new Map(nodes.map((n) => [n.id, n.entity_type]));

}



export function graphToFlow(

  graph: UrbanismGraph,

  visibleCouches: Set<CoucheId>

): { nodes: Node[]; edges: Edge[] } {

  const visibleNodes = graph.nodes.filter((n) =>

    visibleCouches.has(resolveEntityCouche(n.entity_type, n.couche))

  );

  const visibleNodeIds = new Set(visibleNodes.map((n) => n.id));

  const resolvedNodes = visibleNodes.map((n) => ({

    ...n,

    couche: resolveEntityCouche(n.entity_type, n.couche),

  }));

  const autoNodes = resolvedNodes.filter((n) => !isManualNodeLayout((n as GraphNode).layout));

  const manualNodes = resolvedNodes

    .filter((n) => isManualNodeLayout((n as GraphNode).layout))

    .map((n) => ({

      id: n.id,

      couche: n.couche as CoucheId,

      layout: (n as GraphNode).layout as { x: number; y: number },

    }));

  let bandHeights = computeBandHeightsForNodes(autoNodes);

  bandHeights = extendBandHeightsForManualNodes(bandHeights, manualNodes);

  const canonicalPositions = computeCanonicalPositions(autoNodes, bandHeights);

  const types = nodeTypeMap(graph.nodes);



  const visibleEdges = graph.edges.filter(

    (e) => visibleNodeIds.has(e.source) && visibleNodeIds.has(e.target)

  );



  const objectNodes: Node[] = resolvedNodes.map((n) => {

    const couche = n.couche as CoucheId;

    const { position, layoutMode, layoutLocked } = resolveNodePosition(n as GraphNode, canonicalPositions);

    if (!canonicalPositions.has(n.id) && !isManualNodeLayout((n as GraphNode).layout)) {

      console.warn("[urbanism layout] position manquante pour", n.id, n.label, n.entity_type);

    }

    return {

      id: n.id,

      type: "urbanism",

      position,

      data: {

        label: n.label,

        zoneLabel: n.entity_type_label,

        entityType: n.entity_type,

        couche,

        coucheLabel: n.couche_label,

        coucheColor: COUCHE_COLORS[couche],

        layoutMode,

        layoutLocked,

      } satisfies UrbanismNodeData,

      zIndex: 2,

    };

  });



  const bounds = computeGraphBounds(objectNodes);

  const nodePosById = new Map(objectNodes.map((n) => [n.id, n.position]));

  const corridorLanes = new Map<string, number>();



  const edges: Edge[] = visibleEdges

    .map((e) => {

      const sourceType = types.get(e.source) ?? "";

      const targetType = types.get(e.target) ?? "";

      const isDerived = Boolean((e as { derived?: boolean }).derived);

      const sourcePos = nodePosById.get(e.source);

      const targetPos = nodePosById.get(e.target);



      const graphLayout = (e as { layout?: unknown }).layout;

      const manualLayout = isManualLayout(graphLayout) ? graphLayout : null;



      let laneIndex = 0;

      if (!manualLayout && sourcePos && targetPos && shouldUseExteriorRouting(sourceType, targetType)) {

        const laneKey = [sourceType, targetType].sort().join("|");

        laneIndex = corridorLanes.get(laneKey) ?? 0;

        corridorLanes.set(laneKey, laneIndex + 1);

      }



      const route = manualLayout

        ? {

            sourceHandle: manualLayout.sourceHandle,

            targetHandle: manualLayout.targetHandle,

            pathType: "custom" as const,

            curvature: 0,

            labelPosition: manualLayout.labelPosition ?? 0.5,

            labelOffsetX: manualLayout.labelOffsetX ?? 0,

            labelOffsetY: manualLayout.labelOffsetY ?? -12,

          }

        : resolveEdgeRoute(sourceType, targetType, e.relation_type, {

            sourcePos: sourcePos ?? { x: 0, y: 0 },

            targetPos: targetPos ?? { x: 0, y: 0 },

            bounds,

            laneIndex,

            isDerived,

          });

      const isMandatory = MANDATORY_METIER_RELATIONS.has(e.relation_type);

      const isR05 = e.relation_type === "est pris en compte dans";



      return {

        id: e.id,

        type: "urbanismEdge",

        source: e.source,

        target: e.target,

        sourceHandle: route.sourceHandle,

        targetHandle: route.targetHandle,

        label: e.relation_type,

        animated: !isDerived && (e.criticite === "critique" || e.criticite === "élevée"),

        zIndex: isR05 ? 1000 : isDerived ? 1 : isMandatory ? 900 : 10,

        style: {

          stroke: isDerived

            ? "#f59e0b"

            : isR05

              ? "#00d4aa"

              : e.criticite === "critique"

                ? "#ef4444"

                : e.criticite === "élevée"

                  ? "#f59e0b"

                  : isMandatory

                    ? "#7dd3c0"

                    : "#94a3b8",

          strokeWidth: isDerived ? 1.75 : isR05 ? 2.75 : isMandatory ? 2.25 : e.criticite === "critique" ? 2.5 : 2,

          strokeDasharray: isDerived ? "6 4" : undefined,

          opacity: isDerived ? 0.72 : 1,

        },

        markerEnd: isR05 ? "url(#urbanism-arrow-accent)" : "url(#urbanism-arrow)",

        selectable: true,

        focusable: true,

        interactionWidth: 24,

        data: {
          relationType: e.relation_type,
          derived: isDerived,
          ruleId: "ruleId" in route ? route.ruleId : undefined,
          routeOffset: "routeOffset" in route ? route.routeOffset : undefined,
          routeCenterX: "routeCenterX" in route ? route.routeCenterX : undefined,
          routeCenterY: "routeCenterY" in route ? route.routeCenterY : undefined,
          routeStepPosition: "routeStepPosition" in route ? route.routeStepPosition : undefined,
          curvature: manualLayout ? 0 : route.curvature,
          ...(manualLayout
            ? layoutToEdgeData(manualLayout)
            : {
                pathType: route.pathType,
                labelPosition: route.labelPosition,
                labelOffsetX: route.labelOffsetX,
                labelOffsetY: route.labelOffsetY,
                layoutMode: "auto" as const,
                layoutLocked: false,
              }),
        } satisfies UrbanismEdgeData,

      };

    })

    .sort(

      (a, b) =>

        (EDGE_RENDER_ORDER[String(a.label)] ?? 0) - (EDGE_RENDER_ORDER[String(b.label)] ?? 0)

    );



  return { nodes: [...bandNodesForGraph(graph, visibleCouches, bandHeights), ...objectNodes], edges };

}



export function autoLayoutFromGraph(

  graph: UrbanismGraph,

  visibleCouches: Set<CoucheId>

): Node[] {

  return graphToFlow(graph, visibleCouches).nodes;

}



export const HANDLE_POSITIONS: Record<string, Position> = {

  "source-top": Position.Top,

  "source-right": Position.Right,

  "source-bottom": Position.Bottom,

  "source-left": Position.Left,

  "target-top": Position.Top,

  "target-right": Position.Right,

  "target-bottom": Position.Bottom,

  "target-left": Position.Left,

};



export function totalCanvasHeight(

  visibleCouches: Set<CoucheId>,

  bandHeights?: Record<CoucheId, number>

): number {

  return totalCanvasHeightFromBands(visibleCouches, bandHeights);

}


