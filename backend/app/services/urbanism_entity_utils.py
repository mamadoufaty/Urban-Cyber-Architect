"""Utilitaires entités urbanisme — normalisation libellés et détection doublons."""

from __future__ import annotations

import re
import unicodedata
from uuid import UUID

from sqlalchemy.orm.attributes import flag_modified

from app.metamodel.urbanism import get_entity_meta
from app.models.entities import UrbanismEntity, UrbanismRelation

ASSISTANT_DERIVED_LINKS_KEY = "_assistant_derived_links"


def resolve_entity_couche(entity_type: str, stored_couche: str | None = None) -> str:
    """Couche canonique depuis le métamodèle — le type d'entité prime sur la valeur stockée."""
    meta = get_entity_meta(entity_type)
    if meta and meta.get("couche"):
        return meta["couche"]
    return stored_couche or "metier"


def set_assistant_derived_link(
    entity: UrbanismEntity,
    *,
    ilot_fonctionnel_id: UUID,
) -> None:
    """Mémorise un lien d'affichage assistant (hors propriétés métier validées)."""
    props = dict(entity.properties or {})
    links = dict(props.get(ASSISTANT_DERIVED_LINKS_KEY) or {})
    links["ilot_fonctionnel_id"] = str(ilot_fonctionnel_id)
    props[ASSISTANT_DERIVED_LINKS_KEY] = links
    entity.properties = props
    flag_modified(entity, "properties")


def get_assistant_ilot_fonctionnel_id(entity: UrbanismEntity) -> UUID | None:
    props = entity.properties or {}
    links = props.get(ASSISTANT_DERIVED_LINKS_KEY) or {}
    raw = links.get("ilot_fonctionnel_id")
    if not raw:
        return None
    try:
        return UUID(str(raw))
    except (ValueError, TypeError):
        return None


def normalize_label(label: str) -> str:
    """Clé de déduplication : minuscules, espaces réduits, sans accents ni suffixe de type."""
    text = label.strip().lower()
    text = re.sub(r"\s*\([^)]+\)\s*$", "", text)
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", text).strip()


def entity_dedup_key(entity: UrbanismEntity) -> tuple[str, str]:
    return (entity.entity_type, normalize_label(entity.label))


def find_entity_by_normalized_label(
    entities: list[UrbanismEntity],
    entity_type: str,
    label: str,
) -> UrbanismEntity | None:
    key = normalize_label(label)
    for entity in entities:
        if entity.entity_type == entity_type and normalize_label(entity.label) == key:
            return entity
    return None


def relation_degree(entity_id: UUID, relations: list[UrbanismRelation]) -> int:
    return sum(1 for r in relations if r.source_id == entity_id or r.target_id == entity_id)


def pick_canonical_entity(
    group: list[UrbanismEntity],
    relations: list[UrbanismRelation],
) -> UrbanismEntity:
    """Conserve l'entité la plus connectée, puis la plus ancienne."""
    return max(
        group,
        key=lambda e: (
            relation_degree(e.id, relations),
            -(e.created_at.timestamp() if e.created_at else 0),
        ),
    )
