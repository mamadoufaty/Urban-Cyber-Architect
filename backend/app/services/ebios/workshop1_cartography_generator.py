"""Génération automatique de propositions Atelier 1 depuis la cartographie active.

Fonctions pures (aucun accès base de données) : elles analysent le graphe
d'urbanisme déjà chargé (organisations, métiers, processus, activités,
applications, composants techniques…) et proposent un périmètre étudié, des
parties prenantes et un socle de sécurité de départ.

Toute proposition porte sa traçabilité (``properties.generated_from``) — les
entités urbanisme exactes ayant permis de la construire — et n'est **jamais**
considérée comme validée : l'orchestration (:mod:`workshop1_service`)
matérialise chaque proposition avec ``status="proposed"``, à valider,
modifier ou rejeter explicitement par l'utilisateur.
"""

from __future__ import annotations

import re
from typing import Any
from uuid import UUID

from app.models.entities import UrbanismEntity, UrbanismRelation

SOURCE_CARTOGRAPHY = "cartography"

_SCOPE_METIER_TYPES = {"metier", "objectif"}
_SCOPE_ACTIVITY_TYPES = {"processus", "activite"}
_SCOPE_APPLICATION_TYPES = {"ilot_applicatif", "quartier_applicatif", "zone_applicative"}
_SCOPE_SITE_TYPES = {"site"}

# Socle de sécurité — domaines proposés lorsque la cartographie contient au
# moins une entité du couche/type correspondant.
_BASELINE_DOMAINS: list[dict[str, Any]] = [
    {
        "domain": "Sécurité applicative",
        "entity_types": {"ilot_applicatif", "quartier_applicatif", "zone_applicative"},
        "iso27002_ref": "8.25 — Cycle de vie du développement sécurisé",
    },
    {
        "domain": "Sécurité des serveurs et de l'hébergement",
        "entity_types": {"serveur", "site"},
        "iso27002_ref": "8.9 — Gestion des configurations",
    },
    {
        "domain": "Sécurité réseau",
        "entity_types": {"reseau"},
        "iso27002_ref": "8.20 — Sécurité des réseaux",
    },
    {
        "domain": "Sécurité des postes de travail et du BYOD",
        "entity_types": {"poste_travail", "byod"},
        "iso27002_ref": "8.1 — Dispositifs terminaux utilisateurs",
    },
    {
        "domain": "Gouvernance et organisation de la sécurité",
        "entity_types": {"organisation", "acteur", "procedure"},
        "iso27002_ref": "5.2 — Rôles et responsabilités liées à la sécurité",
    },
]

# (mot-clé, rôle, correspondance exacte du mot). Les acronymes courts (rssi,
# dsi, soc, ot…) exigent une frontière de mot des deux côtés pour éviter les
# faux positifs (« société » ne doit jamais matcher « soc »).
_ROLE_KEYWORDS: list[tuple[str, str, bool]] = [
    ("rssi", "RSSI", True),
    ("dsi", "DSI", True),
    ("dpo", "DPO", True),
    ("soc", "Responsable SOC", True),
    ("ot", "Responsable OT", True),
    ("direction générale", "Direction générale", False),
    ("direction generale", "Direction générale", False),
    ("systèmes d'information", "DSI", False),
    ("système d'information", "DSI", False),
    ("sponsor", "Sponsor", False),
    ("audit", "Auditeur", False),
    ("prestataire", "Prestataire", False),
    ("sous-traitant", "Prestataire", False),
    ("exploitation", "Responsable exploitation", False),
    ("urbanisme", "Responsable urbanisme SI", False),
    ("infrastructure", "Responsable infrastructure", False),
    ("réseau", "Responsable infrastructure", False),
    ("reseau", "Responsable infrastructure", False),
    ("applicatif", "Responsable application", False),
    ("application", "Responsable application", False),
    ("technique", "Responsable technique", False),
    ("métier", "Responsable métier", False),
    ("metier", "Responsable métier", False),
]


def _keyword_matches(haystack: str, keyword: str, exact: bool) -> bool:
    pattern = rf"\b{re.escape(keyword)}\b" if exact else rf"\b{re.escape(keyword)}"
    return re.search(pattern, haystack) is not None


def _guess_role(label: str) -> str:
    lowered = label.lower()
    for keyword, role, exact in _ROLE_KEYWORDS:
        if _keyword_matches(lowered, keyword, exact):
            return role
    return "Autre"


def _traceability(
    cartography_id: UUID | None, cartography_version_id: UUID | None, entity_ids: list[str]
) -> dict[str, Any]:
    return {
        "source": SOURCE_CARTOGRAPHY,
        "cartography_id": str(cartography_id) if cartography_id else None,
        "cartography_version_id": str(cartography_version_id) if cartography_version_id else None,
        "entity_ids": entity_ids,
    }


