import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import {
  ReactFlow,
  ReactFlowProvider,
  Background,
  Controls,
  MiniMap,
  useReactFlow,
  applyNodeChanges,
  type Node,
  type Edge,
  type NodeChange,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { toPng } from "html-to-image";

import { useSidebar } from "../context/SidebarContext";
import UrbanismNode from "../components/urbanism/UrbanismNode";
import LayerBandNode from "../components/urbanism/LayerBandNode";
import UrbanismEdge from "../components/urbanism/UrbanismEdge";
import UrbanismAssistant from "../components/urbanism/UrbanismAssistant";
import UrbanismEngineEditor from "../components/urbanism/UrbanismEngineEditor";
import { EdgeEditContext } from "../components/urbanism/EdgeEditContext";
import { COUCHE_ORDER, type CoucheId } from "../components/urbanism/clubUrbaConfig";
import {
  inferWaypointsFromAutoRoute,
  insertWaypointAtClick,
  toLayoutPayload,
} from "../components/urbanism/edgeLayoutUtils";
import { handleFlowPosition } from "../components/urbanism/handleFlowPosition";
import { graphToFlow, type UrbanismEdgeData, type UrbanismNodeData } from "../components/urbanism/layoutGraph";
import {
  alignNodesHorizontally,
  alignNodesVertically,
  bandRectsFromNodes,
  centerNodeInBand,
  distributeNodesHorizontally,
  distributeNodesVertically,
  layoutsFromNodes,
} from "../components/urbanism/nodeLayoutAlign";
import { exportUrbanismPdf } from "../components/urbanism/exportPdf";
import UrbanismRibbon from "../components/urbanism/UrbanismRibbon";
import { FIT_VIEW_PADDING, type ChartMode } from "../components/urbanism/urbanismTypes";
import "../styles/urbanism-beta.css";
import {
  RELATION_FILTER_OPTIONS,
  type RelationCategory,
  type UrbanismAnalysis,
  type UrbanismGraph,
} from "../components/urbanism/metamodel";
import {
  clearEdgeLayout,
  clearEntityLayout,
  getUrbanismGraph,
  listProjects,
  saveEdgeLayout,
  saveEntityLayout,
  saveEntityLayoutsBulk,
  deduplicateUrbanism,
  type Project,
} from "../api";

const nodeTypes = { urbanism: UrbanismNode, layerBand: LayerBandNode };
const edgeTypes = { urbanismEdge: UrbanismEdge };

function SchemaCanvas({
  graph,
  projectId,
  projects,
  selectedProjectId,
  onProjectChange,
  expertMode,
  onExpertModeChange,
  relationFilters,
  onToggleRelationFilter,
  onClearRelationFilters,
  activeCategories,
  onLayoutChanged,
  onAnalysisUpdated,
}: {
  graph: UrbanismGraph;
  projectId: string;
  projects: Project[];
  selectedProjectId: string;
  onProjectChange: (id: string) => void;
  expertMode: boolean;
  onExpertModeChange: (value: boolean) => void;
  relationFilters: Set<RelationCategory>;
  onToggleRelationFilter: (id: RelationCategory) => void;
  onClearRelationFilters: () => void;
  activeCategories: Set<RelationCategory> | null;
  onLayoutChanged?: () => void;
  onAnalysisUpdated?: (analysis: UrbanismAnalysis) => void;
}) {
  const flowRef = useRef<HTMLDivElement>(null);
  const { fitView, screenToFlowPosition } = useReactFlow();
  const { sidebarOpen } = useSidebar();
  const [visibleCouches, setVisibleCouches] = useState<Set<CoucheId>>(() => new Set(COUCHE_ORDER));
  const [author, setAuthor] = useState(graph.author);
  const [chartMode, setChartMode] = useState<ChartMode>("auto");
  const [selectedEdgeId, setSelectedEdgeId] = useState<string | null>(null);
  const [selectedNodeIds, setSelectedNodeIds] = useState<string[]>([]);
  const [activeWaypointIndex, setActiveWaypointIndex] = useState<number | null>(null);
  const [saveStatus, setSaveStatus] = useState<string | null>(null);
  const [deduplicating, setDeduplicating] = useState(false);
  const saveTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const nodeSaveTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const { nodes: initialNodes, edges: initialEdges } = useMemo(
    () => graphToFlow(graph, visibleCouches),
    [graph, visibleCouches]
  );
  const [nodes, setNodes] = useState<Node[]>(initialNodes);
  const [edges, setEdges] = useState<Edge[]>(initialEdges);

  useEffect(() => {
    const flow = graphToFlow(graph, visibleCouches);
    setNodes(flow.nodes);
    setEdges(flow.edges);
    setSelectedEdgeId(null);
    setSelectedNodeIds([]);
    setActiveWaypointIndex(null);
    requestAnimationFrame(() => fitView({ padding: FIT_VIEW_PADDING }));
  }, [graph, visibleCouches, fitView]);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      fitView({ padding: FIT_VIEW_PADDING, duration: 200 });
    }, 280);
    return () => window.clearTimeout(timer);
  }, [sidebarOpen, fitView]);

  const getEdgeEndpoints = useCallback(
    (edge: Edge) => {
      const srcNode = nodes.find((n) => n.id === edge.source);
      const tgtNode = nodes.find((n) => n.id === edge.target);
      if (!srcNode || !tgtNode) return null;
      const source = handleFlowPosition(srcNode.position, edge.sourceHandle);
      const target = handleFlowPosition(tgtNode.position, edge.targetHandle);
      return { source, target };
    },
    [nodes]
  );

  const armEdgeForEditing = useCallback(
    (edgeId: string) => {
      if (chartMode !== "edit") return;
      setEdges((prev) =>
        prev.map((edge) => {
          if (edge.id !== edgeId) return edge;
          const data = edge.data as UrbanismEdgeData;
          if (data.layoutLocked || data.pathType === "custom") return edge;
          const endpoints = getEdgeEndpoints(edge);
          if (!endpoints) return edge;
          const waypoints = inferWaypointsFromAutoRoute(
            endpoints.source.x,
            endpoints.source.y,
            endpoints.target.x,
            endpoints.target.y,
            {
              sourceHandle: String(edge.sourceHandle ?? "source-right"),
              targetHandle: String(edge.targetHandle ?? "target-left"),
              pathType: data.pathType,
              curvature: data.curvature,
              routeCenterX: data.routeCenterX,
              routeCenterY: data.routeCenterY,
              routeOffset: data.routeOffset,
              routeStepPosition: data.routeStepPosition,
              labelPosition: data.labelPosition,
              labelOffsetX: data.labelOffsetX,
              labelOffsetY: data.labelOffsetY,
            }
          );
          return {
            ...edge,
            data: {
              ...data,
              pathType: "custom",
              waypoints,
              layoutLocked: false,
            },
          };
        })
      );
    },
    [chartMode, getEdgeEndpoints]
  );

  const persistEdgeLayout = useCallback(
    async (edgeId: string) => {
      const edge = edges.find((e) => e.id === edgeId);
      if (!edge) return;
      const data = edge.data as UrbanismEdgeData;
      const payload = toLayoutPayload(
        data.waypoints ?? [],
        String(edge.sourceHandle ?? "source-right"),
        String(edge.targetHandle ?? "target-left"),
        data.labelPosition,
        data.labelOffsetX,
        data.labelOffsetY
      );
      try {
        await saveEdgeLayout(projectId, edgeId, payload);
        setEdges((prev) =>
          prev.map((e) =>
            e.id === edgeId
              ? {
                  ...e,
                  data: {
                    ...(e.data as UrbanismEdgeData),
                    layoutMode: "manual",
                    layoutLocked: true,
                  },
                }
              : e
          )
        );
        setSaveStatus("Tracé enregistré");
        setTimeout(() => setSaveStatus(null), 2000);
      } catch {
        setSaveStatus("Erreur d'enregistrement");
      }
    },
    [edges, projectId]
  );

  const persistNodeLayout = useCallback(
    async (entityId: string, position: { x: number; y: number }) => {
      try {
        await saveEntityLayout(projectId, entityId, position);
        setNodes((prev) =>
          prev.map((n) =>
            n.id === entityId
              ? {
                  ...n,
                  position,
                  data: {
                    ...(n.data as UrbanismNodeData),
                    layoutMode: "manual",
                    layoutLocked: true,
                  },
                }
              : n
          )
        );
        setSaveStatus("Position enregistrée");
        setTimeout(() => setSaveStatus(null), 2000);
      } catch {
        setSaveStatus("Erreur d'enregistrement");
      }
    },
    [projectId]
  );

  const persistNodeLayoutsBulk = useCallback(
    async (updatedNodes: Node[]) => {
      const layouts = layoutsFromNodes(updatedNodes);
      if (!layouts.length) return;
      try {
        await saveEntityLayoutsBulk(projectId, layouts);
        setNodes((prev) => {
          const byId = new Map(updatedNodes.map((n) => [n.id, n]));
          return prev.map((n) => byId.get(n.id) ?? n);
        });
        setSaveStatus("Positions enregistrées");
        setTimeout(() => setSaveStatus(null), 2000);
      } catch {
        setSaveStatus("Erreur d'enregistrement");
      }
    },
    [projectId]
  );

  const onNodesChange = useCallback((changes: NodeChange[]) => {
    setNodes((nds) => applyNodeChanges(changes, nds));
  }, []);

  const onNodeDragStop = useCallback(
    (_event: MouseEvent | TouchEvent, node: Node) => {
      if (chartMode !== "edit" || node.type !== "urbanism") return;
      if (nodeSaveTimer.current) clearTimeout(nodeSaveTimer.current);
      nodeSaveTimer.current = setTimeout(() => void persistNodeLayout(node.id, node.position), 300);
    },
    [chartMode, persistNodeLayout]
  );

  const selectedUrbanismNodes = useMemo(
    () => nodes.filter((n) => selectedNodeIds.includes(n.id) && n.type === "urbanism"),
    [nodes, selectedNodeIds]
  );

  const applyAlignedNodes = useCallback(
    (aligned: Node[]) => {
      setNodes((prev) => {
        const byId = new Map(aligned.map((n) => [n.id, n]));
        return prev.map((n) => byId.get(n.id) ?? n);
      });
      void persistNodeLayoutsBulk(aligned);
    },
    [persistNodeLayoutsBulk]
  );

  const alignHorizontal = useCallback(() => {
    if (selectedUrbanismNodes.length < 2) return;
    applyAlignedNodes(alignNodesHorizontally(selectedUrbanismNodes));
  }, [applyAlignedNodes, selectedUrbanismNodes]);

  const alignVertical = useCallback(() => {
    if (selectedUrbanismNodes.length < 2) return;
    applyAlignedNodes(alignNodesVertically(selectedUrbanismNodes));
  }, [applyAlignedNodes, selectedUrbanismNodes]);

  const distributeHorizontal = useCallback(() => {
    if (selectedUrbanismNodes.length < 3) return;
    applyAlignedNodes(distributeNodesHorizontally(selectedUrbanismNodes));
  }, [applyAlignedNodes, selectedUrbanismNodes]);

  const distributeVertical = useCallback(() => {
    if (selectedUrbanismNodes.length < 3) return;
    applyAlignedNodes(distributeNodesVertically(selectedUrbanismNodes));
  }, [applyAlignedNodes, selectedUrbanismNodes]);

  const centerInLayer = useCallback(() => {
    if (!selectedUrbanismNodes.length) return;
    const bands = bandRectsFromNodes(nodes);
    const centered = selectedUrbanismNodes.map((n) => {
      const couche = (n.data as UrbanismNodeData).couche;
      const band = bands.get(couche);
      return band ? centerNodeInBand(n, band) : n;
    });
    applyAlignedNodes(centered);
  }, [applyAlignedNodes, nodes, selectedUrbanismNodes]);

  const resetSelectedNodesLayout = useCallback(async () => {
    if (!selectedNodeIds.length) return;
    try {
      await Promise.all(selectedNodeIds.map((id) => clearEntityLayout(projectId, id)));
      onLayoutChanged?.();
      setSelectedNodeIds([]);
      setSaveStatus("Position réinitialisée — placement automatique");
      setTimeout(() => setSaveStatus(null), 2500);
    } catch {
      setSaveStatus("Erreur lors de la réinitialisation");
    }
  }, [onLayoutChanged, projectId, selectedNodeIds]);

  const onWaypointDrag = useCallback(
    (edgeId: string, index: number, point: { x: number; y: number }) => {
      if (chartMode !== "edit") return;
      setEdges((prev) =>
      prev.map((edge) => {
        if (edge.id !== edgeId) return edge;
        const data = edge.data as UrbanismEdgeData;
        const waypoints = [...(data.waypoints ?? [])];
        waypoints[index] = point;
        return {
          ...edge,
          data: { ...data, pathType: "custom", waypoints, layoutMode: "manual", layoutLocked: data.layoutLocked ?? false },
        };
      })
    );
    },
    [chartMode]
  );

  const onWaypointDragEnd = useCallback(
    (edgeId: string) => {
      if (chartMode !== "edit") return;
      if (saveTimer.current) clearTimeout(saveTimer.current);
      saveTimer.current = setTimeout(() => void persistEdgeLayout(edgeId), 300);
    },
    [chartMode, persistEdgeLayout]
  );

  const clientToFlow = useCallback(
    (clientX: number, clientY: number) => screenToFlowPosition({ x: clientX, y: clientY }),
    [screenToFlowPosition]
  );

  const onSelectionChange = useCallback(
    ({ nodes: selectedNodes, edges: selected }: { nodes: Node[]; edges: Edge[] }) => {
      if (chartMode !== "edit") {
        setSelectedEdgeId(null);
        setSelectedNodeIds([]);
        setActiveWaypointIndex(null);
        return;
      }
      const objectIds = selectedNodes.filter((n) => n.type === "urbanism").map((n) => n.id);
      setSelectedNodeIds(objectIds);
      const id = selected[0]?.id ?? null;
      setSelectedEdgeId(id);
      setActiveWaypointIndex(null);
      if (id) armEdgeForEditing(id);
    },
    [armEdgeForEditing, chartMode]
  );

  const onEdgeDoubleClick = useCallback(
    (_event: React.MouseEvent, edge: Edge) => {
      if (chartMode !== "edit") return;
      const click = screenToFlowPosition({ x: _event.clientX, y: _event.clientY });
      const endpoints = getEdgeEndpoints(edge);
      if (!endpoints) return;
      const data = edge.data as UrbanismEdgeData;
      const current = data.waypoints ?? [];
      const { waypoints } = insertWaypointAtClick(
        endpoints.source.x,
        endpoints.source.y,
        endpoints.target.x,
        endpoints.target.y,
        current,
        click
      );
      setEdges((prev) =>
        prev.map((e) =>
          e.id === edge.id
            ? {
                ...e,
                selected: true,
                data: { ...data, pathType: "custom", waypoints, layoutLocked: false },
              }
            : e
        )
      );
      setSelectedEdgeId(edge.id);
      void persistEdgeLayout(edge.id);
    },
    [chartMode, getEdgeEndpoints, persistEdgeLayout, screenToFlowPosition]
  );

  const deleteActiveWaypoint = useCallback(() => {
    if (chartMode !== "edit") return;
    if (!selectedEdgeId || activeWaypointIndex === null) return;
    setEdges((prev) =>
      prev.map((edge) => {
        if (edge.id !== selectedEdgeId) return edge;
        const data = edge.data as UrbanismEdgeData;
        const waypoints = [...(data.waypoints ?? [])];
        waypoints.splice(activeWaypointIndex, 1);
        return { ...edge, data: { ...data, waypoints } };
      })
    );
    setActiveWaypointIndex(null);
    void persistEdgeLayout(selectedEdgeId);
  }, [activeWaypointIndex, chartMode, persistEdgeLayout, selectedEdgeId]);

  const resetSelectedEdgeLayout = useCallback(async () => {
    if (!selectedEdgeId) return;
    try {
      await clearEdgeLayout(projectId, selectedEdgeId);
      onLayoutChanged?.();
      setSelectedEdgeId(null);
      setSaveStatus("Tracé réinitialisé — routage automatique");
      setTimeout(() => setSaveStatus(null), 2500);
    } catch {
      setSaveStatus("Erreur lors de la réinitialisation");
    }
  }, [graph, onLayoutChanged, projectId, selectedEdgeId, visibleCouches]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (chartMode !== "edit") return;
      if (e.key === "Delete" || e.key === "Backspace") {
        if (activeWaypointIndex !== null) {
          e.preventDefault();
          deleteActiveWaypoint();
        }
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [activeWaypointIndex, chartMode, deleteActiveWaypoint]);

  const edgeEditValue = useMemo(
    () => ({
      editMode: chartMode === "edit",
      onWaypointDrag,
      onWaypointDragEnd,
      clientToFlow,
      activeWaypointIndex,
      setActiveWaypointIndex,
    }),
    [chartMode, onWaypointDrag, onWaypointDragEnd, clientToFlow, activeWaypointIndex]
  );

  const switchChartMode = (mode: ChartMode) => {
    setChartMode(mode);
    setSelectedEdgeId(null);
    setSelectedNodeIds([]);
    setActiveWaypointIndex(null);
    if (mode === "auto") {
      const flow = graphToFlow(graph, visibleCouches);
      setNodes(flow.nodes);
      setEdges(flow.edges);
    }
  };

  const toggleCouche = (id: CoucheId) => {
    setVisibleCouches((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        if (next.size > 1) next.delete(id);
      } else next.add(id);
      return next;
    });
  };

  const handleRelayout = useCallback(() => {
    setNodes((prev) => {
      const flow = graphToFlow(graph, visibleCouches);
      const manualPos = new Map(
        prev
          .filter((n) => n.type === "urbanism" && (n.data as UrbanismNodeData).layoutLocked)
          .map((n) => [n.id, n.position])
      );
      return flow.nodes.map((n) => {
        const manual = manualPos.get(n.id);
        if (manual && n.type === "urbanism") {
          return {
            ...n,
            position: manual,
            data: {
              ...(n.data as UrbanismNodeData),
              layoutMode: "manual",
              layoutLocked: true,
            },
          };
        }
        return n;
      });
    });
    requestAnimationFrame(() => fitView({ padding: FIT_VIEW_PADDING }));
  }, [graph, visibleCouches, fitView]);

  const handleDeduplicate = useCallback(async () => {
    setDeduplicating(true);
    try {
      const result = await deduplicateUrbanism(projectId);
      onAnalysisUpdated?.(result.analysis);
      onLayoutChanged?.();
    } catch {
      setSaveStatus("Erreur fusion doublons");
      setTimeout(() => setSaveStatus(null), 2500);
    } finally {
      setDeduplicating(false);
    }
  }, [onAnalysisUpdated, onLayoutChanged, projectId]);

  const captureMap = useCallback(async () => {
    const viewport = flowRef.current?.querySelector(".react-flow__viewport") as HTMLElement | null;
    if (!viewport) throw new Error("Viewport introuvable");
    return toPng(viewport, { backgroundColor: "#0a0e17", pixelRatio: 2 });
  }, []);

  const handleExportPng = useCallback(async () => {
    const dataUrl = await captureMap();
    const link = document.createElement("a");
    link.download = `cartographie-${graph.project_name.replace(/\s+/g, "-").toLowerCase()}.png`;
    link.href = dataUrl;
    link.click();
  }, [captureMap, graph.project_name]);

  const handleExportPdf = useCallback(async () => {
    const dataUrl = await captureMap();
    await exportUrbanismPdf(graph, dataUrl, author);
  }, [captureMap, graph, author]);

  const isEmpty = graph.stats.total_objects === 0;
  const editMode = chartMode === "edit";

  return (
    <div className="urbanism-map-stack">
      <UrbanismRibbon
        projects={projects}
        selectedProjectId={selectedProjectId}
        onProjectChange={onProjectChange}
        expertMode={expertMode}
        onExpertModeChange={onExpertModeChange}
        chartMode={chartMode}
        onChartModeChange={switchChartMode}
        onRelayout={handleRelayout}
        onAlignH={alignHorizontal}
        onAlignV={alignVertical}
        onDistributeH={distributeHorizontal}
        onDistributeV={distributeVertical}
        onCenter={centerInLayer}
        alignDisabled={{
          h: !editMode || selectedUrbanismNodes.length < 2,
          v: !editMode || selectedUrbanismNodes.length < 2,
          dh: !editMode || selectedUrbanismNodes.length < 3,
          dv: !editMode || selectedUrbanismNodes.length < 3,
          center: !editMode || selectedUrbanismNodes.length < 1,
        }}
        onExportPng={() => void handleExportPng()}
        onExportPdf={() => void handleExportPdf()}
        exportDisabled={isEmpty}
        author={author}
        onAuthorChange={setAuthor}
        onDeduplicate={() => void handleDeduplicate()}
        deduplicateDisabled={isEmpty}
        deduplicating={deduplicating}
        showResetEdge={editMode && Boolean(selectedEdgeId)}
        showResetNodes={editMode && selectedNodeIds.length > 0}
        onResetEdge={() => void resetSelectedEdgeLayout()}
        onResetNodes={() => void resetSelectedNodesLayout()}
        saveStatus={saveStatus}
      />

      <div className={`ua-mode-bar ${editMode ? "ua-mode-bar-edit" : "ua-mode-bar-auto"}`}>
        <strong>{editMode ? "Mode édition" : "Mode automatique"}</strong>
        <span>
          {editMode
            ? "Déplacez les objets et les liens. Toutes les modifications sont enregistrées automatiquement."
            : "Les positions sont calculées automatiquement."}
        </span>
      </div>

      <div className="ua-filter-strip">
        <span className="ua-filter-strip-label">Relations</span>
        {RELATION_FILTER_OPTIONS.map((opt) => (
          <button
            key={opt.id}
            type="button"
            className={`filter-chip relation-filter-chip ${relationFilters.has(opt.id) ? "active" : ""}`}
            onClick={() => onToggleRelationFilter(opt.id)}
          >
            {opt.label}
          </button>
        ))}
        {relationFilters.size > 0 && (
          <button type="button" className="ua-btn" onClick={onClearRelationFilters}>
            Tout
          </button>
        )}
        {activeCategories && (
          <span className="ua-filter-active-badge">
            {[...activeCategories].map((c) => RELATION_FILTER_OPTIONS.find((o) => o.id === c)?.label).join(", ")}
          </span>
        )}
        <span className="ua-filter-strip-label" style={{ marginLeft: "0.35rem" }}>Couches</span>
        {graph.meta_layers.map((layer) => (
          <button
            key={layer.id}
            type="button"
            className={`filter-chip ${visibleCouches.has(layer.id as CoucheId) ? "active" : ""}`}
            style={{
              borderColor: layer.color,
              color: visibleCouches.has(layer.id as CoucheId) ? layer.color : "var(--text)",
              background: visibleCouches.has(layer.id as CoucheId) ? `${layer.color}22` : "var(--surface2)",
            }}
            onClick={() => toggleCouche(layer.id as CoucheId)}
          >
            {layer.label} ({layer.object_count})
          </button>
        ))}
      </div>

      {isEmpty && (
        <div className="ua-panel urbanism-empty-hint">
          Graphe vide — utilisez l&apos;assistant pour créer votre première cartographie.
        </div>
      )}

      <div className="urbanism-flow-wrapper club-urba-flow" ref={flowRef}>
        <svg style={{ position: "absolute", width: 0, height: 0 }}>
          <defs>
            <marker id="urbanism-arrow" markerWidth="12" markerHeight="12" refX="10" refY="6" orient="auto" markerUnits="strokeWidth">
              <path d="M0,0 L12,6 L0,12 Z" fill="#94a3b8" />
            </marker>
            <marker id="urbanism-arrow-accent" markerWidth="12" markerHeight="12" refX="10" refY="6" orient="auto" markerUnits="strokeWidth">
              <path d="M0,0 L12,6 L0,12 Z" fill="#00d4aa" />
            </marker>
          </defs>
        </svg>
        <EdgeEditContext.Provider value={edgeEditValue}>
          <ReactFlow
            nodes={nodes}
            edges={edges}
            nodeTypes={nodeTypes}
            edgeTypes={edgeTypes}
            nodesDraggable={editMode}
            nodesConnectable={false}
            elementsSelectable={editMode}
            edgesFocusable={editMode}
            fitView
            minZoom={0.08}
            maxZoom={2}
            onNodesChange={onNodesChange}
            onNodeDragStop={onNodeDragStop}
            onSelectionChange={onSelectionChange}
            onEdgeDoubleClick={onEdgeDoubleClick}
            proOptions={{ hideAttribution: true }}
          >
            <Background color="#2a3548" gap={24} />
            <Controls />
            <MiniMap
              nodeColor={(n) =>
                n.type === "layerBand" ? "#1a2234" : (n.data as { coucheColor?: string })?.coucheColor ?? "#64748b"
              }
              maskColor="rgba(10, 14, 23, 0.85)"
            />
          </ReactFlow>
        </EdgeEditContext.Provider>
      </div>

      <div className="ua-map-footer">
        <span>{graph.stats.visible_objects} objets</span>
        <span>{graph.stats.visible_relations} relations affichées</span>
        <span>{graph.stats.total_relations} relations totales</span>
      </div>
    </div>
  );
}

