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
import { buildExportFilename, downloadTextFile, graphToCsvString, graphToJsonString } from "../components/urbanism/exportData";
import UrbanismRibbon from "../components/urbanism/UrbanismRibbon";
import CartographyBanner from "../components/urbanism/CartographyBanner";
import CreateCartographyModal from "../components/urbanism/CreateCartographyModal";
import NameCartographyModal from "../components/urbanism/NameCartographyModal";
import CartographyHistoryModal from "../components/urbanism/CartographyHistoryModal";
import {
  isCartographyEditable,
  isHistoricalVersionSelected,
  resolveDefaultCartographyId,
  resolveDefaultVersionId,
  type CartographyCreateInput,
} from "../components/urbanism/cartographySelect";
import { FIT_VIEW_PADDING, type ChartMode } from "../components/urbanism/urbanismTypes";
import "../styles/urbanism-beta.css";
import {
  RELATION_FILTER_OPTIONS,
  type RelationCategory,
  type UrbanismAnalysis,
  type UrbanismGraph,
} from "../components/urbanism/metamodel";
import {
  activateCartography,
  archiveCartography,
  clearEdgeLayout,
  clearEntityLayout,
  createCartography,
  createNewCartographyVersion,
  deduplicateUrbanism,
  duplicateCartography,
  getCartographyHistory,
  getUrbanismGraph,
  listCartographies,
  listCartographyVersions,
  listProjects,
  restoreCartographyVersion,
  saveEdgeLayout,
  saveEntityLayout,
  saveEntityLayoutsBulk,
  submitCartographyForValidation,
  unarchiveCartography,
  validateCartography as apiValidateCartography,
  type Cartography,
  type CartographyHistoryEntry,
  type CartographyVersion,
  type Project,
} from "../api";
import { useAuth } from "../context/AuthContext";

const nodeTypes = { urbanism: UrbanismNode, layerBand: LayerBandNode };
const edgeTypes = { urbanismEdge: UrbanismEdge };