def build_scope_proposal(
    entities: list[UrbanismEntity],
    cartography_id: UUID | None,
    cartography_version_id: UUID | None,
) -> dict[str, Any] | None:
    """Propose un périmètre étudié unique à partir des couches métier/applicatif."""

    def _matching(types: set[str]) -> list[UrbanismEntity]:
        return [e for e in entities if e.entity_type in types]

    metiers = _matching(_SCOPE_METIER_TYPES)
    activities = _matching(_SCOPE_ACTIVITY_TYPES)
    applications = _matching(_SCOPE_APPLICATION_TYPES)
    sites = _matching(_SCOPE_SITE_TYPES)
    contributing = metiers + activities + applications + sites
    if not contributing:
        return None

    return {
        "label": "Périmètre proposé depuis la cartographie",
        "description": (
            f"Généré automatiquement à partir de {len(contributing)} élément(s) de la "
            "cartographie active — à valider ou ajuster."
        ),
        "properties": {
            "business_objectives": ", ".join(e.label for e in metiers),
            "activities": ", ".join(e.label for e in activities),
            "applications": ", ".join(e.label for e in applications),
            "sites": ", ".join(e.label for e in sites),
            "regulatory_constraints": "",
            "generated_from": _traceability(
                cartography_id, cartography_version_id, [str(e.id) for e in contributing]
            ),
        },
    }


def _linked_organisation(
    acteur: UrbanismEntity,
    entities_by_id: dict[str, UrbanismEntity],
    relations: list[UrbanismRelation],
) -> UrbanismEntity | None:
    acteur_id = str(acteur.id)
    for rel in relations:
        if str(rel.source_id) == acteur_id:
            target = entities_by_id.get(str(rel.target_id))
            if target and target.entity_type == "organisation":
                return target
        if str(rel.target_id) == acteur_id:
            source = entities_by_id.get(str(rel.source_id))
            if source and source.entity_type == "organisation":
                return source
    return None


def build_stakeholder_proposals(
    entities: list[UrbanismEntity],
    relations: list[UrbanismRelation],
    cartography_id: UUID | None,
    cartography_version_id: UUID | None,
) -> list[dict[str, Any]]:
    """Une proposition de partie prenante par acteur nommé ET par organisation/
    direction/service du graphe urbanisme — une cartographie qui ne modélise
    aucun « acteur » individuel mais des organisations (directions, services)
    ne doit jamais produire une section Parties prenantes vide."""
    entities_by_id = {str(e.id): e for e in entities}
    proposals: list[dict[str, Any]] = []

    for acteur in entities:
        if acteur.entity_type != "acteur":
            continue
        organisation = _linked_organisation(acteur, entities_by_id, relations)
        proposals.append(
            {
                "label": acteur.label,
                "properties": {
                    "role": _guess_role(acteur.label),
                    "organization": organisation.label if organisation else "",
                    "responsibility": acteur.description or "",
                    "contact": "",
                    "involvement_level": "",
                    "generated_from": _traceability(
                        cartography_id, cartography_version_id, [str(acteur.id)]
                    ),
                },
            }
        )

    for organisation in entities:
        if organisation.entity_type != "organisation":
            continue
        proposals.append(
            {
                "label": organisation.label,
                "properties": {
                    "role": _guess_role(organisation.label),
                    "organization": organisation.label,
                    "responsibility": organisation.description or "",
                    "contact": "",
                    "involvement_level": "",
                    "generated_from": _traceability(
                        cartography_id, cartography_version_id, [str(organisation.id)]
                    ),
                },
            }
        )

    return proposals


# Rôles organisationnels génériques — utilisés uniquement quand la
# cartographie ne contient aucun acteur ni organisation nommés (§ Si aucune
# personne physique n'est connue). Chaque rôle n'est proposé que si la
# cartographie contient effectivement le type d'élément qui le justifie
# (ex. « Responsable OT » seulement si des éléments industriels/OT existent).
_FALLBACK_ROLE_SPECS: list[dict[str, Any]] = [
    {"role": "Direction générale", "always": True},
    {"role": "DSI", "always": True},
    {"role": "RSSI", "always": True},
    {
        "role": "Responsable métier",
        "entity_types": {"metier", "objectif", "processus", "activite", "client", "resultat", "evenement"},
    },
    {
        "role": "Responsable application",
        "entity_types": {"ilot_applicatif", "quartier_applicatif", "zone_applicative"},
    },
    {
        "role": "Responsable technique",
        "entity_types": {"serveur", "reseau", "poste_travail", "byod"},
    },
    {
        "role": "Responsable exploitation",
        "entity_types": {"operation", "procedure"},
    },
    {
        "role": "Responsable urbanisme SI",
        "entity_types": {
            "systeme_information",
            "ilot_fonctionnel",
            "quartier_fonctionnel",
            "zone_fonctionnelle",
            "ilot_applicatif",
        },
    },
    {
        "role": "Responsable SOC",
        "entity_types": {"serveur", "reseau"},
    },
    {
        "role": "Responsable OT",
        "keywords": ("ot", "scada", "automate", "industriel", "capteur", "ics", "iot"),
    },
    {
        "role": "Responsable infrastructure",
        "entity_types": {"serveur", "reseau", "site", "poste_travail", "byod"},
    },
]


