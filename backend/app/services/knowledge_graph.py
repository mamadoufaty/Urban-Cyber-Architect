"""Knowledge Graph service — builds project graph from validated decisions."""

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import GraphEdge, GraphNode


RELATION_CHAIN = [
    ("objectif", "metier", "supports"),
    ("metier", "processus", "executes"),
    ("processus", "application", "uses"),
    ("application", "composant", "contains"),
    ("actif", "risque", "exposes"),
    ("risque", "mesure", "mitigated_by"),
    ("mesure", "architecture", "implements"),
    ("architecture", "livrable", "produces"),
]


class KnowledgeGraphService:
    async def build_from_decision(
        self, session: AsyncSession, project_id: uuid.UUID, content: dict[str, Any]
    ) -> dict[str, Any]:
        nodes_created: list[GraphNode] = []

        mappings = [
            ("objectif", content.get("objectifs_pris_en_compte", [])),
            ("processus", content.get("processus_critiques", [])),
            ("actif", content.get("actifs_critiques", [])),
            ("risque", [s.get("nom", str(s)) for s in content.get("scenarios_ebios", []) if isinstance(s, dict)]),
            ("architecture", list(content.get("architecture_cible", {}).keys()) if isinstance(content.get("architecture_cible"), dict) else []),
        ]

        type_nodes: dict[str, list[GraphNode]] = {}
        for node_type, items in mappings:
            type_nodes[node_type] = []
            for item in items:
                if not item:
                    continue
                node = GraphNode(
                    project_id=project_id,
                    node_type=node_type,
                    label=str(item),
                    properties={"source": "ai_decision"},
                )
                session.add(node)
                type_nodes[node_type].append(node)
                nodes_created.append(node)

        await session.flush()

        edges = [
            (type_nodes.get("objectif", []), type_nodes.get("processus", []), "drives"),
            (type_nodes.get("processus", []), type_nodes.get("actif", []), "depends_on"),
            (type_nodes.get("actif", []), type_nodes.get("risque", []), "exposes"),
            (type_nodes.get("risque", []), type_nodes.get("architecture", []), "mitigated_by"),
        ]

        for sources, targets, relation in edges:
            for src in sources:
                for tgt in targets:
                    session.add(
                        GraphEdge(
                            project_id=project_id,
                            source_id=src.id,
                            target_id=tgt.id,
                            relation=relation,
                        )
                    )

        return {"nodes": len(nodes_created), "edges": sum(len(s) * len(t) for s, t, _ in edges)}

    async def get_graph(self, session: AsyncSession, project_id: uuid.UUID) -> dict[str, Any]:
        nodes_result = await session.execute(
            select(GraphNode).where(GraphNode.project_id == project_id)
        )
        nodes = nodes_result.scalars().all()

        edges_result = await session.execute(
            select(GraphEdge).where(GraphEdge.project_id == project_id)
        )
        edges = edges_result.scalars().all()

        return {
            "nodes": [
                {"id": str(n.id), "type": n.node_type, "label": n.label, "properties": n.properties}
                for n in nodes
            ],
            "edges": [
                {"id": str(e.id), "source": str(e.source_id), "target": str(e.target_id), "relation": e.relation}
                for e in edges
            ],
        }
