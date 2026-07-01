import { memo } from "react";
import { Handle, Position, type NodeProps } from "@xyflow/react";
import type { UrbanismNodeData } from "./layoutGraph";

function UrbanismNode({ data }: NodeProps) {
  const nodeData = data as UrbanismNodeData;
  const color = nodeData.coucheColor;
  const locked = nodeData.layoutLocked;

  return (
    <div
      className={`urbanism-node club-urba-node${locked ? " urbanism-node-locked" : ""}`}
      style={{
        background: `${color}22`,
        borderColor: color,
      }}
    >
      {locked && <span className="urbanism-node-lock" title="Position verrouillée">🔒</span>}
      <Handle type="target" position={Position.Top} id="target-top" className="urbanism-handle" />
      <Handle type="target" position={Position.Left} id="target-left" className="urbanism-handle" />
      <Handle type="target" position={Position.Right} id="target-right" className="urbanism-handle" />
      <Handle type="target" position={Position.Bottom} id="target-bottom" className="urbanism-handle" />
      <Handle type="source" position={Position.Bottom} id="source-bottom" className="urbanism-handle" />
      <Handle type="source" position={Position.Right} id="source-right" className="urbanism-handle" />
      <Handle type="source" position={Position.Top} id="source-top" className="urbanism-handle" />
      <Handle type="source" position={Position.Left} id="source-left" className="urbanism-handle" />
      <span className="urbanism-node-layer" style={{ color }}>
        {nodeData.zoneLabel}
      </span>
      <span className="urbanism-node-label">{nodeData.label}</span>
    </div>
  );
}

export default memo(UrbanismNode);
