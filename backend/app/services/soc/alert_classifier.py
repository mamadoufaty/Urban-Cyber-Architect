"""Normalisation des alertes Wazuh pour le moteur SOC."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class NormalizedAlert:
    alert_id: str
    timestamp: str
    rule_id: str
    rule_level: int
    rule_description: str
    agent_id: str
    agent_name: str
    agent_ip: str
    full_log: str
    groups: list[str] = field(default_factory=list)
    severity_label: str = ""
    category: str = ""
    raw: dict[str, Any] = field(default_factory=dict)


def _severity_from_level(level: int) -> str:
    if level >= 12:
        return "Critique"
    if level >= 8:
        return "Élevée"
    if level >= 5:
        return "Modérée"
    return "Faible"


def _category_from_groups(groups: list[str]) -> str:
    if not groups:
        return "générique"
    priority = ("authentication", "syscheck", "vulnerability", "pci", "attack", "malware")
    lowered = [g.lower() for g in groups]
    for key in priority:
        if any(key in g for g in lowered):
            return key
    return groups[0]


def classify_alert(alert: dict[str, Any]) -> NormalizedAlert:
    """Transforme une alerte Wazuh (connecteur) en alerte normalisée."""
    raw = alert.get("raw") or {}
    agent_block = raw.get("agent") if isinstance(raw, dict) else {}
    if not isinstance(agent_block, dict):
        agent_block = {}

    level = int(alert.get("rule_level") or 0)
    groups = list(alert.get("groups") or [])
    return NormalizedAlert(
        alert_id=str(alert.get("id") or ""),
        timestamp=str(alert.get("timestamp") or ""),
        rule_id=str(alert.get("rule_id") or ""),
        rule_level=level,
        rule_description=str(alert.get("rule_description") or ""),
        agent_id=str(alert.get("agent_id") or agent_block.get("id") or ""),
        agent_name=str(alert.get("agent_name") or agent_block.get("name") or ""),
        agent_ip=str(alert.get("agent_ip") or agent_block.get("ip") or ""),
        full_log=str(alert.get("full_log") or ""),
        groups=groups,
        severity_label=_severity_from_level(level),
        category=_category_from_groups(groups),
        raw=raw if isinstance(raw, dict) else alert,
    )
