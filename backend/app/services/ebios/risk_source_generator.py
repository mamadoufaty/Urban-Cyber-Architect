"""Génération automatique de propositions Atelier 2 — sources de risque.

Fonctions pures (aucun accès base de données) : elles analysent l'Atelier 1
validé (parties prenantes, périmètre), la cartographie active et les biens
supports déjà synchronisés pour proposer un jeu de sources de risque
génériques EBIOS RM (Cybercriminel, Employé malveillant, APT, …), chacune
liée à un objectif visé, un événement redouté, des parties prenantes et des
biens supports.

Chaque proposition est **explicable** : elle porte une justification
(``properties.justification``, une liste de faits cartographiques ayant
motivé la proposition) et un niveau de confiance indicatif
(``properties.confidence_score``/``confidence_label``) destinés à accélérer
la revue par un RSSI — ces deux champs sont purement informatifs et n'ont
aucun effet sur la progression de l'atelier.

Le générateur est également **contextuel** : une archétype de source de
risque n'est proposée que si la cartographie contient les éléments qui la
justifient (ex. pas de « Prestataire » sans signal de prestataire/contrat,
pas de « Défaillance technique » sans composant technique).

Toute proposition porte sa traçabilité (``properties.generated_from``) et
n'est **jamais** considérée comme validée : l'orchestration
(:mod:`workshop2_service`) matérialise chaque proposition avec
``status="proposed"``, à valider, modifier ou rejeter explicitement par
l'utilisateur.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Callable
from uuid import UUID

from app.models.entities import UrbanismEntity
from app.models.ebios import EbiosRecord

SOURCE_CARTOGRAPHY = "cartography"

_OBJECTIVE_ENTITY_TYPES = {"metier", "objectif", "processus", "activite"}

_OT_KEYWORDS = ("ot", "scada", "automate", "industriel", "capteur", "ics", "iot")
_CONTRACT_KEYWORDS = ("contrat", "prestataire", "sous-traitant", "fournisseur", "infogérance")


def _keyword_matches(haystack: str, keyword: str) -> bool:
    return re.search(rf"\b{re.escape(keyword)}\b", haystack) is not None


@dataclass(frozen=True)
class _Context:
    """Statistiques cartographiques utilisées pour la justification, le score
    de confiance et l'adaptation contextuelle des propositions."""

    metier_count: int
    applicatif_count: int
    technique_count: int
    organisation_count: int
    flux_count: int
    has_ot: bool
    contract_entity_count: int
    has_prestataire_stakeholder: bool

    @property
    def has_prestataire_signal(self) -> bool:
        return self.contract_entity_count > 0 or self.has_prestataire_stakeholder


def _build_context(
    entities: list[UrbanismEntity], stakeholder_records: list[EbiosRecord]
) -> _Context:
    def _count(couche: str) -> int:
        return sum(1 for e in entities if e.couche == couche)

    def _mentions(entity: UrbanismEntity, keywords: tuple[str, ...]) -> bool:
        haystack = f"{entity.label or ''} {entity.description or ''}".lower()
        return any(_keyword_matches(haystack, kw) for kw in keywords)

    flux_count = sum(
        len((e.properties or {}).get("import_flux") or [])
        for e in entities
        if e.couche == "applicatif"
    )
    has_ot = any(_mentions(e, _OT_KEYWORDS) for e in entities)
    contract_entity_count = sum(1 for e in entities if _mentions(e, _CONTRACT_KEYWORDS))
    has_prestataire_stakeholder = any(
        str((s.properties or {}).get("role", "")) == "Prestataire" for s in stakeholder_records
    )

    return _Context(
        metier_count=_count("metier"),
        applicatif_count=_count("applicatif"),
        technique_count=_count("technique"),
        organisation_count=_count("organisation"),
        flux_count=flux_count,
        has_ot=has_ot,
        contract_entity_count=contract_entity_count,
        has_prestataire_stakeholder=has_prestataire_stakeholder,
    )


