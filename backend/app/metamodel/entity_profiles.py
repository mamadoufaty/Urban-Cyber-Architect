"""Profils de création assistée — cardinalités et champs par type d'entité (Sprint 2.11)."""

from typing import Any

from app.metamodel.urbanism import ENTITY_CREATION_GUIDE, ENTITY_BY_ID, RULE_BY_ID

# Relations obligatoires à la création si des pairs compatibles existent
REQUIRED_RULE_IDS = frozenset({
    "R02", "R03", "R04", "R06", "R07", "R08", "R09", "R12", "R14", "R16",
})

# Obligatoire uniquement quand des pairs compatibles existent (ex. R05 si des objectifs sont présents)
CONDITIONAL_REQUIRED_RULE_IDS: dict[str, frozenset[str]] = {
    "processus": frozenset({"R05"}),
}

# Cardinalité stricte (min=1 max=1 côté entité créée quand required)
SINGLE_CARDINALITY_RULE_IDS = frozenset({
    "R02", "R03", "R04", "R06", "R07", "R08", "R09", "R12", "R14", "R16",
})

PROGRESS_GROUPS: dict[str, str] = {
    "metier": "metier",
    "objectif": "objectifs",
    "processus": "processus",
    "activite": "activites",
    "classe": "classes",
    "resultat": "resultats",
    "client": "clients",
    "evenement": "evenements",
    "organisation": "organisation",
    "procedure": "procedures",
    "operation": "operations",
    "acteur": "acteurs",
    "ilot_fonctionnel": "fonctionnel",
    "quartier_fonctionnel": "fonctionnel",
    "zone_fonctionnelle": "fonctionnel",
    "ilot_applicatif": "applicatif",
    "quartier_applicatif": "applicatif",
    "zone_applicative": "applicatif",
    "poste_travail": "technique",
    "byod": "technique",
    "serveur": "technique",
    "reseau": "technique",
    "site": "technique",
    "systeme_information": "transverse",
}

CREATION_ORDER: dict[str, int] = {
    "metier": 1,
    "objectif": 2,
    "processus": 3,
    "activite": 4,
    "classe": 5,
    "client": 6,
    "evenement": 7,
    "resultat": 8,
    "organisation": 9,
    "procedure": 10,
    "operation": 11,
    "acteur": 12,
    "ilot_fonctionnel": 13,
    "quartier_fonctionnel": 14,
    "zone_fonctionnelle": 15,
    "ilot_applicatif": 16,
    "quartier_applicatif": 17,
    "zone_applicative": 18,
    "poste_travail": 19,
    "byod": 20,
    "serveur": 21,
    "reseau": 22,
    "site": 23,
    "systeme_information": 24,
}


def _field_id(rule_id: str, direction: str, peer_type: str) -> str:
    return f"{rule_id}_{direction}_{peer_type}"


def _cardinality_for_rule(rule_id: str, required: bool) -> dict[str, int | None]:
    if rule_id in SINGLE_CARDINALITY_RULE_IDS:
        return {"min": 1 if required else 0, "max": 1}
    return {"min": 1 if required else 0, "max": None}


def _build_profile_field(guide_item: dict[str, str]) -> dict[str, Any]:
    rule_id = guide_item["relation_id"]
    direction = guide_item["direction"]
    peer_type = guide_item["peer_type"]
    required = rule_id in REQUIRED_RULE_IDS
    rule = RULE_BY_ID[rule_id]
    cardinality = _cardinality_for_rule(rule_id, required)

    return {
        "field_id": _field_id(rule_id, direction, peer_type),
        "rule_id": rule_id,
        "label": guide_item["label"],
        "relation_type": guide_item["relation_type"],
        "peer_type": peer_type,
        "direction": direction,
        "required": required,
        "cardinality": cardinality,
        "widget": "select" if cardinality["max"] == 1 else "multi-select",
        "source_type": rule["source"],
        "target_type": rule["target"],
    }


def build_entity_profiles() -> dict[str, dict[str, Any]]:
    profiles: dict[str, dict[str, Any]] = {}
    for entity_type, guide_items in ENTITY_CREATION_GUIDE.items():
        meta = ENTITY_BY_ID.get(entity_type, {})
        fields = [_build_profile_field(item) for item in guide_items]
        profiles[entity_type] = {
            "entity_type": entity_type,
            "entity_label": meta.get("label", entity_type),
            "couche": meta.get("couche", ""),
            "creation_order": CREATION_ORDER.get(entity_type, 99),
            "progress_group": PROGRESS_GROUPS.get(entity_type, entity_type),
            "fields": fields,
            "hints": _hints_for(entity_type),
        }
    return profiles


def _hints_for(entity_type: str) -> list[str]:
    hints = {
        "metier": ["Point d'entrée de la cartographie — aucune dépendance requise."],
        "objectif": ["Sélectionnez le Métier qui définit cet objectif."],
        "processus": [
            "Indiquez le Métier pilote.",
            "Liez au moins un Objectif (relation « est pris en compte dans »).",
            "Vous pouvez aussi lier des Procédures ou Événements existants.",
        ],
        "activite": ["Choisissez le Processus parent — la relation se décompose en sera créée automatiquement."],
        "ilot_applicatif": [
            "Sélectionnez l'Îlot fonctionnel mis en œuvre (lien dérivé d'affichage + R29/R30 si opération existante).",
        ],
    }
    return hints.get(entity_type, [])


ENTITY_PROFILES: dict[str, dict[str, Any]] = build_entity_profiles()


def get_entity_profile(entity_type: str) -> dict[str, Any] | None:
    return ENTITY_PROFILES.get(entity_type)


def get_profile_field(entity_type: str, field_id: str) -> dict[str, Any] | None:
    profile = get_entity_profile(entity_type)
    if not profile:
        return None
    for field in profile["fields"]:
        if field["field_id"] == field_id:
            return field
    return None


def resolve_relation_endpoints(
    field: dict[str, Any],
    new_entity_type: str,
    peer_id: str,
) -> tuple[str, str, str, str]:
    """Retourne (source_id_placeholder, target_id_placeholder, source_type, target_type).

    Les IDs sont 'new' ou 'peer' pour résolution ultérieure.
    """
    direction = field["direction"]
    if direction == "outgoing":
        return "new", "peer", new_entity_type, field["peer_type"]
    return "peer", "new", field["peer_type"], new_entity_type
