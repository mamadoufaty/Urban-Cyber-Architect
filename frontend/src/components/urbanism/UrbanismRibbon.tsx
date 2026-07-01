import type { Project } from "../../api";
import type { ChartMode } from "./urbanismTypes";

type UrbanismRibbonProps = {
  projects: Project[];
  selectedProjectId: string;
  onProjectChange: (id: string) => void;
  expertMode: boolean;
  onExpertModeChange: (value: boolean) => void;
  chartMode: ChartMode;
  onChartModeChange: (mode: ChartMode) => void;
  onRelayout: () => void;
  onAlignH: () => void;
  onAlignV: () => void;
  onDistributeH: () => void;
  onDistributeV: () => void;
  onCenter: () => void;
  alignDisabled: { h: boolean; v: boolean; dh: boolean; dv: boolean; center: boolean };
  onExportPng: () => void;
  onExportPdf: () => void;
  exportDisabled: boolean;
  author: string;
  onAuthorChange: (value: string) => void;
  onDeduplicate: () => void;
  deduplicateDisabled: boolean;
  deduplicating: boolean;
  onResetEdge?: () => void;
  onResetNodes?: () => void;
  showResetEdge?: boolean;
  showResetNodes?: boolean;
  saveStatus: string | null;
};

function RibbonGroup({ children, label }: { children: React.ReactNode; label?: string }) {
  return (
    <div className="ua-ribbon-group" role="group" aria-label={label}>
      {children}
    </div>
  );
}

function RibbonSep() {
  return <div className="ua-ribbon-sep" aria-hidden />;
}

export default function UrbanismRibbon({
  projects,
  selectedProjectId,
  onProjectChange,
  expertMode,
  onExpertModeChange,
  chartMode,
  onChartModeChange,
  onRelayout,
  onAlignH,
  onAlignV,
  onDistributeH,
  onDistributeV,
  onCenter,
  alignDisabled,
  onExportPng,
  onExportPdf,
  exportDisabled,
  author,
  onAuthorChange,
  onDeduplicate,
  deduplicateDisabled,
  deduplicating,
  onResetEdge,
  onResetNodes,
  showResetEdge,
  showResetNodes,
  saveStatus,
}: UrbanismRibbonProps) {
  return (
    <div className="ua-ribbon">
      <div className="ua-ribbon-row ua-ribbon-row-top">
        <label className="ua-ribbon-project">
          <span className="ua-ribbon-project-label">Projet</span>
          <select
            value={selectedProjectId}
            onChange={(e) => onProjectChange(e.target.value)}
            className="ua-select"
          >
            {projects.map((p) => (
              <option key={p.id} value={p.id}>{p.name}</option>
            ))}
          </select>
        </label>
        <label className="ua-ribbon-expert">
          <input
            type="checkbox"
            checked={expertMode}
            onChange={(e) => onExpertModeChange(e.target.checked)}
          />
          Mode expert
        </label>
        {saveStatus && <span className="ua-ribbon-status">{saveStatus}</span>}
      </div>

      <div className="ua-ribbon-row ua-ribbon-row-actions">
        <RibbonGroup label="Mode cartographie">
          <button
            type="button"
            className={`ua-btn ua-btn-toggle${chartMode === "auto" ? " active" : ""}`}
            onClick={() => onChartModeChange("auto")}
          >
            Automatique
          </button>
          <button
            type="button"
            className={`ua-btn ua-btn-toggle${chartMode === "edit" ? " active" : ""}`}
            onClick={() => onChartModeChange("edit")}
          >
            Édition
          </button>
          <button type="button" className="ua-btn" onClick={onRelayout}>
            Réorganiser
          </button>
          {showResetEdge && onResetEdge && (
            <button type="button" className="ua-btn" onClick={onResetEdge}>
              Réinit. lien
            </button>
          )}
          {showResetNodes && onResetNodes && (
            <button type="button" className="ua-btn" onClick={onResetNodes}>
              Réinit. position
            </button>
          )}
        </RibbonGroup>

        <RibbonSep />

        <RibbonGroup label="Alignement">
          <button type="button" className="ua-btn" disabled={alignDisabled.h} onClick={onAlignH}>
            Aligner H
          </button>
          <button type="button" className="ua-btn" disabled={alignDisabled.v} onClick={onAlignV}>
            Aligner V
          </button>
          <button type="button" className="ua-btn" disabled={alignDisabled.dh} onClick={onDistributeH}>
            Distribuer H
          </button>
          <button type="button" className="ua-btn" disabled={alignDisabled.dv} onClick={onDistributeV}>
            Distribuer V
          </button>
          <button type="button" className="ua-btn" disabled={alignDisabled.center} onClick={onCenter}>
            Centrer
          </button>
        </RibbonGroup>

        <RibbonSep />

        <RibbonGroup label="Export">
          <button type="button" className="ua-btn ua-btn-primary" disabled={exportDisabled} onClick={onExportPng}>
            Export PNG
          </button>
          <button type="button" className="ua-btn ua-btn-primary" disabled={exportDisabled} onClick={onExportPdf}>
            Export PDF
          </button>
          <label className="ua-ribbon-author">
            <span className="sr-only">Auteur PDF</span>
            <input
              className="ua-input-compact"
              value={author}
              onChange={(e) => onAuthorChange(e.target.value)}
              placeholder="Auteur PDF"
              title="Auteur (PDF)"
            />
          </label>
        </RibbonGroup>

        <RibbonSep />

        <RibbonGroup label="Maintenance">
          <button
            type="button"
            className="ua-btn"
            disabled={deduplicateDisabled || deduplicating}
            onClick={onDeduplicate}
          >
            {deduplicating ? "Fusion…" : "Fusion doublons"}
          </button>
        </RibbonGroup>
      </div>
    </div>
  );
}
