import { useCallback, useRef } from "react";
import {
  BaseEdge,
  EdgeLabelRenderer,
  getBezierPath,
  getSmoothStepPath,
  getStraightPath,
  type EdgeProps,
} from "@xyflow/react";
import { useEdgeEdit } from "./EdgeEditContext";
import { buildCustomEdgePath, labelOnPolyline } from "./edgeLayoutUtils";
import { buildExteriorOrthogonalPath } from "./exteriorEdgeRouting";
import type { UrbanismEdgeData } from "./layoutGraph";

function interpolatePathPoint(
  path: string,
  t: number,
): { x: number; y: number } | null {
  const nums = path.match(/-?\d+\.?\d*/g);
  if (!nums || nums.length < 4) return null;
  const x1 = parseFloat(nums[0]);
  const y1 = parseFloat(nums[1]);
  const x2 = parseFloat(nums[nums.length - 2]);
  const y2 = parseFloat(nums[nums.length - 1]);
  return {
    x: x1 + (x2 - x1) * t,
    y: y1 + (y2 - y1) * t,
  };
}

function WaypointHandle({
  edgeId,
  index,
  x,
  y,
  active,
}: {
  edgeId: string;
  index: number;
  x: number;
  y: number;
  active: boolean;
}) {
  const edit = useEdgeEdit();
  const dragging = useRef(false);

  const onPointerDown = useCallback(
    (e: React.PointerEvent) => {
      e.stopPropagation();
      e.preventDefault();
      dragging.current = true;
      edit?.setActiveWaypointIndex(index);
      (e.target as HTMLElement).setPointerCapture(e.pointerId);
    },
    [edit, index]
  );

  const onPointerMove = useCallback(
    (e: React.PointerEvent) => {
      if (!dragging.current || !edit) return;
      e.stopPropagation();
      const flow = edit.clientToFlow(e.clientX, e.clientY);
      edit.onWaypointDrag(edgeId, index, flow);
    },
    [edit, edgeId, index]
  );

  const onPointerUp = useCallback(
    (e: React.PointerEvent) => {
      if (!dragging.current) return;
      dragging.current = false;
      edit?.onWaypointDragEnd(edgeId);
      (e.target as HTMLElement).releasePointerCapture(e.pointerId);
    },
    [edit, edgeId]
  );

  if (!edit) return null;

  return (
    <EdgeLabelRenderer>
      <div
        className={`edge-waypoint-handle${active ? " active" : ""}`}
        style={{ transform: `translate(-50%, -50%) translate(${x}px, ${y}px)` }}
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={onPointerUp}
        role="button"
        tabIndex={-1}
        aria-label={`Point de contrôle ${index + 1}`}
      />
    </EdgeLabelRenderer>
  );
}

export default function UrbanismEdge({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  label,
  style,
  markerEnd,
  data,
  selected,
}: EdgeProps) {
  const edit = useEdgeEdit();
  const edgeData = (data ?? {}) as UrbanismEdgeData;
  const pathType = edgeData.pathType ?? "bezier";
  const labelT = edgeData.labelPosition ?? 0.5;
  const isR05 = edgeData.ruleId === "R05" || edgeData.relationType === "est pris en compte dans";
  const isDerived = Boolean(edgeData.derived);
  const waypoints = edgeData.waypoints ?? [];
  const showHandles = Boolean(selected && edit?.editMode && edgeData.layoutMode !== "auto");

  let edgePath: string;
  let labelX: number;
  let labelY: number;

  if (pathType === "custom") {
    const chain = [{ x: sourceX, y: sourceY }, ...waypoints, { x: targetX, y: targetY }];
    edgePath = buildCustomEdgePath(sourceX, sourceY, targetX, targetY, waypoints);
    const labelPt = labelOnPolyline(chain, labelT);
    labelX = labelPt.x;
    labelY = labelPt.y;
  } else if (pathType === "exterior" && edgeData.routeCenterX !== undefined) {
    [edgePath, labelX, labelY] = buildExteriorOrthogonalPath(
      sourceX,
      sourceY,
      targetX,
      targetY,
      edgeData.routeCenterX
    );
  } else if (pathType === "straight") {
    [edgePath, labelX, labelY] = getStraightPath({
      sourceX,
      sourceY,
      targetX,
      targetY,
    });
  } else if (pathType === "smoothstep") {
    [edgePath, labelX, labelY] = getSmoothStepPath({
      sourceX,
      sourceY,
      sourcePosition,
      targetX,
      targetY,
      targetPosition,
      borderRadius: 12,
      offset: edgeData.routeOffset ?? 20,
      centerX: edgeData.routeCenterX,
      centerY: edgeData.routeCenterY,
      stepPosition: edgeData.routeStepPosition ?? 0.5,
    });
    const custom = interpolatePathPoint(edgePath, labelT);
    if (custom) {
      labelX = custom.x;
      labelY = custom.y;
    }
  } else {
    [edgePath, labelX, labelY] = getBezierPath({
      sourceX,
      sourceY,
      sourcePosition,
      targetX,
      targetY,
      targetPosition,
      curvature: edgeData.curvature ?? 0.25,
    });
    const sx = sourceX + (labelX - sourceX) * labelT + (targetX - labelX) * (labelT - 0.5) * 0.15;
    const sy = sourceY + (labelY - sourceY) * labelT;
    labelX = sx;
    labelY = sy;
  }

  labelX += edgeData.labelOffsetX ?? 0;
  labelY += edgeData.labelOffsetY ?? 0;

  const labelZ = isR05 ? 1002 : isDerived ? 2 : 1000;
  const edgeStyle = selected
    ? {
        ...style,
        strokeWidth: ((style?.strokeWidth as number) ?? 2) + 1,
        filter: "drop-shadow(0 0 4px rgba(0,212,170,0.45))",
      }
    : style;

  return (
    <>
      <BaseEdge id={id} path={edgePath} style={edgeStyle} markerEnd={markerEnd} interactionWidth={24} />
      {label && (
        <EdgeLabelRenderer>
          <div
            className={`urbanism-edge-label${isR05 ? " urbanism-edge-label-r05" : ""}${isDerived ? " urbanism-edge-label-derived" : ""}${selected ? " urbanism-edge-label-selected" : ""}`}
            data-relation={edgeData.relationType ?? label}
            data-rule={edgeData.ruleId}
            style={{
              transform: `translate(-50%, -50%) translate(${labelX}px, ${labelY}px)`,
              zIndex: labelZ,
              opacity: isDerived ? 0.85 : 1,
            }}
          >
            {label}
            {edgeData.layoutLocked && (
              <span className="edge-layout-locked" title="Lien verrouillé (mode manuel)">
                🔒
              </span>
            )}
          </div>
        </EdgeLabelRenderer>
      )}
      {showHandles &&
        waypoints.map((wp, i) => (
          <WaypointHandle
            key={`${id}-wp-${i}`}
            edgeId={id}
            index={i}
            x={wp.x}
            y={wp.y}
            active={edit?.activeWaypointIndex === i}
          />
        ))}
    </>
  );
}
