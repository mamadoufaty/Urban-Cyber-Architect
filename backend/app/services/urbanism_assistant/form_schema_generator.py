"""Génération dynamique du formulaire de création assistée."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from app.metamodel.entity_profiles import ENTITY_PROFILES, get_entity_profile, CONDITIONAL_REQUIRED_RULE_IDS
from app.metamodel.urbanism import ENTITY_BY_ID, RULE_BY_ID
from app.models.entities import UrbanismEntity, UrbanismRelation

# Champs assistant hors métamodèle R01–R30 (liens dérivés / propriétés)
VIRTUAL_ASSISTANT_FIELDS: dict[str, list[dict[str, Any]]] = {
    "ilot_applicatif": [
        {
            "field_id": "virtual_linked_ilot_fonctionnel",
            "rule_id": "virtual",
            "label": "Sélectionnez l'Îlot fonctionnel",
            "relation_type": "",
            "peer_type": "ilot_fonctionnel",
            "direction": "incoming",
            "widget": "select",
        },
    ],
}


def _connected_entity_ids(relations: list[UrbanismRelation]) -> set[UUID]:
    connected: set[UUID] = set()
    for r in relations:
        connected.add(r.source_id)
        connected.add(r.target_id)
    return connected


def _peer_candidates(
    entities: list[UrbanismEntity],
    relations: list[UrbanismRelation],
    peer_type: str,
) -> list[UrbanismEntity]:
    """Candidats pour les listes déroulantes — masque les doublons orphelins si une entité reliée existe."""
    peers = [e for e in entities if e.entity_type == peer_type]
    connected = _connected_entity_ids(relations)

    connected_peers = [p for p in peers if p.id in connected]
    labels_with_connection = {p.label for p in connected_peers}

    orphan_peers: list[UrbanismEntity] = []
    seen_orphan_labels: set[str] = set()
    for p in peers:
        if p.id in connected:
            continue
        if p.label in labels_with_connection:
            continue
        if p.label in seen_orphan_labels:
            continue
        orphan_peers.append(p)
        seen_orphan_labels.add(p.label)

    return sorted(connected_peers + orphan_peers, key=lambda e: e.label.lower())


def _count_existing_for_field(
    field: dict[str, Any],
    entity_id: UUID,
    relations: list[UrbanismRelation],
    *,
    as_source: bool,
) -> int:
    rule = RULE_BY_ID[field["rule_id"]]
    count = 0
    for rel in relations:
        if rel.relation_type != rule["type"]:
            continue
        if as_source and rel.source_id == entity_id:
            count += 1
        elif not as_source and rel.target_id == entity_id:
            count += 1
    return count


def _peer_saturated(
    field: dict[str, Any],
    peer: UrbanismEntity,
    relations: list[UrbanismRelation],
) -> bool:
    """Vrai si le pair ne peut plus accepter de relation pour cette règle (max côté pair)."""
    rule = RULE_BY_ID[field["rule_id"]]
    max_card = field["cardinality"]["max"]
    if max_card is None:
        return False

    if field["direction"] == "incoming":
        # peer est source
        count = sum(
            1 for r in relations
            if r.source_id == peer.id and r.relation_type == rule["type"]
        )
        effective_max = max_card
        if effective_max is not None:
            return count >= effective_max
    # outgoing: peer est cible — rarement saturé pour max=1 sur new entity side
    return False


def generate_form_schema(
    entity_type: str,
    entities: list[UrbanismEntity],
    relations: list[UrbanismRelation],
) -> dict[str, Any]:
    profile = get_entity_profile(entity_type)
    if not profile:
        raise ValueError(f"Type d'entité inconnu: {entity_type}")

    meta = ENTITY_BY_ID.get(entity_type, {})
    fields_out: list[dict[str, Any]] = []
    schema_required_ids: set[str] = set()

    for field in profile["fields"]:
        peers = _peer_candidates(entities, relations, field["peer_type"])
        options = [
            {"entity_id": str(p.id), "label": p.label, "entity_type": p.entity_type}
            for p in peers
            if not _peer_saturated(field, p, relations)
        ]

        if not options:
            continue

        is_required = field["required"] or field["rule_id"] in CONDITIONAL_REQUIRED_RULE_IDS.get(entity_type, frozenset())
        selected: list[str] = []
        if is_required and len(options) == 1 and field["widget"] == "select":
            selected = [options[0]["entity_id"]]

        if is_required:
            schema_required_ids.add(field["field_id"])

        fields_out.append({
            **field,
            "required": is_required,
            "options": options,
            "selected": selected,
            "visible": True,
        })

    for vfield in VIRTUAL_ASSISTANT_FIELDS.get(entity_type, []):
        peers = _peer_candidates(entities, relations, vfield["peer_type"])
        if not peers:
            continue
        options = [
            {"entity_id": str(p.id), "label": p.label, "entity_type": p.entity_type}
            for p in peers
        ]
        is_required = True
        selected: list[str] = []
        if len(options) == 1:
            selected = [options[0]["entity_id"]]
        schema_required_ids.add(vfield["field_id"])
        fields_out.insert(0, {
            **vfield,
            "required": is_required,
            "cardinality": {"min": 1, "max": 1},
            "options": options,
            "selected": selected,
            "visible": True,
        })

    return {
        "entity_type": entity_type,
        "entity_label": profile["entity_label"],
        "label_field": {
            "placeholder": f"Nom du {meta.get('label', entity_type).lower()}",
            "required": True,
        },
        "fields": fields_out,
        "required_field_ids": sorted(schema_required_ids),
        "hints": profile["hints"],
        "creation_order": profile["creation_order"],
    }