def _requires_technique(ctx: _Context) -> bool:
    return ctx.technique_count > 0


def _requires_prestataire_signal(ctx: _Context) -> bool:
    return ctx.has_prestataire_signal


def _always_applicable(_ctx: _Context) -> bool:
    return True


# (libellé, événement redouté, gravité par défaut, couches de biens supports
# privilégiées, rôles de parties prenantes privilégiés, condition
# d'applicabilité). Une liste vide pour les couches/rôles signifie « aucune
# préférence » : la sélection retombe alors sur l'ensemble disponible.
_RISK_SOURCE_ARCHETYPES: list[dict[str, Any]] = [
    {
        "label": "Cybercriminel",
        "feared_event": (
            "Vol, chiffrement (rançongiciel) ou destruction de données à des fins "
            "d'extorsion financière"
        ),
        "severity": "Critique",
        "asset_couches": {"applicatif", "technique"},
        "stakeholder_roles": (),
        "applicable": _always_applicable,
    },
    {
        "label": "Employé malveillant",
        "feared_event": (
            "Sabotage, vol ou divulgation d'informations sensibles par un collaborateur interne"
        ),
        "severity": "Élevée",
        "asset_couches": {"applicatif", "organisation"},
        "stakeholder_roles": (),
        "applicable": _always_applicable,
    },
    {
        "label": "Prestataire",
        "feared_event": (
            "Compromission ou usage abusif des accès accordés à un prestataire externe"
        ),
        "severity": "Élevée",
        "asset_couches": {"applicatif", "technique"},
        "stakeholder_roles": ("Prestataire",),
        "applicable": _requires_prestataire_signal,
    },
    {
        "label": "Sous-traitant",
        "feared_event": "Défaillance ou compromission d'un maillon de la chaîne de sous-traitance",
        "severity": "Modérée",
        "asset_couches": {"applicatif", "technique"},
        "stakeholder_roles": ("Prestataire",),
        "applicable": _requires_prestataire_signal,
    },
    {
        "label": "Concurrent",
        "feared_event": "Espionnage industriel ou captation d'informations stratégiques",
        "severity": "Modérée",
        "asset_couches": {"metier", "applicatif"},
        "stakeholder_roles": (),
        "applicable": _always_applicable,
    },
    {
        "label": "APT (menace persistante avancée)",
        "feared_event": (
            "Intrusion prolongée et furtive visant l'exfiltration ou le sabotage stratégique"
        ),
        "severity": "Critique",
        "asset_couches": {"applicatif", "technique"},
        "stakeholder_roles": (),
        "applicable": _always_applicable,
    },
    {
        "label": "Erreur humaine",
        "feared_event": (
            "Perte, altération ou divulgation accidentelle de données ou de configuration"
        ),
        "severity": "Modérée",
        "asset_couches": {"applicatif", "technique", "organisation"},
        "stakeholder_roles": (),
        "applicable": _always_applicable,
    },
    {
        "label": "Défaillance technique",
        "feared_event": (
            "Indisponibilité ou dégradation du service suite à une panne matérielle ou logicielle"
        ),
        "severity": "Élevée",
        "asset_couches": {"technique"},
        "stakeholder_roles": ("Responsable technique", "Responsable infrastructure"),
        "applicable": _requires_technique,
    },
    {
        "label": "Catastrophe naturelle",
        "feared_event": (
            "Destruction ou indisponibilité prolongée des infrastructures suite à un sinistre "
            "majeur"
        ),
        "severity": "Critique",
        "asset_couches": {"technique"},
        "stakeholder_roles": (),
        "applicable": _requires_technique,
    },
]

_MAX_LINKED_ASSETS = 8
_MAX_LINKED_STAKEHOLDERS = 6


