import { memo } from "react";
import type { NodeProps } from "@xyflow/react";
import type { LayerBandData } from "./layoutClubUrba";

function LayerBandNode({ data }: NodeProps) {
  const band = data as LayerBandData;

  return (
    <div
      className="layer-band-node"
      style={{
        width: band.width,
        height: band.height,
        borderColor: `${band.color}40`,
        background: `linear-gradient(90deg, ${band.color}14 0%, ${band.color}06 50%, transparent 100%)`,
      }}
    >
      <div className="layer-band-label" style={{ color: band.color }}>
        {band.label}
      </div>
      <div className="layer-band-separator" style={{ background: `${band.color}25` }} />
    </div>
  );
}

export default memo(LayerBandNode);
