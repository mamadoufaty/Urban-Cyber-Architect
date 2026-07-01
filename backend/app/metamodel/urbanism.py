"""Club Urba metamodel — entity types and relation semantics (référence ISRC10 / Métropolis)."""

from typing import Any

# (type_id, label, couche, color)
ENTITY_TYPES: list[dict[str, str]] = [
    # Métier
    {"id": "metier", "label": "Métier", "couche": "metier", "color": "#00d4aa"},
    {"id": "objectif", "label": "Objectif", "couche": "metier", "color": "#00d4aa"},
    {"id": "processus", "label": "Processus", "couche": "metier", "color": "#00d4aa"},
    {"id": "activite", "label": "Activité", "couche": "metier", "color": "#00d4aa"},
    {"id": "classe", "label": "Classe", "couche": "metier", "color": "#00d4aa"},
    {"id": "resultat", "label": "Résultat", "couche": "metier", "color": "#00d4aa"},
    {"id": "client", "label": "Client", "couche": "metier", "color": "#00d4aa"},
    {"id": "evenement", "label": "Événement", "couche": "metier", "color": "#00d4aa"},
    # Organisation
    {"id": "organisation", "label": "Organisation", "couche": "organisation", "color": "#3b82f6"},
    {"id": "procedure", "label": "Procédure", "couche": "organisation", "color": "#3b82f6"},
    {"id": "operation", "label": "Opération", "couche": "organisation", "color": "#3b82f6"},
    {"id": "acteur", "label": "Acteur", "couche": "organisation", "color": "#3b82f6"},
    # Fonctionnel
    {"id": "ilot_fonctionnel", "label": "Îlot fonctionnel", "couche": "fonctionnel", "color": "#8b5cf6"},
    {"id": "quartier_fonctionnel", "label": "Quartier fonctionnel", "couche": "fonctionnel", "color": "#8b5cf6"},
    {"id": "zone_fonctionnelle", "label": "Zone fonctionnelle", "couche": "fonctionnel", "color": "#8b5cf6"},
    # Applicatif
    {"id": "ilot_applicatif", "label": "Îlot applicatif", "couche": "applicatif", "color": "#f59e0b"},
    {"id": "quartier_applicatif", "label": "Quartier applicatif", "couche": "applicatif", "color": "#f59e0b"},
    {"id": "zone_applicative", "label": "Zone applicative", "couche": "applicatif", "color": "#f59e0b"},
    # Technique
    {"id": "poste_travail", "label": "Poste de travail", "couche": "technique", "color": "#06b6d4"},
    {"id": "byod", "label": "BYOD", "couche": "technique", "color": "#06b6d4"},
    {"id": "serveur", "label": "Serveur", "couche": "technique", "color": "#06b6d4"},
    {"id": "reseau", "label": "Réseau", "couche": "technique", "color": "#06b6d4"},
    {"id": "site", "label": "Site", "couche": "technique", "color": "#06b6d4"},
    # Transverse (schéma Club Urba — R01)
    {"id": "systeme_information", "label": "Système d'information", "couche": "transverse", "color": "#64748b"},
]

COUCHE_LABELS = {
    "metier": "Couche Métier",
    "organisation": "Couche Organisation",
    "fonctionnel": "Couche Fonctionnelle",
    "applicatif": "Couche Applicative",
    "technique": "Couche Technique",
    "transverse": "Transverse",
}

COUCHE_COLORS = {
    "metier": "#00d4aa",
    "organisation": "#3b82f6",
    "fonctionnel": "#8b5cf6",
    "applicatif": "#f59e0b",
    "technique": "#06b6d4",
    "transverse": "#64748b",
}

