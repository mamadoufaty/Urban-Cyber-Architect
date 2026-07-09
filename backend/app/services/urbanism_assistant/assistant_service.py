"""Service principal de l'assistant de construction du graphe d'urbanisme."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.metamodel.entity_profiles import get_entity_profile, get_profile_field
from app.metamodel.urbanism import RULE_BY_ID, get_entity_meta
from app.models.entities import Project, UrbanismEntity, UrbanismRelation
from app.services.urbanism_assistant.cardinality_validator import (
    ValidationError,
    split_bindings,
    validate_bindings,
    validate_link_action,
    validate_virtual_bindings,
)
from app.services.urbanism_assistant.form_schema_generator import generate_form_schema
from app.services.urbanism_entity_utils import (
    find_entity_by_normalized_label,
    resolve_entity_couche,
    set_assistant_derived_link,
)
from app.services.urbanism_derived_edges import link_applicatif_to_fonctionnel_via_operation
from app.services.urbanism_engine import _analyze_graph, _category_for_relation


class AssistantError(Exception):
    def __init__(self, message: str, errors: list[ValidationError] | None = None):
        super().__init__(message)
        self.errors = errors or []


def _apply_virtual_bindings(
    entity: UrbanismEntity,
    virtual_bindings: dict[str, list[str]],
    entities: list[UrbanismEntity],
    relations: list[UrbanismRelation],
    project_id: UUID,
) -> list[UrbanismRelation]:
    """Applique les champs virtual_* — relations officielles uniquement, rien en properties."""
    created: list[UrbanismRelation] = []

    for field_id, peer_ids in virtual_bindings.items():
        if field_id == "virtual_linked_ilot_fonctionnel" and peer_ids:
            try:
                ilot_f_id = UUID(peer_ids[0])
            except ValueError:
                continue
            set_assistant_derived_link(entity, ilot_fonctionnel_id=ilot_f_id)
            official = link_applicatif_to_fonctionnel_via_operation(
                entity, ilot_f_id, entities, relations, project_id
            )
            created.extend(official)
            relations.extend(official)

    return created


async def _load_project_graph(
    db: AsyncSession, project_id: UUID, cartography_version_id: UUID | None = None
) -> tuple[list[UrbanismEntity], list[UrbanismRelation]]:
    entity_stmt = select(UrbanismEntity).where(UrbanismEntity.project_id == project_id)
    relation_stmt = select(UrbanismRelation).where(UrbanismRelation.project_id == project_id)
    if cartography_version_id is not None:
        entity_stmt = entity_stmt.where(
            UrbanismEntity.cartography_version_id == cartography_version_id
        )
        relation_stmt = relation_stmt.where(
            UrbanismRelation.cartography_version_id == cartography_version_id
        )
    entities = list((await db.execute(entity_stmt)).scalars())
    relations = list((await db.execute(relation_stmt)).scalars())
    return entities, relations


async def get_form_schema(
    db: AsyncSession, project_id: UUID, entity_type: str, cartography_id: UUID | None = None
) -> dict[str, Any]:
    from app.services import cartography_service

    project = await db.get(Project, project_id)
    if not project:
        raise AssistantError("Project not found")
    if not get_entity_profile(entity_type):
        raise AssistantError(f"Type d'entité inconnu: {entity_type}")

    _cartography, version = await cartography_service.resolve_read_version(
        db, project_id, cartography_id
    )
    entities, relations = await _load_project_graph(db, project_id, version.id)
    return generate_form_schema(entity_type, entities, relations)


async def assisted_create(
    db: AsyncSession,
    project_id: UUID,
    entity_type: str,
    label: str,
    bindings: dict[str, list[str]],
    cartography_id: UUID | None = None,
) -> dict[str, Any]:
    from app.services import cartography_service

    project = await db.get(Project, project_id)
    if not project:
        raise AssistantError("Project not found")

    try:
        cartography, version, id_map = await cartography_service.resolve_editable_version(
            db, project_id, cartography_id
        )
    except cartography_service.CartographyError as e:
        raise AssistantError(str(e)) from e
    version_id = version.id
    if id_map:
        # Une bascule de version a eu lieu (COW) : les identifiants de pairs
        # fournis par le client référencent encore l'ancienne version figée.
        def _remap_pid(pid: str) -> str:
            try:
                return str(id_map.get(UUID(pid), UUID(pid)))
            except (ValueError, TypeError):
                return pid

        bindings = {
            field_id: [_remap_pid(pid) for pid in peer_ids]
            for field_id, peer_ids in bindings.items()
        }

    meta = get_entity_meta(entity_type)
    profile = get_entity_profile(entity_type)
    if not meta or not profile:
        raise AssistantError(f"Type d'entité inconnu: {entity_type}")

    if not label.strip():
        raise AssistantError("Le nom est obligatoire")

    entities, relations = await _load_project_graph(db, project_id, version_id)
    schema = generate_form_schema(entity_type, entities, relations)
    schema_required = set(schema.get("required_field_ids", []))

    metamodel_bindings, virtual_bindings = split_bindings(bindings)

    errors = validate_bindings(
        entity_type,
        metamodel_bindings,
        entities,
        relations,
        new_entity_id=None,
        schema_field_ids=schema_required,
    )
    errors.extend(validate_virtual_bindings(entity_type, virtual_bindings, entities))
    if errors:
        raise AssistantError(errors[0].message, errors)

    existing = find_entity_by_normalized_label(entities, entity_type, label)
    reused = existing is not None
    canonical_couche = resolve_entity_couche(entity_type, meta["couche"])
    if existing:
        entity = existing
        if entity.couche != canonical_couche:
            entity.couche = canonical_couche
    else:
        entity = UrbanismEntity(
            project_id=project_id,
            cartography_version_id=version_id,
            entity_type=entity_type,
            couche=canonical_couche,
            label=label.strip(),
        )
        db.add(entity)
        await db.flush()

    created_relations: list[UrbanismRelation] = []
    created_relations.extend(
        _apply_virtual_bindings(
            entity, virtual_bindings, entities, relations, project_id
        )
    )
    for rel in created_relations:
        rel.cartography_version_id = version_id
        db.add(rel)
    await db.flush()

    for field_id, peer_ids in metamodel_bindings.items():
        field = get_profile_field(entity_type, field_id)
        if not field:
            continue
        rule = RULE_BY_ID[field["rule_id"]]
        for peer_id_str in peer_ids:
            peer_id = UUID(peer_id_str)
            if field["direction"] == "outgoing":
                source_id, target_id = entity.id, peer_id
            else:
                source_id, target_id = peer_id, entity.id

            dup = any(
                r.source_id == source_id and r.target_id == target_id and r.relation_type == rule["type"]
                for r in relations
            )
            if dup:
                raise AssistantError("Cette relation existe déjà.")

            source_entity = entity if source_id == entity.id else next(e for e in entities if e.id == source_id)
            target_entity = entity if target_id == entity.id else next(e for e in entities if e.id == target_id)

            rel = UrbanismRelation(
                project_id=project_id,
                cartography_version_id=version_id,
                source_id=source_id,
                target_id=target_id,
                relation_type=rule["type"],
                category=_category_for_relation(
                    source_entity.entity_type, rule["type"], target_entity.entity_type
                ),
            )
            db.add(rel)
            created_relations.append(rel)
            relations.append(rel)

    await cartography_service.log_history(
        db,
        cartography,
        version,
        author=None,
        action="updated",
        comment=f"Assistant : « {label.strip()} » ({entity_type}).",
    )
    await db.commit()
    await db.refresh(entity)
    for rel in created_relations:
        await db.refresh(rel)

    all_entities, all_relations = await _load_project_graph(db, project_id, version_id)
    analysis = _analyze_graph(all_entities, all_relations)

    return {
        "entity": entity,
        "relations_created": created_relations,
        "analysis": analysis,
        "bindings_applied": len(created_relations),
        "reused": reused,
    }


async def assisted_link(
    db: AsyncSession,
    project_id: UUID,
    action: str,
    rule_id: str,
    source_id: UUID,
    target_id: UUID,
    cartography_id: UUID | None = None,
) -> dict[str, Any]:
    from app.services import cartography_service

    if action not in ("add", "remove", "replace"):
        raise AssistantError(f"Action inconnue: {action}")

    project = await db.get(Project, project_id)
    if not project:
        raise AssistantError("Project not found")

    try:
        cartography, version, id_map = await cartography_service.resolve_editable_version(
            db, project_id, cartography_id
        )
    except cartography_service.CartographyError as e:
        raise AssistantError(str(e)) from e
    version_id = version.id
    source_id = cartography_service.remap_id(id_map, source_id)
    target_id = cartography_service.remap_id(id_map, target_id)

    source = await db.get(UrbanismEntity, source_id)
    target = await db.get(UrbanismEntity, target_id)
    if not source or not target or source.project_id != project_id or target.project_id != project_id:
        raise AssistantError("Entité source ou cible introuvable")

    entities, relations = await _load_project_graph(db, project_id, version_id)
    rule = RULE_BY_ID.get(rule_id)
    if not rule:
        raise AssistantError(f"Règle inconnue: {rule_id}")

    if action == "remove":
        result = await db.execute(
            select(UrbanismRelation).where(
                UrbanismRelation.project_id == project_id,
                UrbanismRelation.cartography_version_id == version_id,
                UrbanismRelation.source_id == source_id,
                UrbanismRelation.target_id == target_id,
                UrbanismRelation.relation_type == rule["type"],
            )
        )
        rel = result.scalar_one_or_none()
        if not rel:
            raise AssistantError("Relation introuvable")
        await db.delete(rel)
        await cartography_service.log_history(
            db, cartography, version, author=None, action="updated", comment="Suppression d'un lien."
        )
        await db.commit()
        all_entities, all_relations = await _load_project_graph(db, project_id, version_id)
        return {
            "action": "remove",
            "relation": None,
            "analysis": _analyze_graph(all_entities, all_relations),
        }

    if action == "replace":
        await db.execute(
            delete(UrbanismRelation).where(
                UrbanismRelation.project_id == project_id,
                UrbanismRelation.cartography_version_id == version_id,
                UrbanismRelation.source_id == source_id,
                UrbanismRelation.relation_type == rule["type"],
            )
        )
        await db.flush()
        entities, relations = await _load_project_graph(db, project_id, version_id)

    errors = validate_link_action(rule_id, source, target, relations, "add")
    if errors:
        raise AssistantError(errors[0].message, errors)

    rel = UrbanismRelation(
        project_id=project_id,
        cartography_version_id=version_id,
        source_id=source_id,
        target_id=target_id,
        relation_type=rule["type"],
        category=_category_for_relation(source.entity_type, rule["type"], target.entity_type),
    )
    db.add(rel)
    await cartography_service.log_history(
        db, cartography, version, author=None, action="updated", comment="Ajout d'un lien."
    )
    await db.commit()
    await db.refresh(rel)

    all_entities, all_relations = await _load_project_graph(db, project_id, version_id)
    return {
        "action": action,
        "relation": rel,
        "analysis": _analyze_graph(all_entities, all_relations),
    }