def _traceability(
    cartography_id: UUID | None, cartography_version_id: UUID | None, entity_ids: list[str]
) -> dict[str, Any]:
    return {
        "source": SOURCE_CARTOGRAPHY,
        "cartography_id": str(cartography_id) if cartography_id else None,
        "cartography_version_id": str(cartography_version_id) if cartography_version_id else None,
        "entity_ids": entity_ids,
    }


def _derive_target_objective(
    entities: list[UrbanismEntity], scope_record: EbiosRecord | None
) -> tuple[str, bool]:
    """Objectif visé déduit en priorité du périmètre Atelier 1 validé (métiers,
    processus), sinon des entités métier/processus de la cartographie active.
    Retourne aussi si la déduction provient bien du périmètre validé (fiabilité
    plus élevée que le repli sur la cartographie brute)."""
    if scope_record is not None:
        props = scope_record.properties or {}
        parts = [
            str(props.get("business_objectives", "")).strip(),
            str(props.get("activities", "")).strip(),
        ]
        parts = [p for p in parts if p]
        if parts:
            return " ; ".join(parts), True

    objective_entities = [e.label for e in entities if e.entity_type in _OBJECTIVE_ENTITY_TYPES]
    if objective_entities:
        return ", ".join(objective_entities[:8]), False

    return "Continuité et sécurité des activités du périmètre étudié", False


def _select_assets(
    supporting_assets: list[EbiosRecord], couches: set[str]
) -> tuple[list[EbiosRecord], bool]:
    """Retourne les biens supports sélectionnés et si la sélection correspond
    réellement à la couche privilégiée (``False`` si repli sur l'ensemble)."""
    if couches:
        matching = [a for a in supporting_assets if (a.properties or {}).get("couche") in couches]
        if matching:
            return matching[:_MAX_LINKED_ASSETS], True
    return list(supporting_assets)[:_MAX_LINKED_ASSETS], False


def _select_stakeholders(
    stakeholders: list[EbiosRecord], roles: tuple[str, ...]
) -> tuple[list[EbiosRecord], bool]:
    """Retourne les parties prenantes sélectionnées et si la sélection
    correspond réellement au(x) rôle(s) privilégié(s) (``False`` si repli)."""
    if roles:
        matching = [s for s in stakeholders if str((s.properties or {}).get("role", "")) in roles]
        if matching:
            return matching[:_MAX_LINKED_STAKEHOLDERS], True
    return list(stakeholders)[:_MAX_LINKED_STAKEHOLDERS], False


def _confidence_score(
    *, objective_from_scope: bool, assets_matched: bool, stakeholders_matched: bool, contributing: int
) -> int:
    score = 45
    if objective_from_scope:
        score += 15
    if assets_matched:
        score += 15
    if stakeholders_matched:
        score += 15
    score += min(10, contributing)
    return min(96, score)


def _confidence_label(score: int) -> str:
    if score >= 80:
        return "Élevée"
    if score >= 55:
        return "Moyenne"
    return "Faible"


def _justification_bullets(
    spec: dict[str, Any],
    ctx: _Context,
    *,
    assets_matched: bool,
    stakeholders_matched: bool,
    linked_asset_count: int,
    linked_stakeholder_count: int,
) -> list[str]:
    couches: set[str] = spec["asset_couches"]
    bullets: list[str] = []

    if (not couches or "applicatif" in couches) and ctx.applicatif_count:
        bullets.append(f"{ctx.applicatif_count} application(s) recensée(s) dans la cartographie")
    if (not couches or "technique" in couches) and ctx.technique_count:
        bullets.append(f"{ctx.technique_count} composant(s) technique(s) recensé(s)")
    if (not couches or "metier" in couches) and ctx.metier_count:
        bullets.append(f"{ctx.metier_count} métier(s)/processus recensé(s)")
    if (not couches or "organisation" in couches) and ctx.organisation_count:
        bullets.append(f"{ctx.organisation_count} organisation(s)/direction(s) recensée(s)")
    if ctx.flux_count and (not couches or couches & {"applicatif", "technique"}):
        bullets.append(f"{ctx.flux_count} flux réseau recensé(s)")
    if ctx.has_ot and (not couches or "technique" in couches):
        bullets.append("Présence de composants OT dans la cartographie")
    if spec["applicable"] is _requires_prestataire_signal and ctx.contract_entity_count:
        bullets.append(
            f"{ctx.contract_entity_count} élément(s) évoquant un contrat/prestataire détecté(s)"
        )
    if ctx.technique_count + ctx.applicatif_count >= 5:
        bullets.append("Plusieurs dépendances techniques et applicatives")

    if assets_matched:
        bullets.append(f"{linked_asset_count} bien(s) support directement concerné(s)")
    else:
        bullets.append("Aucune correspondance directe de couche — biens supports proposés par défaut")

    if stakeholders_matched:
        bullets.append(
            f"{linked_stakeholder_count} partie(s) prenante(s) au rôle concordant (Atelier 1)"
        )

    if not bullets:
        bullets.append("Analyse générique EBIOS RM — cartographie disponible mais peu détaillée")

    return bullets[:6]