# Contrat fonctionnel officiel — schéma Club Urba (R01–R30)
REFERENCE_RELATIONS: list[dict[str, Any]] = [
    {"id": "R01", "source": "metier", "type": "commande", "target": "systeme_information", "category": "transverse"},
    {"id": "R02", "source": "metier", "type": "définit", "target": "objectif", "category": "metier"},
    {"id": "R03", "source": "metier", "type": "pilote", "target": "processus", "category": "metier"},
    {"id": "R04", "source": "metier", "type": "décide de", "target": "organisation", "category": "organisation"},
    {"id": "R05", "source": "objectif", "type": "est pris en compte dans", "target": "processus", "category": "metier"},
    {"id": "R06", "source": "processus", "type": "se décompose en", "target": "activite", "category": "metier"},
    {"id": "R07", "source": "activite", "type": "manipule", "target": "classe", "category": "metier"},
    {"id": "R08", "source": "classe", "type": "donne lieu à", "target": "ilot_fonctionnel", "category": "fonctionnel"},
    {"id": "R09", "source": "client", "type": "génère", "target": "evenement", "category": "metier"},
    {"id": "R10", "source": "evenement", "type": "déclenche", "target": "processus", "category": "metier"},
    {"id": "R11", "source": "resultat", "type": "satisfait", "target": "client", "category": "metier"},
    {"id": "R12", "source": "organisation", "type": "est déclinée en", "target": "procedure", "category": "organisation"},
    {"id": "R13", "source": "procedure", "type": "s'organise en", "target": "processus", "category": "organisation"},
    {"id": "R14", "source": "procedure", "type": "se décompose en", "target": "operation", "category": "organisation"},
    {"id": "R15", "source": "acteur", "type": "réalise", "target": "operation", "category": "organisation"},
    {"id": "R16", "source": "operation", "type": "produit", "target": "resultat", "category": "organisation"},
    {"id": "R17", "source": "ilot_fonctionnel", "type": "se regroupe dans", "target": "quartier_fonctionnel", "category": "fonctionnel"},
    {"id": "R18", "source": "quartier_fonctionnel", "type": "compose", "target": "zone_fonctionnelle", "category": "fonctionnel"},
    {"id": "R19", "source": "ilot_applicatif", "type": "compose", "target": "quartier_applicatif", "category": "applicatif"},
    {"id": "R20", "source": "quartier_applicatif", "type": "compose", "target": "zone_applicative", "category": "applicatif"},
    {"id": "R21", "source": "ilot_applicatif", "type": "est accessible via", "target": "poste_travail", "category": "technique"},
    {"id": "R22", "source": "ilot_applicatif", "type": "est accessible via", "target": "byod", "category": "technique"},
    {"id": "R23", "source": "acteur", "type": "utilise", "target": "poste_travail", "category": "technique"},
    {"id": "R24", "source": "acteur", "type": "utilise", "target": "byod", "category": "technique"},
    {"id": "R25", "source": "poste_travail", "type": "est connecté à", "target": "serveur", "category": "technique"},
    {"id": "R26", "source": "poste_travail", "type": "est connecté à", "target": "reseau", "category": "technique"},
    {"id": "R27", "source": "byod", "type": "est connecté à", "target": "reseau", "category": "technique"},
    {"id": "R28", "source": "serveur", "type": "est hébergé sur", "target": "site", "category": "technique"},
    {"id": "R29", "source": "operation", "type": "est mise en œuvre par", "target": "ilot_applicatif", "category": "applicatif"},
    {"id": "R30", "source": "operation", "type": "est mise en œuvre par", "target": "ilot_fonctionnel", "category": "fonctionnel"},
    # Extension Club Urba — pilotage organisationnel par les acteurs
    {"id": "R31", "source": "acteur", "type": "pilote", "target": "procedure", "category": "organisation"},
]

# Relations implémentées par le moteur (= référence officielle)
RELATION_RULES: list[dict[str, Any]] = list(REFERENCE_RELATIONS)
RULE_BY_ID: dict[str, dict[str, Any]] = {r["id"]: r for r in REFERENCE_RELATIONS}

RELATION_CATEGORIES = {
    "metier": "Relations métier",
    "organisation": "Relations organisationnelles",
    "fonctionnel": "Dépendances fonctionnelles",
    "applicatif": "Dépendances applicatives",
    "technique": "Dépendances techniques",
    "transverse": "Relations transverses",
}

# Entités attendues par couche (contrat Sprint 2.10)
REFERENCE_ENTITY_IDS = [
    "metier", "objectif", "processus", "activite", "classe", "resultat", "client", "evenement",
    "organisation", "procedure", "operation", "acteur",
    "ilot_fonctionnel", "quartier_fonctionnel", "zone_fonctionnelle",
    "ilot_applicatif", "quartier_applicatif", "zone_applicative",
    "poste_travail", "byod", "serveur", "reseau", "site",
]

# Libellés inverses pour guider l'utilisateur lors de la création (relations entrantes)
_INVERSE_LABELS: dict[tuple[str, str, str], str] = {
    ("metier", "définit", "objectif"): "est défini par",
    ("metier", "pilote", "processus"): "est piloté par",
    ("metier", "décide de", "organisation"): "est décidée par",
    ("objectif", "est pris en compte dans", "processus"): "prend en compte",
    ("evenement", "déclenche", "processus"): "est déclenché par",
    ("procedure", "s'organise en", "processus"): "est organisé par",
    ("procedure", "se décompose en", "operation"): "est issue de",
    ("acteur", "réalise", "operation"): "est réalisée par",
    ("acteur", "pilote", "procedure"): "est pilotée par",
    ("metier", "commande", "systeme_information"): "est commandé par",
}

