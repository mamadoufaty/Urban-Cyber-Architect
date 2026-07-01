"""Club Urba simplified urbanism cartography — multi-layer schema from SQLite."""

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import Project

# (couche_id, couche_label, color, zones: [(zone_key, zone_label), ...])
CLUB_URBA_COUCHES: list[dict[str, Any]] = [
    {
        "id": "metier",
        "label": "Couche Métier",
        "color": "#00d4aa",
        "zones": [
            ("objectifs", "Objectifs"),
            ("processus", "Processus"),
            ("activites", "Activités"),
            ("resultats", "Résultats"),
        ],
    },
    {
        "id": "organisation",
        "label": "Couche Organisation",
        "color": "#3b82f6",
        "zones": [
            ("organisation", "Organisation"),
            ("procedures", "Procédures"),
            ("operations", "Opérations"),
            ("acteurs", "Acteurs"),
        ],
    },
    {
        "id": "fonctionnel",
        "label": "Couche Fonctionnelle",
        "color": "#8b5cf6",
        "zones": [
            ("ilots", "Îlots fonctionnels"),
            ("quartiers", "Quartiers fonctionnels"),
            ("zones", "Zones fonctionnelles"),
        ],
    },
    {
        "id": "applicatif",
        "label": "Couche Applicative",
        "color": "#f59e0b",
        "zones": [
            ("ilots", "Îlots applicatifs"),
            ("quartiers", "Quartiers applicatifs"),
            ("zones", "Zones applicatives"),
        ],
    },
    {
        "id": "technique",
        "label": "Couche Technique",
        "color": "#06b6d4",
        "zones": [
            ("postes", "Postes de travail"),
            ("serveurs", "Serveurs"),
            ("reseaux", "Réseaux"),
            ("sites", "Sites"),
        ],
    },
]

INTRA_COUCH_RELATIONS = {
  ("objectifs", "processus"): "pilote",
  ("processus", "activites"): "déploie",
  ("activites", "resultats"): "produit",
  ("organisation", "procedures"): "encadre",
  ("procedures", "operations"): "oriente",
  ("operations", "acteurs"): "mobilise",
  ("ilots", "quartiers"): "regroupe",
  ("quartiers", "zones"): "structure",
  ("postes", "serveurs"): "accède à",
  ("serveurs", "reseaux"): "connecte",
  ("reseaux", "sites"): "héberge",
}

INTER_COUCH_RELATIONS = {
  ("metier", "organisation"): "s'organise en",
  ("organisation", "fonctionnel"): "se traduit en",
  ("fonctionnel", "applicatif"): "est porté par",
  ("applicatif", "technique"): "s'appuie sur",
}


def _empty_club_urba() -> dict[str, dict[str, list[str]]]:
    return {
        couche["id"]: {zone_key: [] for zone_key, _ in couche["zones"]}
        for couche in CLUB_URBA_COUCHES
    }


def normalize_club_urba(project: Project) -> dict[str, dict[str, list[str]]]:
    """Merge club_urba structure with legacy urbanism keys."""
    urbanism = project.urbanism or {}
    data = _empty_club_urba()

    club = urbanism.get("club_urba")
    if isinstance(club, dict):
        for couche_id, zones in club.items():
            if couche_id not in data or not isinstance(zones, dict):
                continue
            for zone_key, items in zones.items():
                if zone_key in data[couche_id] and isinstance(items, list):
                    data[couche_id][zone_key] = [str(i).strip() for i in items if str(i).strip()]

    # Rétrocompatibilité : anciens projets avec clés plates (sans écraser club_urba saisi)
    legacy_map: list[tuple[str, str, str]] = [
        ("metier", "objectifs", "objectifs"),
        ("metier", "processus", "processus"),
        ("metier", "activites", "metiers"),
        ("organisation", "acteurs", "metiers"),
        ("fonctionnel", "ilots", "fonctionnel"),
        ("applicatif", "ilots", "applicatif"),
        ("technique", "serveurs", "technique"),
    ]
    for couche_id, zone_key, legacy_key in legacy_map:
        if data[couche_id][zone_key]:
            continue
        if legacy_key not in urbanism:
            continue
        for item in urbanism.get(legacy_key, []):
            label = str(item).strip()
            if label:
                data[couche_id][zone_key].append(label)

    return data


