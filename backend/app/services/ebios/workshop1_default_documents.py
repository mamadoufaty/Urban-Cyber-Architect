"""Socle documentaire par défaut — Atelier 1 EBIOS RM.

Les documents de référence d'une étude EBIOS RM ne doivent jamais dépendre
uniquement de la cartographie (qui ne modélise pas de « documents ») : dès la
création d'une étude, un jeu de documents usuels (méthode EBIOS RM, normes
ISO, PSSI, PCA/PRA, politiques transverses…) est proposé automatiquement,
avec ``status="proposed"`` et ``properties.source="default_framework"`` —
jamais validé d'office. Le générateur Atelier 1 (cartographie active) peut
ensuite compléter cette liste avec des documents réellement détectés dans le
projet (voir :mod:`workshop1_cartography_generator`).
"""

from __future__ import annotations

from typing import Any

SOURCE_DEFAULT_FRAMEWORK = "default_framework"

# (label, doc_type — cf. DOCUMENT_TYPES frontend, commentaire)
DEFAULT_REFERENCE_DOCUMENTS: list[dict[str, str]] = [
    {
        "label": "EBIOS RM v1.5",
        "doc_type": "Autre",
        "comment": "Référentiel méthodologique ANSSI / Club EBIOS utilisé pour l'étude.",
    },
    {
        "label": "ISO/IEC 27001:2022",
        "doc_type": "Norme ISO",
        "comment": "Système de management de la sécurité de l'information.",
    },
    {
        "label": "ISO/IEC 27002:2022",
        "doc_type": "Norme ISO",
        "comment": "Mesures de sécurité de référence.",
    },
    {
        "label": "PSSI",
        "doc_type": "PSSI",
        "comment": "Politique de sécurité des systèmes d'information — à rattacher si disponible.",
    },
    {
        "label": "Cartographie d'urbanisme",
        "doc_type": "Autre",
        "comment": "Cartographie du système d'information support de l'étude.",
    },
    {
        "label": "Dossier d'architecture",
        "doc_type": "Autre",
        "comment": "Architecture technique et applicative du périmètre étudié.",
    },
    {
        "label": "PCA",
        "doc_type": "PCA",
        "comment": "Plan de continuité d'activité.",
    },
    {
        "label": "PRA",
        "doc_type": "PRA",
        "comment": "Plan de reprise d'activité.",
    },
    {
        "label": "Politique IAM",
        "doc_type": "Politique de sécurité",
        "comment": "Politique de gestion des identités et des accès.",
    },
    {
        "label": "Politique de sauvegarde",
        "doc_type": "Politique de sécurité",
        "comment": "Politique de sauvegarde et de restauration des données.",
    },
    {
        "label": "Politique de journalisation",
        "doc_type": "Politique de sécurité",
        "comment": "Politique de journalisation et de traçabilité des événements.",
    },
    {
        "label": "Contrats critiques",
        "doc_type": "Contrat",
        "comment": "Contrats et clauses de sécurité des prestataires/tiers critiques — à rattacher si renseignés.",
    },
]


def build_default_reference_document_proposals() -> list[dict[str, Any]]:
    """Construit les propositions de documents de référence du socle par défaut."""
    proposals: list[dict[str, Any]] = []
    for spec in DEFAULT_REFERENCE_DOCUMENTS:
        proposals.append(
            {
                "label": spec["label"],
                "description": spec["comment"],
                "properties": {
                    "doc_type": spec["doc_type"],
                    "version": "",
                    "date": "",
                    "owner": "",
                    "link": "",
                    "comment": spec["comment"],
                    "source": SOURCE_DEFAULT_FRAMEWORK,
                },
            }
        )
    return proposals