# Guide de création par type d'entité (Sprint 2.10 §3)
ENTITY_CREATION_GUIDE: dict[str, list[dict[str, str]]] = {
    "metier": [],
    "objectif": [
        {"direction": "incoming", "relation_id": "R02", "label": "est défini par", "relation_type": "définit", "peer_type": "metier"},
        {"direction": "outgoing", "relation_id": "R05", "label": "est pris en compte dans", "relation_type": "est pris en compte dans", "peer_type": "processus"},
    ],
    "processus": [
        {"direction": "incoming", "relation_id": "R03", "label": "est piloté par", "relation_type": "pilote", "peer_type": "metier"},
        {"direction": "incoming", "relation_id": "R05", "label": "prend en compte", "relation_type": "est pris en compte dans", "peer_type": "objectif"},
        {"direction": "incoming", "relation_id": "R10", "label": "est déclenché par", "relation_type": "déclenche", "peer_type": "evenement"},
        {"direction": "incoming", "relation_id": "R13", "label": "est organisé par", "relation_type": "s'organise en", "peer_type": "procedure"},
        {"direction": "outgoing", "relation_id": "R06", "label": "se décompose en", "relation_type": "se décompose en", "peer_type": "activite"},
    ],
    "activite": [
        {"direction": "incoming", "relation_id": "R06", "label": "est issue de", "relation_type": "se décompose en", "peer_type": "processus"},
        {"direction": "outgoing", "relation_id": "R07", "label": "manipule", "relation_type": "manipule", "peer_type": "classe"},
    ],
    "classe": [
        {"direction": "incoming", "relation_id": "R07", "label": "est manipulée par", "relation_type": "manipule", "peer_type": "activite"},
        {"direction": "outgoing", "relation_id": "R08", "label": "donne lieu à", "relation_type": "donne lieu à", "peer_type": "ilot_fonctionnel"},
    ],
    "client": [
        {"direction": "incoming", "relation_id": "R11", "label": "est satisfait par", "relation_type": "satisfait", "peer_type": "resultat"},
        {"direction": "outgoing", "relation_id": "R09", "label": "génère", "relation_type": "génère", "peer_type": "evenement"},
    ],
    "evenement": [
        {"direction": "incoming", "relation_id": "R09", "label": "est généré par", "relation_type": "génère", "peer_type": "client"},
        {"direction": "outgoing", "relation_id": "R10", "label": "déclenche", "relation_type": "déclenche", "peer_type": "processus"},
    ],
    "resultat": [
        {"direction": "incoming", "relation_id": "R16", "label": "est produit par", "relation_type": "produit", "peer_type": "operation"},
        {"direction": "outgoing", "relation_id": "R11", "label": "satisfait", "relation_type": "satisfait", "peer_type": "client"},
    ],
    "organisation": [
        {"direction": "incoming", "relation_id": "R04", "label": "est décidée par", "relation_type": "décide de", "peer_type": "metier"},
        {"direction": "outgoing", "relation_id": "R12", "label": "est déclinée en", "relation_type": "est déclinée en", "peer_type": "procedure"},
    ],
    "procedure": [
        {"direction": "incoming", "relation_id": "R12", "label": "est issue de", "relation_type": "est déclinée en", "peer_type": "organisation"},
        {"direction": "incoming", "relation_id": "R31", "label": "est pilotée par", "relation_type": "pilote", "peer_type": "acteur"},
        {"direction": "outgoing", "relation_id": "R13", "label": "s'organise en", "relation_type": "s'organise en", "peer_type": "processus"},
        {"direction": "outgoing", "relation_id": "R14", "label": "se décompose en", "relation_type": "se décompose en", "peer_type": "operation"},
    ],
    "operation": [
        {"direction": "incoming", "relation_id": "R14", "label": "est issue de", "relation_type": "se décompose en", "peer_type": "procedure"},
        {"direction": "incoming", "relation_id": "R15", "label": "est réalisée par", "relation_type": "réalise", "peer_type": "acteur"},
        {"direction": "outgoing", "relation_id": "R16", "label": "produit", "relation_type": "produit", "peer_type": "resultat"},
        {"direction": "outgoing", "relation_id": "R29", "label": "est mise en œuvre par", "relation_type": "est mise en œuvre par", "peer_type": "ilot_applicatif"},
        {"direction": "outgoing", "relation_id": "R30", "label": "est mise en œuvre par", "relation_type": "est mise en œuvre par", "peer_type": "ilot_fonctionnel"},
    ],
    "acteur": [
        {"direction": "outgoing", "relation_id": "R31", "label": "pilote", "relation_type": "pilote", "peer_type": "procedure"},
        {"direction": "outgoing", "relation_id": "R15", "label": "réalise", "relation_type": "réalise", "peer_type": "operation"},
        {"direction": "outgoing", "relation_id": "R23", "label": "utilise", "relation_type": "utilise", "peer_type": "poste_travail"},
        {"direction": "outgoing", "relation_id": "R24", "label": "utilise", "relation_type": "utilise", "peer_type": "byod"},
    ],
    "ilot_fonctionnel": [
        {"direction": "incoming", "relation_id": "R08", "label": "est issu de", "relation_type": "donne lieu à", "peer_type": "classe"},
        {"direction": "incoming", "relation_id": "R30", "label": "met en œuvre", "relation_type": "est mise en œuvre par", "peer_type": "operation"},
        {"direction": "outgoing", "relation_id": "R17", "label": "se regroupe dans", "relation_type": "se regroupe dans", "peer_type": "quartier_fonctionnel"},
    ],
    "quartier_fonctionnel": [
        {"direction": "incoming", "relation_id": "R17", "label": "regroupe", "relation_type": "se regroupe dans", "peer_type": "ilot_fonctionnel"},
        {"direction": "outgoing", "relation_id": "R18", "label": "compose", "relation_type": "compose", "peer_type": "zone_fonctionnelle"},
    ],
    "zone_fonctionnelle": [
        {"direction": "incoming", "relation_id": "R18", "label": "est composée de", "relation_type": "compose", "peer_type": "quartier_fonctionnel"},
    ],
    "ilot_applicatif": [
        {"direction": "incoming", "relation_id": "R29", "label": "met en œuvre", "relation_type": "est mise en œuvre par", "peer_type": "operation"},
        {"direction": "outgoing", "relation_id": "R19", "label": "compose", "relation_type": "compose", "peer_type": "quartier_applicatif"},
        {"direction": "outgoing", "relation_id": "R21", "label": "est accessible via", "relation_type": "est accessible via", "peer_type": "poste_travail"},
        {"direction": "outgoing", "relation_id": "R22", "label": "est accessible via", "relation_type": "est accessible via", "peer_type": "byod"},
    ],
    "quartier_applicatif": [
        {"direction": "incoming", "relation_id": "R19", "label": "est composé de", "relation_type": "compose", "peer_type": "ilot_applicatif"},
        {"direction": "outgoing", "relation_id": "R20", "label": "compose", "relation_type": "compose", "peer_type": "zone_applicative"},
    ],
    "zone_applicative": [
        {"direction": "incoming", "relation_id": "R20", "label": "est composée de", "relation_type": "compose", "peer_type": "quartier_applicatif"},
    ],
    "poste_travail": [
        {"direction": "incoming", "relation_id": "R23", "label": "est utilisé par", "relation_type": "utilise", "peer_type": "acteur"},
        {"direction": "incoming", "relation_id": "R21", "label": "donne accès à", "relation_type": "est accessible via", "peer_type": "ilot_applicatif"},
        {"direction": "outgoing", "relation_id": "R25", "label": "est connecté à", "relation_type": "est connecté à", "peer_type": "serveur"},
        {"direction": "outgoing", "relation_id": "R26", "label": "est connecté à", "relation_type": "est connecté à", "peer_type": "reseau"},
    ],
    "byod": [
        {"direction": "incoming", "relation_id": "R24", "label": "est utilisé par", "relation_type": "utilise", "peer_type": "acteur"},
        {"direction": "incoming", "relation_id": "R22", "label": "donne accès à", "relation_type": "est accessible via", "peer_type": "ilot_applicatif"},
        {"direction": "outgoing", "relation_id": "R27", "label": "est connecté à", "relation_type": "est connecté à", "peer_type": "reseau"},
    ],
    "serveur": [
        {"direction": "incoming", "relation_id": "R25", "label": "est connecté à", "relation_type": "est connecté à", "peer_type": "poste_travail"},
        {"direction": "outgoing", "relation_id": "R28", "label": "est hébergé sur", "relation_type": "est hébergé sur", "peer_type": "site"},
    ],
    "reseau": [
        {"direction": "incoming", "relation_id": "R26", "label": "est connecté à", "relation_type": "est connecté à", "peer_type": "poste_travail"},
        {"direction": "incoming", "relation_id": "R27", "label": "est connecté à", "relation_type": "est connecté à", "peer_type": "byod"},
    ],
    "site": [
        {"direction": "incoming", "relation_id": "R28", "label": "héberge", "relation_type": "est hébergé sur", "peer_type": "serveur"},
    ],
    "systeme_information": [
        {"direction": "incoming", "relation_id": "R01", "label": "est commandé par", "relation_type": "commande", "peer_type": "metier"},
    ],
}