export default function UrbanismSchema() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedId, setSelectedId] = useState(searchParams.get("project") ?? "");
  const [graph, setGraph] = useState<UrbanismGraph | null>(null);
  const [loading, setLoading] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [graphKey, setGraphKey] = useState(0);
  const [relationFilters, setRelationFilters] = useState<Set<RelationCategory>>(new Set());
  const [expertMode, setExpertMode] = useState(false);
  const [liveAnalysis, setLiveAnalysis] = useState<UrbanismAnalysis | null>(null);

  const refreshGraph = useCallback(() => {
    if (!selectedId) return;
    const cats = relationFilters.size > 0 ? [...relationFilters] : undefined;
    getUrbanismGraph(selectedId, cats)
      .then((g) => {
        setGraph(g);
        setLiveAnalysis(g.analysis);
      })
      .catch((e) => setLoadError(e instanceof Error ? e.message : "Erreur"));
    setGraphKey((k) => k + 1);
  }, [selectedId, relationFilters]);

  const onAssistantSaved = useCallback(
    (analysis?: UrbanismAnalysis) => {
      if (analysis) setLiveAnalysis(analysis);
      refreshGraph();
    },
    [refreshGraph]
  );

  useEffect(() => {
    listProjects().then((list) => {
      setProjects(list);
      const fromUrl = searchParams.get("project");
      if (fromUrl && list.some((p) => p.id === fromUrl)) setSelectedId(fromUrl);
      else if (!selectedId && list.length) setSelectedId(list[0].id);
    });
  }, [searchParams]);

  useEffect(() => {
    if (!selectedId) return;
    setLoading(true);
    setLoadError(null);
    const cats = relationFilters.size > 0 ? [...relationFilters] : undefined;
    getUrbanismGraph(selectedId, cats)
      .then((g) => {
        setGraph(g);
        setLiveAnalysis(g.analysis);
      })
      .catch((e) => setLoadError(e instanceof Error ? e.message : "Erreur"))
      .finally(() => setLoading(false));
  }, [selectedId, relationFilters, graphKey]);

  const toggleRelationFilter = (id: RelationCategory) => {
    setRelationFilters((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  return (
    <div className="urbanism-workspace">
      {loadError && <div className="ua-panel ua-error">{loadError}</div>}

      {selectedId && (
        <div className="urbanism-workspace-body">
          {expertMode ? (
            <UrbanismEngineEditor projectId={selectedId} onSaved={refreshGraph} />
          ) : (
            <UrbanismAssistant
              projectId={selectedId}
              onSaved={onAssistantSaved}
              liveAnalysis={liveAnalysis}
              hideDeduplicateButton
            />
          )}
          <div className="urbanism-map-panel">
            {loading && <div className="ua-panel">Génération de la cartographie…</div>}
            {!loading && graph && (
              <ReactFlowProvider key={`${selectedId}-${graphKey}`}>
                <SchemaCanvas
                  graph={graph}
                  projectId={selectedId}
                  projects={projects}
                  selectedProjectId={selectedId}
                  onProjectChange={(id) => {
                    setSelectedId(id);
                    setSearchParams(id ? { project: id } : {});
                  }}
                  expertMode={expertMode}
                  onExpertModeChange={setExpertMode}
                  relationFilters={relationFilters}
                  onToggleRelationFilter={toggleRelationFilter}
                  onClearRelationFilters={() => setRelationFilters(new Set())}
                  activeCategories={relationFilters.size > 0 ? relationFilters : null}
                  onLayoutChanged={refreshGraph}
                  onAnalysisUpdated={setLiveAnalysis}
                />
              </ReactFlowProvider>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