function SchemaCanvas({
  graph,
  projectId,
  cartographyId,
  readOnly,
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
  onCartographyMetaChanged,
}: {
  graph: UrbanismGraph;
  projectId: string;
  cartographyId?: string;
  readOnly?: boolean;
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
  /** Rafraîchit juste les métadonnées (statut/version) du bandeau, sans recharger
   * le graphe — utilisé après un déplacement qui a pu déclencher une copie-sur-
   * écriture silencieuse côté serveur (version validée → nouveau brouillon). */
  onCartographyMetaChanged?: () => void;
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
        await saveEdgeLayout(projectId, edgeId, payload, cartographyId);
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
        onCartographyMetaChanged?.();
      } catch {
        setSaveStatus("Erreur d'enregistrement");
      }
    },
    [edges, projectId, cartographyId, onCartographyMetaChanged]
  );

  const persistNodeLayout = useCallback(
    async (entityId: string, position: { x: number; y: number }) => {
      try {
        await saveEntityLayout(projectId, entityId, position, cartographyId);
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
        onCartographyMetaChanged?.();
      } catch {
        setSaveStatus("Erreur d'enregistrement");
      }
    },
    [projectId, cartographyId, onCartographyMetaChanged]
  );

  const persistNodeLayoutsBulk = useCallback(
    async (updatedNodes: Node[]) => {
      const layouts = layoutsFromNodes(updatedNodes);
      if (!layouts.length) return;
      try {
        await saveEntityLayoutsBulk(projectId, layouts, cartographyId);
        setNodes((prev) => {
          const byId = new Map(updatedNodes.map((n) => [n.id, n]));
          return prev.map((n) => byId.get(n.id) ?? n);
        });
        setSaveStatus("Positions enregistrées");
        setTimeout(() => setSaveStatus(null), 2000);
        onCartographyMetaChanged?.();
      } catch {
        setSaveStatus("Erreur d'enregistrement");
      }
    },
    [projectId, cartographyId, onCartographyMetaChanged]
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
      await Promise.all(selectedNodeIds.map((id) => clearEntityLayout(projectId, id, cartographyId)));
      onLayoutChanged?.();
      setSelectedNodeIds([]);
      setSaveStatus("Position réinitialisée — placement automatique");
      setTimeout(() => setSaveStatus(null), 2500);
    } catch {
      setSaveStatus("Erreur lors de la réinitialisation");
    }
  }, [onLayoutChanged, projectId, cartographyId, selectedNodeIds]);

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
      await clearEdgeLayout(projectId, selectedEdgeId, cartographyId);
      onLayoutChanged?.();
      setSelectedEdgeId(null);
      setSaveStatus("Tracé réinitialisé — routage automatique");
      setTimeout(() => setSaveStatus(null), 2500);
    } catch {
      setSaveStatus("Erreur lors de la réinitialisation");
    }
  }, [graph, onLayoutChanged, projectId, cartographyId, selectedEdgeId, visibleCouches]);

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
      const result = await deduplicateUrbanism(projectId, cartographyId);
      onAnalysisUpdated?.(result.analysis);
      onLayoutChanged?.();
    } catch {
      setSaveStatus("Erreur fusion doublons");
      setTimeout(() => setSaveStatus(null), 2500);
    } finally {
      setDeduplicating(false);
    }
  }, [onAnalysisUpdated, onLayoutChanged, projectId, cartographyId]);

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

  const handleExportJson = useCallback(() => {
    downloadTextFile(buildExportFilename(graph, "json"), graphToJsonString(graph), "application/json");
  }, [graph]);

  const handleExportCsv = useCallback(() => {
    downloadTextFile(buildExportFilename(graph, "csv"), graphToCsvString(graph), "text/csv");
  }, [graph]);

  const isEmpty = graph.stats.total_objects === 0;
  const editMode = chartMode === "edit" && !readOnly;

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
        onExportJson={handleExportJson}
        onExportCsv={handleExportCsv}
        exportDisabled={isEmpty}
        author={author}
        onAuthorChange={setAuthor}
        onDeduplicate={() => void handleDeduplicate()}
        deduplicateDisabled={isEmpty || Boolean(readOnly)}
        deduplicating={deduplicating}
        showResetEdge={editMode && Boolean(selectedEdgeId)}
        showResetNodes={editMode && selectedNodeIds.length > 0}
        onResetEdge={() => void resetSelectedEdgeLayout()}
        onResetNodes={() => void resetSelectedNodesLayout()}
        saveStatus={saveStatus}
        readOnly={readOnly}
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
          Cette cartographie est vide. Commencez à créer vos premiers objets.
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
  const { user } = useAuth();
  const authorName = user?.displayName ?? undefined;
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

  const [cartographies, setCartographies] = useState<Cartography[]>([]);
  const [selectedCartographyId, setSelectedCartographyId] = useState<string | null>(
    searchParams.get("cartography")
  );
  const [versions, setVersions] = useState<CartographyVersion[]>([]);
  const [selectedVersionId, setSelectedVersionId] = useState<string | null>(null);
  const [cartographyBusy, setCartographyBusy] = useState(false);
  const [cartographyError, setCartographyError] = useState<string | null>(null);

  const [showCreateModal, setShowCreateModal] = useState(false);
  const [nameModal, setNameModal] = useState<"duplicate" | "save-as" | null>(null);
  const [showHistoryModal, setShowHistoryModal] = useState(false);
  const [historyEntries, setHistoryEntries] = useState<CartographyHistoryEntry[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [restoring, setRestoring] = useState(false);

  const currentCartography = useMemo(
    () => cartographies.find((c) => c.id === selectedCartographyId) ?? null,
    [cartographies, selectedCartographyId]
  );
  const isHistoricalVersion = useMemo(
    () => isHistoricalVersionSelected(versions, selectedVersionId),
    [versions, selectedVersionId]
  );
  const readOnly = isHistoricalVersion || !isCartographyEditable(currentCartography);

  const reloadCartographies = useCallback(
    async (opts?: { preferredId?: string }) => {
      if (!selectedId) {
        setCartographies([]);
        setSelectedCartographyId(null);
        return;
      }
      try {
        const res = await listCartographies(selectedId);
        setCartographies(res.items);
        setSelectedCartographyId((prev) => opts?.preferredId ?? resolveDefaultCartographyId(res.items, prev));
      } catch (e) {
        setCartographyError(e instanceof Error ? e.message : "Erreur de chargement des cartographies");
      }
    },
    [selectedId]
  );

  const reloadVersions = useCallback(async (cartographyId: string) => {
    try {
      const res = await listCartographyVersions(cartographyId);
      setVersions(res.items);
      setSelectedVersionId(resolveDefaultVersionId(res.items, null));
    } catch (e) {
      setCartographyError(e instanceof Error ? e.message : "Erreur de chargement des versions");
    }
  }, []);

  const refreshGraph = useCallback(() => {
    if (!selectedId) return;
    const cats = relationFilters.size > 0 ? [...relationFilters] : undefined;
    const versionParam = isHistoricalVersion ? selectedVersionId ?? undefined : undefined;
    getUrbanismGraph(selectedId, cats, selectedCartographyId ?? undefined, versionParam)
      .then((g) => {
        setGraph(g);
        setLiveAnalysis(g.analysis);
      })
      .catch((e) => setLoadError(e instanceof Error ? e.message : "Erreur"));
    setGraphKey((k) => k + 1);
  }, [selectedId, relationFilters, selectedCartographyId, selectedVersionId, isHistoricalVersion]);

  const onGraphMutated = useCallback(
    (analysis?: UrbanismAnalysis) => {
      if (analysis) setLiveAnalysis(analysis);
      refreshGraph();
      if (selectedCartographyId) {
        void reloadCartographies({ preferredId: selectedCartographyId });
        void reloadVersions(selectedCartographyId);
      }
    },
    [refreshGraph, selectedCartographyId, reloadCartographies, reloadVersions]
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
    reloadCartographies();
  }, [reloadCartographies]);

  useEffect(() => {
    if (!selectedCartographyId) {
      setVersions([]);
      setSelectedVersionId(null);
      return;
    }
    reloadVersions(selectedCartographyId);
  }, [selectedCartographyId, reloadVersions]);

  useEffect(() => {
    if (!selectedId) return;
    setLoading(true);
    setLoadError(null);
    const cats = relationFilters.size > 0 ? [...relationFilters] : undefined;
    const versionParam = isHistoricalVersion ? selectedVersionId ?? undefined : undefined;
    getUrbanismGraph(selectedId, cats, selectedCartographyId ?? undefined, versionParam)
      .then((g) => {
        setGraph(g);
        setLiveAnalysis(g.analysis);
      })
      .catch((e) => setLoadError(e instanceof Error ? e.message : "Erreur"))
      .finally(() => setLoading(false));
  }, [selectedId, relationFilters, graphKey, selectedCartographyId, selectedVersionId, isHistoricalVersion]);

  const toggleRelationFilter = (id: RelationCategory) => {
    setRelationFilters((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  function handleProjectChange(id: string) {
    setSelectedId(id);
    setSelectedCartographyId(null);
    setSearchParams(id ? { project: id } : {});
  }

  function handleCartographyChange(id: string) {
    setSelectedCartographyId(id);
    if (id) void activateCartography(id).catch(() => undefined);
  }

  async function handleCreateCartography(values: CartographyCreateInput) {
    if (!selectedId) return;
    setCartographyBusy(true);
    setCartographyError(null);
    try {
      const created = await createCartography(selectedId, {
        name: values.name,
        type: values.type,
        description: values.description || null,
        author: authorName,
      });
      await reloadCartographies({ preferredId: created.id });
      setShowCreateModal(false);
    } catch (e) {
      setCartographyError(e instanceof Error ? e.message : "Erreur de création de la cartographie");
    } finally {
      setCartographyBusy(false);
    }
  }

  async function handleNameModalSubmit(name: string) {
    if (!currentCartography) return;
    setCartographyBusy(true);
    setCartographyError(null);
    try {
      const clone = await duplicateCartography(currentCartography.id, name, authorName);
      await reloadCartographies({ preferredId: clone.id });
      setNameModal(null);
    } catch (e) {
      setCartographyError(e instanceof Error ? e.message : "Erreur de duplication");
    } finally {
      setCartographyBusy(false);
    }
  }

  async function handleNewVersion() {
    if (!currentCartography) return;
    setCartographyBusy(true);
    setCartographyError(null);
    try {
      await createNewCartographyVersion(currentCartography.id, authorName);
      await reloadCartographies({ preferredId: currentCartography.id });
      await reloadVersions(currentCartography.id);
    } catch (e) {
      setCartographyError(e instanceof Error ? e.message : "Erreur de création de version");
    } finally {
      setCartographyBusy(false);
    }
  }

  async function handleSubmitForValidation() {
    if (!currentCartography) return;
    setCartographyBusy(true);
    try {
      await submitCartographyForValidation(currentCartography.id, authorName);
      await reloadCartographies({ preferredId: currentCartography.id });
      await reloadVersions(currentCartography.id);
    } catch (e) {
      setCartographyError(e instanceof Error ? e.message : "Erreur de soumission");
    } finally {
      setCartographyBusy(false);
    }
  }

  async function handleValidate() {
    if (!currentCartography) return;
    setCartographyBusy(true);
    try {
      await apiValidateCartography(currentCartography.id, { validated_by: authorName });
      await reloadCartographies({ preferredId: currentCartography.id });
      await reloadVersions(currentCartography.id);
    } catch (e) {
      setCartographyError(e instanceof Error ? e.message : "Erreur de validation");
    } finally {
      setCartographyBusy(false);
    }
  }

  async function handleArchiveToggle() {
    if (!currentCartography) return;
    setCartographyBusy(true);
    try {
      if (currentCartography.is_archived) {
        await unarchiveCartography(currentCartography.id, authorName);
      } else {
        await archiveCartography(currentCartography.id, authorName);
      }
      await reloadCartographies({ preferredId: currentCartography.id });
      await reloadVersions(currentCartography.id);
    } catch (e) {
      setCartographyError(e instanceof Error ? e.message : "Erreur d'archivage");
    } finally {
      setCartographyBusy(false);
    }
  }

  async function handleOpenHistory() {
    if (!currentCartography) return;
    setShowHistoryModal(true);
    setHistoryLoading(true);
    try {
      const [historyRes, versionsRes] = await Promise.all([
        getCartographyHistory(currentCartography.id),
        listCartographyVersions(currentCartography.id),
      ]);
      setHistoryEntries(historyRes.items);
      setVersions(versionsRes.items);
    } catch (e) {
      setCartographyError(e instanceof Error ? e.message : "Erreur de chargement de l'historique");
    } finally {
      setHistoryLoading(false);
    }
  }

  async function handleRestore(versionId: string) {
    if (!currentCartography) return;
    setRestoring(true);
    try {
      await restoreCartographyVersion(currentCartography.id, versionId, authorName);
      await reloadCartographies({ preferredId: currentCartography.id });
      await reloadVersions(currentCartography.id);
      setShowHistoryModal(false);
    } catch (e) {
      setCartographyError(e instanceof Error ? e.message : "Erreur de restauration");
    } finally {
      setRestoring(false);
    }
  }

  return (
    <div className="urbanism-workspace">
      {loadError && <div className="ua-panel ua-error">{loadError}</div>}
      {cartographyError && (
        <div className="ua-panel ua-error" role="alert">
          {cartographyError}
        </div>
      )}

      {selectedId && (
        <>
          <CartographyBanner
            projects={projects}
            selectedProjectId={selectedId}
            onProjectChange={handleProjectChange}
            cartographies={cartographies}
            selectedCartographyId={selectedCartographyId}
            onCartographyChange={handleCartographyChange}
            versions={versions}
            selectedVersionId={selectedVersionId}
            onVersionChange={setSelectedVersionId}
            currentCartography={currentCartography}
            isHistoricalVersion={isHistoricalVersion}
            canManage
            busy={cartographyBusy}
            onNewCartography={() => setShowCreateModal(true)}
            onSaveAs={() => setNameModal("save-as")}
            onDuplicate={() => setNameModal("duplicate")}
            onNewVersion={() => void handleNewVersion()}
            onOpenHistory={() => void handleOpenHistory()}
            onSubmitForValidation={() => void handleSubmitForValidation()}
            onValidate={() => void handleValidate()}
            onArchiveToggle={() => void handleArchiveToggle()}
          />

          <div className="urbanism-workspace-body">
            {expertMode ? (
              <UrbanismEngineEditor
                projectId={selectedId}
                cartographyId={selectedCartographyId ?? undefined}
                readOnly={readOnly}
                onSaved={() => onGraphMutated()}
              />
            ) : (
              <UrbanismAssistant
                projectId={selectedId}
                cartographyId={selectedCartographyId ?? undefined}
                readOnly={readOnly}
                onSaved={onGraphMutated}
                liveAnalysis={liveAnalysis}
                hideDeduplicateButton
              />
            )}
            <div className="urbanism-map-panel">
              {loading && <div className="ua-panel">Génération de la cartographie…</div>}
              {!loading && graph && (
                <ReactFlowProvider key={`${selectedId}-${selectedCartographyId}-${selectedVersionId}-${graphKey}`}>
                  <SchemaCanvas
                    graph={graph}
                    projectId={selectedId}
                    cartographyId={selectedCartographyId ?? undefined}
                    readOnly={readOnly}
                    projects={projects}
                    selectedProjectId={selectedId}
                    onProjectChange={handleProjectChange}
                    expertMode={expertMode}
                    onExpertModeChange={setExpertMode}
                    relationFilters={relationFilters}
                    onToggleRelationFilter={toggleRelationFilter}
                    onClearRelationFilters={() => setRelationFilters(new Set())}
                    activeCategories={relationFilters.size > 0 ? relationFilters : null}
                    onLayoutChanged={() => onGraphMutated()}
                    onAnalysisUpdated={setLiveAnalysis}
                    onCartographyMetaChanged={() => {
                      if (selectedCartographyId) {
                        void reloadCartographies({ preferredId: selectedCartographyId });
                        void reloadVersions(selectedCartographyId);
                      }
                    }}
                  />
                </ReactFlowProvider>
              )}
            </div>
          </div>
        </>
      )}

      <CreateCartographyModal
        open={showCreateModal}
        saving={cartographyBusy}
        error={cartographyError}
        onClose={() => setShowCreateModal(false)}
        onSubmit={(values) => void handleCreateCartography(values)}
      />

      <NameCartographyModal
        open={nameModal !== null}
        mode={nameModal ?? "duplicate"}
        sourceName={currentCartography?.name ?? ""}
        existingNames={cartographies.map((c) => c.name)}
        saving={cartographyBusy}
        error={cartographyError}
        onClose={() => setNameModal(null)}
        onSubmit={(name) => void handleNameModalSubmit(name)}
      />

      <CartographyHistoryModal
        open={showHistoryModal}
        cartographyName={currentCartography?.name ?? ""}
        history={historyEntries}
        versions={versions}
        loading={historyLoading}
        restoring={restoring}
        canRestore={!currentCartography?.is_archived}
        onClose={() => setShowHistoryModal(false)}
        onRestore={(versionId) => void handleRestore(versionId)}
      />
    </div>
  );
}
