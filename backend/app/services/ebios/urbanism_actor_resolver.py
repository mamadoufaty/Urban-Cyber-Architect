"""Résolution des acteurs urbanisme — lecture seule, sans rôles codés en dur."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import UrbanismEntity, UrbanismRelation


async def load_urbanism_graph(
    db: AsyncSession, project_id: UUID
) -> tuple[list[UrbanismEntity], list[UrbanismRelation]]:
    """Charge le graphe de la cartographie active du projet (lecture seule).

    EBIOS RM, le générateur de livrables et la corrélation SOC raisonnent sur
    « la » cartographie d'un projet : depuis l'introduction du multi-cartographies
    (plusieurs cartes indépendantes par projet), ils continuent de s'appuyer sur
    la cartographie active par défaut plutôt que d'agréger toutes les cartes du
    projet, afin qu'aucune donnée ne soit mélangée entre cartes indépendantes.
    """
    from app.services import cartography_service

    try:
        _cartography, version = await cartography_service.resolve_read_version(db, project_id)
    except cartography_service.CartographyError:
        return [], []

    entities = list(
        (
            await db.execute(
                select(UrbanismEntity)
                .where(UrbanismEntity.cartography_version_id == version.id)
                .order_by(UrbanismEntity.entity_type, UrbanismEntity.label)
            )
        ).scalars().all()
    )
    relations = list(
        (
            await db.execute(
                select(UrbanismRelation).where(
                    UrbanismRelation.cartography_version_id == version.id
                )
            )
        ).scalars().all()
    )
    return entities, relations


def _entity_map(entities: list[UrbanismEntity]) -> dict[str, UrbanismEntity]:
    return {str(e.id): e for e in entities}


def _acteur_refs(entities: list[UrbanismEntity]) -> list[dict]:
    return [
        {
            "id": str(e.id),
            "label": e.label,
            "entity_type": e.entity_type,
            "description": e.description,
            "couche": e.couche,
        }
        for e in entities
        if e.entity_type == "acteur"
    ]


def _organisation_for_acteur(
    acteur_id: str,
    entities_by_id: dict[str, UrbanismEntity],
    relations: list[UrbanismRelation],
) -> UrbanismEntity | None:
    for rel in relations:
        if str(rel.source_id) != acteur_id:
            continue
        target = entities_by_id.get(str(rel.target_id))
        if target and target.entity_type == "organisation":
            return target
    for rel in relations:
        if str(rel.target_id) != acteur_id:
            continue
        source = entities_by_id.get(str(rel.source_id))
        if source and source.entity_type == "organisation":
            return source
    return None


def _acteurs_near_entity(
    urbanism_entity_id: str | None,
    entities_by_id: dict[str, UrbanismEntity],
    relations: list[UrbanismRelation],
    acteurs: list[UrbanismEntity],
) -> list[UrbanismEntity]:
    if not urbanism_entity_id:
        return acteurs

    linked_ids: list[str] = []
    seen: set[str] = set()

    def add_acteur(entity_id: str) -> None:
        entity = entities_by_id.get(entity_id)
        if entity and entity.entity_type == "acteur" and entity_id not in seen:
            seen.add(entity_id)
            linked_ids.append(entity_id)

    root = entities_by_id.get(urbanism_entity_id)
    if root and root.entity_type == "acteur":
        add_acteur(urbanism_entity_id)

    for rel in relations:
        if str(rel.source_id) == urbanism_entity_id:
            add_acteur(str(rel.target_id))
        if str(rel.target_id) == urbanism_entity_id:
            add_acteur(str(rel.source_id))

    near = [entities_by_id[i] for i in linked_ids]
    return near if near else acteurs


def _organisation_near_entity(
    urbanism_entity_id: str | None,
    entities_by_id: dict[str, UrbanismEntity],
    relations: list[UrbanismRelation],
) -> UrbanismEntity | None:
    if not urbanism_entity_id:
        orgs = [e for e in entities_by_id.values() if e.entity_type == "organisation"]
        return orgs[0] if orgs else None
    visited = {urbanism_entity_id}
    frontier = [urbanism_entity_id]
    for _ in range(4):
        next_frontier: list[str] = []
        for node_id in frontier:
            for rel in relations:
                candidates: list[str] = []
                if str(rel.source_id) == node_id:
                    candidates.append(str(rel.target_id))
                if str(rel.target_id) == node_id:
                    candidates.append(str(rel.source_id))
                for cid in candidates:
                    if cid in visited:
                        continue
                    visited.add(cid)
                    entity = entities_by_id.get(cid)
                    if entity and entity.entity_type == "organisation":
                        return entity
                    next_frontier.append(cid)
        frontier = next_frontier
    orgs = [e for e in entities_by_id.values() if e.entity_type == "organisation"]
    return orgs[0] if orgs else None


def resolve_urbanism_roles(
    entities: list[UrbanismEntity],
    relations: list[UrbanismRelation],
    *,
    urbanism_entity_id: str | None = None,
) -> dict:
    """Attribue propriétaire, décideur et validateur parmi les acteurs urbanisme."""
    entities_by_id = _entity_map(entities)
    acteurs = [e for e in entities if e.entity_type == "acteur"]
    pool = _acteurs_near_entity(urbanism_entity_id, entities_by_id, relations, acteurs)

    def ref(entity: UrbanismEntity | None) -> dict | None:
        if not entity:
            return None
        return {
            "urbanism_entity_id": str(entity.id),
            "label": entity.label,
            "entity_type": entity.entity_type,
            "couche": entity.couche,
        }

    owner = pool[0] if pool else None
    decision_maker = pool[1] if len(pool) > 1 else (pool[0] if pool else None)
    validator = pool[2] if len(pool) > 2 else (pool[1] if len(pool) > 1 else owner)

    org = _organisation_near_entity(urbanism_entity_id, entities_by_id, relations)
    if owner and not org:
        org = _organisation_for_acteur(str(owner.id), entities_by_id, relations)

    return {
        "owner_actor": ref(owner),
        "decision_maker_actor": ref(decision_maker),
        "validator_actor": ref(validator),
        "organization": ref(org) if org else None,
        "available_acteurs": _acteur_refs(entities),
    }
