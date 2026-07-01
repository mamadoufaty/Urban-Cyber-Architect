"""Résolution Agent/IP Wazuh → Bien support Urbanisme (lecture seule)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.models.entities import UrbanismEntity, UrbanismRelation

TECHNICAL_TYPES = frozenset({"serveur", "poste_travail", "reseau", "site", "byod"})


@dataclass
class AssetResolution:
    urbanism_entity_id: str | None = None
    supporting_asset_label: str = ""
    urbanism_entity_label: str = ""
    urbanism_entity_type: str = ""
    agent_id: str = ""
    agent_name: str = ""
    agent_ip: str = ""
    match_method: str = ""
    confidence: float = 0.0
    organization: str = ""
    processus: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


def _norm(value: str) -> str:
    return str(value or "").strip().lower()


def _entity_ips(entity: UrbanismEntity) -> set[str]:
    props = entity.properties or {}
    ips: set[str] = set()
    for key in ("ip", "adresse_ip", "address", "hostname", "fqdn"):
        val = props.get(key)
        if val:
            ips.add(_norm(str(val)))
    return ips


def _label_match(a: str, b: str) -> bool:
    na, nb = _norm(a), _norm(b)
    if not na or not nb:
        return False
    return na == nb or na in nb or nb in na


def resolve_agent_to_asset(
    *,
    agent_id: str,
    agent_name: str,
    agent_ip: str,
    entities: list[UrbanismEntity],
    relations: list[UrbanismRelation],
    ebios_asset_labels: list[str] | None = None,
) -> AssetResolution:
    """Associe un agent Wazuh à une entité urbanisme technique."""
    result = AssetResolution(
        agent_id=agent_id,
        agent_name=agent_name,
        agent_ip=agent_ip,
    )
    technical = [e for e in entities if e.entity_type in TECHNICAL_TYPES]
    if not technical:
        return result

    entities_by_id = {str(e.id): e for e in entities}

    # 1 — Correspondance IP
    if agent_ip:
        ip_norm = _norm(agent_ip)
        for entity in technical:
            if ip_norm in _entity_ips(entity):
                return _finalize(result, entity, entities_by_id, relations, "ip", 0.95)

    # 2 — Correspondance exacte du nom d'agent
    for entity in technical:
        if _norm(agent_name) == _norm(entity.label):
            return _finalize(result, entity, entities_by_id, relations, "agent_name_exact", 0.9)

    # 3 — Correspondance partielle nom / label
    for entity in technical:
        if _label_match(agent_name, entity.label):
            return _finalize(result, entity, entities_by_id, relations, "agent_name_fuzzy", 0.75)

    # 4 — Label bien support EBIOS
    for label in ebios_asset_labels or []:
        if _label_match(agent_name, label) or (agent_ip and _label_match(agent_ip, label)):
            for entity in technical:
                if _label_match(label, entity.label):
                    return _finalize(result, entity, entities_by_id, relations, "ebios_asset_label", 0.7)
            result.supporting_asset_label = label
            result.match_method = "ebios_asset_label_only"
            result.confidence = 0.55
            return result

    return result


def _finalize(
    result: AssetResolution,
    entity: UrbanismEntity,
    entities_by_id: dict[str, UrbanismEntity],
    relations: list[UrbanismRelation],
    method: str,
    confidence: float,
) -> AssetResolution:
    result.urbanism_entity_id = str(entity.id)
    result.urbanism_entity_label = entity.label
    result.urbanism_entity_type = entity.entity_type
    result.supporting_asset_label = entity.label
    result.match_method = method
    result.confidence = confidence
    result.organization = _find_nearby_label(entity.id, entities_by_id, relations, "organisation")
    result.processus = _find_nearby_label(entity.id, entities_by_id, relations, "processus")
    return result


def _find_nearby_label(
    start_id: str,
    entities_by_id: dict[str, UrbanismEntity],
    relations: list[UrbanismRelation],
    entity_type: str,
    *,
    max_depth: int = 5,
) -> str:
    visited = {str(start_id)}
    frontier = [str(start_id)]
    for _ in range(max_depth):
        next_frontier: list[str] = []
        for node_id in frontier:
            for rel in relations:
                for cid in (str(rel.source_id), str(rel.target_id)):
                    if cid == node_id or cid in visited:
                        continue
                    visited.add(cid)
                    entity = entities_by_id.get(cid)
                    if entity and entity.entity_type == entity_type:
                        return entity.label
                    next_frontier.append(cid)
        frontier = next_frontier
    fallback = next((e.label for e in entities_by_id.values() if e.entity_type == entity_type), "")
    return fallback