def build_fallback_stakeholder_role_proposals(
    entities: list[UrbanismEntity],
    cartography_id: UUID | None,
    cartography_version_id: UUID | None,
) -> list[dict[str, Any]]:
    """Rôles organisationnels proposés quand aucune personne physique ni
    organisation n'est identifiable dans la cartographie — l'utilisateur les
    remplace ensuite par les personnes réelles si nécessaire."""

    def _keyword_matches_entities(keywords: tuple[str, ...]) -> list[UrbanismEntity]:
        matches = []
        for entity in entities:
            haystack = f"{entity.label or ''} {entity.description or ''}".lower()
            if any(_keyword_matches(haystack, keyword, True) for keyword in keywords):
                matches.append(entity)
        return matches

    proposals: list[dict[str, Any]] = []
    for spec in _FALLBACK_ROLE_SPECS:
        if spec.get("always"):
            contributing = list(entities)
        elif "keywords" in spec:
            contributing = _keyword_matches_entities(spec["keywords"])
            if not contributing:
                continue
        else:
            entity_types: set[str] = spec.get("entity_types", set())
            contributing = [e for e in entities if e.entity_type in entity_types]
            if not contributing:
                continue

        proposals.append(
            {
                "label": spec["role"],
                "properties": {
                    "role": spec["role"],
                    "organization": "",
                    "responsibility": (
                        "Rôle organisationnel générique proposé faute d'acteur ou d'organisation "
                        "nommés dans la cartographie — à remplacer par la personne réelle si connue."
                    ),
                    "contact": "",
                    "involvement_level": "",
                    "generated_from": _traceability(
                        cartography_id,
                        cartography_version_id,
                        [str(e.id) for e in contributing],
                    ),
                },
            }
        )
    return proposals


_CONTRACT_KEYWORDS = ("contrat", "prestataire", "sous-traitant", "fournisseur", "infogérance")


def build_reference_document_proposals(
    entities: list[UrbanismEntity],
    cartography_id: UUID | None,
    cartography_version_id: UUID | None,
    cartography_label: str | None,
) -> list[dict[str, Any]]:
    """Complète le socle documentaire par défaut avec des documents détectés
    dans la cartographie active (jamais un doublon du socle par défaut —
    l'orchestrateur déduplique par libellé)."""
    proposals: list[dict[str, Any]] = []

    if entities and cartography_label:
        proposals.append(
            {
                "label": f"Cartographie d'urbanisme — {cartography_label}",
                "description": (
                    f"Cartographie active du système d'information ({len(entities)} élément(s))."
                ),
                "properties": {
                    "doc_type": "Autre",
                    "version": "",
                    "date": "",
                    "owner": "",
                    "link": "",
                    "comment": "Cartographie active utilisée comme source de l'étude EBIOS RM.",
                    "generated_from": _traceability(
                        cartography_id, cartography_version_id, [str(e.id) for e in entities]
                    ),
                },
            }
        )

    def _mentions_contract(entity: UrbanismEntity) -> bool:
        haystack = f"{entity.label or ''} {entity.description or ''}".lower()
        return any(keyword in haystack for keyword in _CONTRACT_KEYWORDS)

    contract_entities = [e for e in entities if _mentions_contract(e)]
    if contract_entities:
        proposals.append(
            {
                "label": "Contrats critiques (détectés)",
                "description": (
                    f"{len(contract_entities)} élément(s) de la cartographie évoquent un "
                    "contrat, prestataire ou sous-traitant — à documenter précisément."
                ),
                "properties": {
                    "doc_type": "Contrat",
                    "version": "",
                    "date": "",
                    "owner": "",
                    "link": "",
                    "comment": (
                        "Détecté depuis la cartographie active — à compléter avec les "
                        "références contractuelles exactes."
                    ),
                    "generated_from": _traceability(
                        cartography_id,
                        cartography_version_id,
                        [str(e.id) for e in contract_entities],
                    ),
                },
            }
        )

    return proposals


def build_baseline_proposals(
    entities: list[UrbanismEntity],
    cartography_id: UUID | None,
    cartography_version_id: UUID | None,
) -> list[dict[str, Any]]:
    """Un domaine de socle de sécurité proposé par grande famille technique/organisationnelle
    détectée dans la cartographie (statut « À vérifier » par défaut — jamais présumé en place)."""
    proposals: list[dict[str, Any]] = []
    for spec in _BASELINE_DOMAINS:
        matching = [e for e in entities if e.entity_type in spec["entity_types"]]
        if not matching:
            continue
        proposals.append(
            {
                "label": spec["domain"],
                "description": (
                    f"{len(matching)} élément(s) concerné(s) détecté(s) dans la cartographie "
                    "active — à vérifier."
                ),
                "properties": {
                    "domain": spec["domain"],
                    "status": "À vérifier",
                    "maturity_level": "1",
                    "iso27002_ref": spec["iso27002_ref"],
                    "generated_from": _traceability(
                        cartography_id, cartography_version_id, [str(e.id) for e in matching]
                    ),
                },
            }
        )
    return proposals
