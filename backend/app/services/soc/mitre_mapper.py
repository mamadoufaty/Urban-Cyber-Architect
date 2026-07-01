"""Préparation enrichissement MITRE ATT&CK — lecture seule."""

from __future__ import annotations

from typing import Any

from app.services.soc.alert_classifier import NormalizedAlert

_GROUP_TO_MITRE_HINTS: dict[str, list[str]] = {
    "authentication": ["T1078", "T1110"],
    "syscheck": ["T1565", "T1485"],
    "vulnerability": ["T1190", "T1203"],
    "pci": ["T1046", "T1133"],
    "attack": ["T1059", "T1021"],
    "malware": ["T1204", "T1105"],
}


def map_mitre_from_alert(alert: NormalizedAlert) -> dict[str, Any]:
    """Produit un objet mitre_seed extensible sans appel externe."""
    techniques: list[str] = []
    for group in alert.groups:
        key = group.lower()
        for hint_key, hints in _GROUP_TO_MITRE_HINTS.items():
            if hint_key in key:
                techniques.extend(hints)

    if not techniques and alert.category in _GROUP_TO_MITRE_HINTS:
        techniques = list(_GROUP_TO_MITRE_HINTS[alert.category])

    techniques = list(dict.fromkeys(techniques))

    return {
        "mitre_ready": True,
        "tactics": [],
        "techniques": techniques,
        "technique_labels": [],
        "mapping_source": "rule_groups_heuristic",
        "confidence": 0.6 if techniques else 0.0,
    }