ENTITY_BY_ID = {e["id"]: e for e in ENTITY_TYPES}


def get_entity_meta(entity_type: str) -> dict[str, str] | None:
    return ENTITY_BY_ID.get(entity_type)


def allowed_relations_for_source(source_type: str) -> list[dict[str, Any]]:
    return [r for r in RELATION_RULES if r["source"] == source_type]


def allowed_relations_for_target(target_type: str) -> list[dict[str, Any]]:
    return [r for r in RELATION_RULES if r["target"] == target_type]


def validate_relation(source_type: str, relation_type: str, target_type: str) -> bool:
    return any(
        r["source"] == source_type and r["type"] == relation_type and r["target"] == target_type
        for r in RELATION_RULES
    )


def get_creation_guide(entity_type: str) -> list[dict[str, str]]:
    return ENTITY_CREATION_GUIDE.get(entity_type, [])


def _relation_key(r: dict[str, Any]) -> tuple[str, str, str]:
    return (r["source"], r["type"], r["target"])


def validate_metamodel_implementation() -> dict[str, Any]:
    """Compare le moteur implémenté au contrat Club Urba R01–R30."""
    implemented_entities = {e["id"] for e in ENTITY_TYPES}
    expected_entities = set(REFERENCE_ENTITY_IDS)

    ref_by_id = {r["id"]: r for r in REFERENCE_RELATIONS}
    impl_by_key = {_relation_key(r): r for r in RELATION_RULES}
    ref_by_key = {_relation_key(r): r for r in REFERENCE_RELATIONS}

    missing_entities = sorted(expected_entities - implemented_entities)
    extra_entities = sorted(implemented_entities - expected_entities - {"systeme_information"})

    missing_relations = [
        ref_by_id[rid]
        for rid in sorted(ref_by_id)
        if _relation_key(ref_by_id[rid]) not in impl_by_key
    ]
    invalid_relations = [
        r for key, r in impl_by_key.items()
        if key not in ref_by_key
    ]

    implemented_relations = list(RELATION_RULES)
    expected_relations = list(REFERENCE_RELATIONS)

    return {
        "status": "ok" if not missing_entities and not missing_relations and not invalid_relations else "ko",
        "expected_entities": [
            {**ENTITY_BY_ID[eid], "required": True}
            for eid in REFERENCE_ENTITY_IDS
            if eid in ENTITY_BY_ID
        ] + [{"id": "systeme_information", "label": "Système d'information", "couche": "transverse", "required": False, "note": "Requis par R01"}],
        "missing_entities": missing_entities,
        "extra_entities": extra_entities,
        "expected_relations": expected_relations,
        "implemented_relations": implemented_relations,
        "missing_relations": missing_relations,
        "invalid_relations": invalid_relations,
        "summary": {
            "entities_expected": len(expected_entities),
            "entities_implemented": len(implemented_entities),
            "relations_expected": len(expected_relations),
            "relations_implemented": len(implemented_relations),
            "relations_missing_count": len(missing_relations),
            "relations_invalid_count": len(invalid_relations),
        },
    }


def list_metamodel() -> dict[str, Any]:
    from app.metamodel.entity_profiles import ENTITY_PROFILES

    return {
        "entity_types": ENTITY_TYPES,
        "relation_rules": RELATION_RULES,
        "relation_categories": RELATION_CATEGORIES,
        "couches": [{"id": k, "label": v, "color": COUCHE_COLORS[k]} for k, v in COUCHE_LABELS.items()],
        "creation_guides": ENTITY_CREATION_GUIDE,
        "entity_profiles": {
            k: {
                "creation_order": v["creation_order"],
                "progress_group": v["progress_group"],
                "field_count": len(v["fields"]),
            }
            for k, v in ENTITY_PROFILES.items()
        },
        "reference_relation_ids": [r["id"] for r in REFERENCE_RELATIONS],
    }
