"""Génération des mesures de sécurité — moteur remplaçable (IA / référentiels)."""

from __future__ import annotations

import uuid
from typing import Any

TREATMENT_DECISIONS = ("Accepter", "Réduire", "Transférer", "Éviter")
WORKFLOW_AUTO = "Proposé automatiquement"
WORKFLOW_IN_PROGRESS = "En cours"
WORKFLOW_VALIDATED = "Validé"

_FRAMEWORK_TEMPLATE = {
    "iso27002": "",
    "nist_csf": "",
    "cis_controls": "",
    "anssi": "",
}


def generate_security_measures(operational_context: dict[str, Any]) -> list[dict[str, Any]]:
    """Propose des mesures à partir du scénario opérationnel (sans appel IA)."""
    entry = str(operational_context.get("entry_point", "")).lower()
    technical = str(operational_context.get("technical_event", "")).lower()
    actor = str(operational_context.get("threatening_actor", "")).lower()
    measures: list[dict[str, Any]] = []

    if "phishing" in entry or "phishing" in actor:
        measures.append(
            _measure(
                "Campagne de sensibilisation anti-phishing",
                "Former les utilisateurs à détecter les courriels malveillants.",
                iso27002="6.3",
                nist="PR.AT-1",
                cis="CIS 14.1",
                anssi="Guide hygiène informatique",
            )
        )
        measures.append(
            _measure(
                "Filtrage anti-phishing sur la messagerie",
                "Déployer une solution de détection des messages frauduleux.",
                iso27002="8.23",
                nist="DE.CM-1",
                cis="CIS 9.2",
                anssi="EBIOS — réduction exposition",
            )
        )

    if "ransom" in technical or "ransom" in actor:
        measures.append(
            _measure(
                "Sauvegardes isolées et tests de restauration",
                "Garantir la récupération sans paiement de rançon.",
                iso27002="8.13",
                nist="PR.IP-4",
                cis="CIS 11.1",
                anssi="PGSSI-S — continuité",
            )
        )
        measures.append(
            _measure(
                "Segmentation réseau des systèmes critiques",
                "Limiter la propagation latérale en cas de compromission.",
                iso27002="8.22",
                nist="PR.AC-5",
                cis="CIS 13.3",
                anssi="ANSSI — cloisonnement",
            )
        )

    if "vpn" in str(operational_context.get("attack_path", "")).lower():
        measures.append(
            _measure(
                "Renforcement de l'authentification VPN (MFA)",
                "Réduire le risque d'accès via identifiants volés.",
                iso27002="8.5",
                nist="PR.AC-7",
                cis="CIS 6.3",
                anssi="Recommandations ANSSI IAM",
            )
        )

    if not measures:
        measures.append(
            _measure(
                "Revue des contrôles de sécurité applicables",
                "Analyser et renforcer les mesures existantes sur le périmètre concerné.",
                iso27002="5.36",
                nist="ID.RA-5",
                cis="CIS 1.1",
                anssi="EBIOS — traitement du risque",
            )
        )

    return measures


def _measure(
    label: str,
    description: str,
    *,
    iso27002: str,
    nist: str,
    cis: str,
    anssi: str,
) -> dict[str, Any]:
    return {
        "measure_uid": str(uuid.uuid4()),
        "label": label,
        "description": description,
        "auto_generated": True,
        "retained": True,
        "framework_refs": {
            "iso27002": iso27002,
            "nist_csf": nist,
            "cis_controls": cis,
            "anssi": anssi,
        },
        "grc_seed": {"soa_ready": True, "ptr_ready": True},
    }


def generate_ptr_action(
    measure: dict[str, Any],
    responsible_actor: dict | None,
    *,
    priority: str = "Haute",
) -> dict[str, Any]:
    actor_id = (responsible_actor or {}).get("urbanism_entity_id", "")
    return {
        "action_uid": str(uuid.uuid4()),
        "measure_uid": measure.get("measure_uid"),
        "label": measure.get("label"),
        "responsible_actor_id": actor_id,
        "responsible_actor_label": (responsible_actor or {}).get("label", ""),
        "due_date": "",
        "priority": priority,
        "budget": None,
        "status": "Planifié",
        "grc_seed": {"risk_register_ready": True, "ptr_ready": True},
    }