def build_risk_source_proposals(
    entities: list[UrbanismEntity],
    scope_record: EbiosRecord | None,
    stakeholder_records: list[EbiosRecord],
    supporting_asset_records: list[EbiosRecord],
    cartography_id: UUID | None,
    cartography_version_id: UUID | None,
) -> list[dict[str, Any]]:
    """Un jeu de sources de risque EBIOS RM contextualisées, chacune liée à un
    objectif visé, un événement redouté, des parties prenantes et des biens
    supports pertinents, avec justification et score de confiance — toujours
    à l'état ``proposed``.

    Seules les archétypes cohérentes avec la cartographie active sont
    proposées (ex. pas de « Prestataire » sans signal de prestataire/contrat,
    pas de source de risque technique sans composant technique modélisé)."""
    ctx = _build_context(entities, stakeholder_records)
    target_objective, objective_from_scope = _derive_target_objective(entities, scope_record)
    contributing_ids = [str(e.id) for e in entities if e.entity_type in _OBJECTIVE_ENTITY_TYPES]

    proposals: list[dict[str, Any]] = []
    for spec in _RISK_SOURCE_ARCHETYPES:
        applicable: Callable[[_Context], bool] = spec["applicable"]
        if not applicable(ctx):
            continue

        linked_assets, assets_matched = _select_assets(
            supporting_asset_records, spec["asset_couches"]
        )
        linked_stakeholders, stakeholders_matched = _select_stakeholders(
            stakeholder_records, spec["stakeholder_roles"]
        )

        confidence_score = _confidence_score(
            objective_from_scope=objective_from_scope,
            assets_matched=assets_matched,
            stakeholders_matched=stakeholders_matched,
            contributing=len(contributing_ids),
        )
        justification = _justification_bullets(
            spec,
            ctx,
            assets_matched=assets_matched,
            stakeholders_matched=stakeholders_matched,
            linked_asset_count=len(linked_assets),
            linked_stakeholder_count=len(linked_stakeholders),
        )

        proposals.append(
            {
                "label": spec["label"],
                "description": spec["feared_event"],
                "properties": {
                    "target_objective": target_objective,
                    "feared_event": spec["feared_event"],
                    "severity": spec["severity"],
                    "stakeholder_ids": [str(s.id) for s in linked_stakeholders],
                    "supporting_asset_ids": [str(a.id) for a in linked_assets],
                    "comment": (
                        "Proposition générée automatiquement depuis la cartographie active et "
                        "l'Atelier 1 validé — à valider, modifier ou rejeter."
                    ),
                    "justification": justification,
                    "confidence_score": confidence_score,
                    "confidence_label": _confidence_label(confidence_score),
                    "scenario_seed": {"strategic_ready": True, "operational_ready": False},
                    "generated_from": _traceability(
                        cartography_id, cartography_version_id, contributing_ids
                    ),
                },
            }
        )

    return proposals
