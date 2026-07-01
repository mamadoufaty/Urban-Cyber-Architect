"""Calcul de la progression de construction du graphe d'urbanisme."""

from __future__ import annotations

from typing import Any

from app.metamodel.entity_profiles import ENTITY_PROFILES
from app.models.entities import UrbanismEntity, UrbanismRelation

PROGRESS_STEPS: list[dict[str, Any]] = [
    {"id": "metier", "label": "Métier", "entity_types": ["metier"]},
    {"id": "objectifs", "label": "Objectifs", "entity_types": ["objectif"]},
    {"id": "processus", "label": "Processus", "entity_types": ["processus"]},
    {"id": "activites", "label": "Activités", "entity_types": ["activite"]},
    {"id": "classes", "label": "Classes", "entity_types": ["classe"]},
    {"id": "organisation", "label": "Organisation", "entity_types": ["organisation"]},
    {"id": "procedures", "label": "Procédures", "entity_types": ["procedure"]},
    {"id": "operations", "label": "Opérations", "entity_types": ["operation"]},
    {"id": "fonctionnel", "label": "Fonctionnel", "entity_types": ["ilot_fonctionnel", "quartier_fonctionnel", "zone_fonctionnelle"]},
    {"id": "applicatif", "label": "Applicatif", "entity_types": ["ilot_applicatif", "quartier_applicatif", "zone_applicative"]},
    {"id": "technique", "label": "Technique", "entity_types": ["poste_travail", "byod", "serveur", "reseau", "site"]},
]


def calculate_progress(
    entities: list[UrbanismEntity],
    relations: list[UrbanismRelation],
    orphan_ids: set[str] | None = None,
) -> dict[str, Any]:
    orphan_ids = orphan_ids or set()
    connected: set[str] = set()
    for r in relations:
        connected.add(str(r.source_id))
        connected.add(str(r.target_id))

    groups: list[dict[str, Any]] = []
    done_count = 0

    for step in PROGRESS_STEPS:
        typed = [e for e in entities if e.entity_type in step["entity_types"]]
        count = len(typed)
        if count == 0:
            status = "pending"
        else:
            orphans_in_group = sum(1 for e in typed if str(e.id) in orphan_ids)
            if orphans_in_group > 0 and len(typed) == orphans_in_group:
                status = "partial"
            else:
                status = "done"
                done_count += 1

        groups.append({
            "id": step["id"],
            "label": step["label"],
            "status": status,
            "count": count,
        })

    total = len(PROGRESS_STEPS)
    return {
        "groups": groups,
        "overall_percent": round((done_count / total) * 100) if total else 0,
        "total_entities": len(entities),
        "total_relations": len(relations),
    }
