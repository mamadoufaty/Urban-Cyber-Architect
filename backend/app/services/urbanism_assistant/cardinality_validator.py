"""Validation des cardinalités et doublons pour l'assistant d'urbanisme."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from app.metamodel.entity_profiles import get_profile_field
from app.services.urbanism_assistant.form_schema_generator import VIRTUAL_ASSISTANT_FIELDS
from app.metamodel.urbanism import RULE_BY_ID, validate_relation
from app.models.entities import UrbanismEntity, UrbanismRelation


@dataclass
class ValidationError:
    code: str
    message: str
    field_id: str | None = None


def _relation_key(source_id: UUID, relation_type: str, target_id: UUID) -> tuple[UUID, str, UUID]:
    return (source_id, relation_type, target_id)


def count_bindings_for_field(
    field: dict[str, Any],
    new_entity_id: UUID | None,
    relations: list[UrbanismRelation],
    peer_ids: list[UUID],
) -> int:
    """Compte les relations existantes + nouvelles pour une règle côté entité créée."""
    rule = RULE_BY_ID[field["rule_id"]]
    count = len(peer_ids)

    for rel in relations:
        if rel.relation_type != rule["type"]:
            continue
        if field["direction"] == "outgoing" and new_entity_id and rel.source_id == new_entity_id:
            if rel.target_id not in peer_ids:
                count += 1
        elif field["direction"] == "incoming" and new_entity_id and rel.target_id == new_entity_id:
            if rel.source_id not in peer_ids:
                count += 1
    return count


def _is_virtual_field(field_id: str) -> bool:
    return field_id.startswith("virtual_")


def split_bindings(
    bindings: dict[str, list[str]],
) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    """Sépare liaisons métamodèle (R01–R30) et champs virtuels assistant."""
    metamodel: dict[str, list[str]] = {}
    virtual: dict[str, list[str]] = {}
    for field_id, peer_ids in bindings.items():
        if _is_virtual_field(field_id):
            virtual[field_id] = peer_ids
        else:
            metamodel[field_id] = peer_ids
    return metamodel, virtual


def validate_bindings(
    entity_type: str,
    bindings: dict[str, list[str]],
    entities: list[UrbanismEntity],
    relations: list[UrbanismRelation],
    new_entity_id: UUID | None = None,
    schema_field_ids: set[str] | None = None,
) -> list[ValidationError]:
    errors: list[ValidationError] = []
    entity_map = {e.id: e for e in entities}
    existing_keys = {_relation_key(r.source_id, r.relation_type, r.target_id) for r in relations}

    # Champs requis présents dans le schéma doivent avoir une valeur
    if schema_field_ids:
        for field_id in schema_field_ids:
            if _is_virtual_field(field_id):
                continue
            field = get_profile_field(entity_type, field_id)
            if not field:
                continue
            selected = bindings.get(field_id, [])
            if not selected:
                errors.append(ValidationError(
                    "required_field_missing",
                    f"Le champ « {field['label']} » est obligatoire.",
                    field_id,
                ))

    for field_id, peer_id_strs in bindings.items():
        if _is_virtual_field(field_id):
            continue

        field = get_profile_field(entity_type, field_id)
        if not field:
            errors.append(ValidationError("unknown_field", f"Champ inconnu: {field_id}", field_id))
            continue

        rule = RULE_BY_ID[field["rule_id"]]
        peer_ids: list[UUID] = []
        for pid in peer_id_strs:
            try:
                peer_ids.append(UUID(pid))
            except ValueError:
                errors.append(ValidationError("invalid_id", f"Identifiant invalide: {pid}", field_id))
                continue

        if field["widget"] == "select" and len(peer_ids) > 1:
            errors.append(ValidationError(
                "cardinality_max",
                f"Une seule valeur autorisée pour « {field['label']} ».",
                field_id,
            ))

        cardinality = field["cardinality"]
        total = count_bindings_for_field(field, new_entity_id, relations, peer_ids)
        if cardinality["max"] is not None and total > cardinality["max"]:
            errors.append(ValidationError(
                "cardinality_max",
                f"Maximum {cardinality['max']} pour « {field['label']} ».",
                field_id,
            ))

        if len(peer_ids) != len(set(peer_ids)):
            errors.append(ValidationError(
                "duplicate_peer",
                f"Valeurs en double pour « {field['label']} ».",
                field_id,
            ))

        for peer_id in peer_ids:
            peer = entity_map.get(peer_id)
            if not peer:
                errors.append(ValidationError("peer_not_found", f"Objet introuvable: {peer_id}", field_id))
                continue
            if peer.entity_type != field["peer_type"]:
                errors.append(ValidationError(
                    "peer_type_mismatch",
                    f"Type attendu {field['peer_type']}, reçu {peer.entity_type}.",
                    field_id,
                ))
                continue

            if field["direction"] == "outgoing":
                source_type, target_type = entity_type, field["peer_type"]
            else:
                source_type, target_type = field["peer_type"], entity_type

            if not validate_relation(source_type, rule["type"], target_type):
                errors.append(ValidationError(
                    "invalid_relation",
                    f"Relation non conforme: {source_type} —{rule['type']}→ {target_type}",
                    field_id,
                ))
                continue

            if new_entity_id:
                if field["direction"] == "outgoing":
                    src, tgt = new_entity_id, peer_id
                else:
                    src, tgt = peer_id, new_entity_id
                if _relation_key(src, rule["type"], tgt) in existing_keys:
                    errors.append(ValidationError(
                        "duplicate_relation",
                        "Cette relation existe déjà.",
                        field_id,
                    ))

    return errors


def validate_virtual_bindings(
    entity_type: str,
    virtual_bindings: dict[str, list[str]],
    entities: list[UrbanismEntity],
) -> list[ValidationError]:
    """Valide les champs virtual_* (hors métamodèle, non persistés)."""
    errors: list[ValidationError] = []
    entity_map = {e.id: e for e in entities}

    for vfield in VIRTUAL_ASSISTANT_FIELDS.get(entity_type, []):
        field_id = vfield["field_id"]
        peers = [e for e in entities if e.entity_type == vfield["peer_type"]]
        if not peers:
            continue

        peer_id_strs = virtual_bindings.get(field_id, [])
        if not peer_id_strs:
            errors.append(ValidationError(
                "required_field_missing",
                f"Le champ « {vfield['label']} » est obligatoire.",
                field_id,
            ))
            continue

        if vfield.get("widget") == "select" and len(peer_id_strs) > 1:
            errors.append(ValidationError(
                "cardinality_max",
                f"Une seule valeur autorisée pour « {vfield['label']} ».",
                field_id,
            ))

        for pid in peer_id_strs:
            try:
                peer_id = UUID(pid)
            except ValueError:
                errors.append(ValidationError("invalid_id", f"Identifiant invalide: {pid}", field_id))
                continue
            peer = entity_map.get(peer_id)
            if not peer:
                errors.append(ValidationError("peer_not_found", f"Objet introuvable: {peer_id}", field_id))
            elif peer.entity_type != vfield["peer_type"]:
                errors.append(ValidationError(
                    "peer_type_mismatch",
                    f"Type attendu {vfield['peer_type']}, reçu {peer.entity_type}.",
                    field_id,
                ))

    for field_id in virtual_bindings:
        if not _is_virtual_field(field_id):
            errors.append(ValidationError("unknown_field", f"Champ inconnu: {field_id}", field_id))

    return errors


def validate_link_action(
    rule_id: str,
    source: UrbanismEntity,
    target: UrbanismEntity,
    relations: list[UrbanismRelation],
    action: str,
) -> list[ValidationError]:
    errors: list[ValidationError] = []
    rule = RULE_BY_ID.get(rule_id)
    if not rule:
        return [ValidationError("unknown_rule", f"Règle inconnue: {rule_id}")]

    if action == "remove":
        return errors

    if not validate_relation(source.entity_type, rule["type"], target.entity_type):
        errors.append(ValidationError(
            "invalid_relation",
            f"Relation non conforme: {source.entity_type} —{rule['type']}→ {target.entity_type}",
        ))
        return errors

    if source.entity_type != rule["source"] or target.entity_type != rule["target"]:
        errors.append(ValidationError(
            "invalid_endpoints",
            f"Pour {rule_id}, la source doit être {rule['source']} et la cible {rule['target']}.",
        ))

    key = _relation_key(source.id, rule["type"], target.id)
    existing_keys = {_relation_key(r.source_id, r.relation_type, r.target_id) for r in relations}
    if action == "add" and key in existing_keys:
        errors.append(ValidationError("duplicate_relation", "Cette relation existe déjà."))

    return errors