def build_urbanism_schema(project: Project) -> dict[str, Any]:
    club_data = normalize_club_urba(project)
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    zone_node_map: dict[tuple[str, str], list[str]] = {}
    couche_zone_counts: dict[str, dict[str, int]] = {}

    for couche in CLUB_URBA_COUCHES:
        couche_id = couche["id"]
        couche_zone_counts[couche_id] = {}
        for zone_key, zone_label in couche["zones"]:
            items = club_data[couche_id].get(zone_key, [])
            couche_zone_counts[couche_id][zone_key] = len(items)
            ids: list[str] = []
            for index, label in enumerate(items):
                node_id = f"{couche_id}-{zone_key}-{index}"
                ids.append(node_id)
                nodes.append(
                    {
                        "id": node_id,
                        "type": "urbanism",
                        "couche": couche_id,
                        "couche_label": couche["label"],
                        "couche_color": couche["color"],
                        "zone": zone_key,
                        "zone_label": zone_label,
                        "label": label,
                    }
                )
            zone_node_map[(couche_id, zone_key)] = ids

    for couche in CLUB_URBA_COUCHES:
        couche_id = couche["id"]
        zones = couche["zones"]
        for i in range(len(zones) - 1):
            src_key, _ = zones[i]
            tgt_key, _ = zones[i + 1]
            sources = zone_node_map.get((couche_id, src_key), [])
            targets = zone_node_map.get((couche_id, tgt_key), [])
            if not sources or not targets:
                continue
            relation = INTRA_COUCH_RELATIONS.get((src_key, tgt_key), "relie")
            for source_id in sources:
                for target_id in targets:
                    edges.append(
                        {
                            "id": f"{source_id}--{target_id}",
                            "source": source_id,
                            "target": target_id,
                            "relation": relation,
                            "couche": couche_id,
                        }
                    )

    for i in range(len(CLUB_URBA_COUCHES) - 1):
        src_couche = CLUB_URBA_COUCHES[i]
        tgt_couche = CLUB_URBA_COUCHES[i + 1]
        src_zone = src_couche["zones"][-1][0]
        tgt_zone = tgt_couche["zones"][0][0]
        sources = zone_node_map.get((src_couche["id"], src_zone), [])
        targets = zone_node_map.get((tgt_couche["id"], tgt_zone), [])
        if not sources or not targets:
            continue
        relation = INTER_COUCH_RELATIONS.get((src_couche["id"], tgt_couche["id"]), "décline en")
        for source_id in sources:
            for target_id in targets:
                edges.append(
                    {
                        "id": f"inter-{source_id}--{target_id}",
                        "source": source_id,
                        "target": target_id,
                        "relation": relation,
                        "couche": f"{src_couche['id']}-{tgt_couche['id']}",
                    }
                )

    org = project.organization or {}
    by_couche = {c["id"]: sum(couche_zone_counts[c["id"]].values()) for c in CLUB_URBA_COUCHES}

    meta_layers = []
    for couche in CLUB_URBA_COUCHES:
        cid = couche["id"]
        meta_layers.append(
            {
                "id": cid,
                "label": couche["label"],
                "color": couche["color"],
                "object_count": by_couche[cid],
                "zones": [
                    {
                        "key": zk,
                        "label": zl,
                        "count": couche_zone_counts[cid][zk],
                    }
                    for zk, zl in couche["zones"]
                ],
            }
        )

    return {
        "project_id": str(project.id),
        "project_name": project.name,
        "organization": org,
        "author": org.get("author") or org.get("name") or "Urban Cyber Architect",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "model": "club_urba",
        "nodes": nodes,
        "edges": edges,
        "meta_layers": meta_layers,
        "stats": {
            "total_objects": len(nodes),
            "total_relations": len(edges),
            "by_couche": by_couche,
        },
    }


async def get_project_urbanism_schema(session: AsyncSession, project_id: UUID) -> dict[str, Any] | None:
    project = await session.get(Project, project_id)
    if not project:
        return None
    return build_urbanism_schema(project)
