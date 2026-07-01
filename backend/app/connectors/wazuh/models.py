"""Modèles de données — connecteur Wazuh."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class WazuhConnectionConfig:
    base_url: str = ""
    username: str = ""
    password: str = ""
    verify_ssl: bool = True
    indexer_url: str | None = None
    indexer_username: str | None = None
    indexer_password: str | None = None
    enabled: bool = False

    def is_configured(self) -> bool:
        return bool(self.base_url.strip() and self.username.strip() and self.password)

    def normalized_base_url(self) -> str:
        return self.base_url.rstrip("/")

    def resolved_indexer_url(self) -> str:
        if self.indexer_url and self.indexer_url.strip():
            return self.indexer_url.rstrip("/")
        base = self.normalized_base_url()
        if ":55000" in base:
            return base.replace(":55000", ":9200")
        return base

    def credentials_for_indexer(self) -> tuple[str, str]:
        """Identifiants indexer (dashboard/admin) ou repli sur l'utilisateur API manager."""
        user = (self.indexer_username or "").strip() or self.username.strip()
        pwd = self.indexer_password if self.indexer_password not in (None, "") else self.password
        return user, pwd


@dataclass
class WazuhAgent:
    id: str
    name: str
    ip: str
    status: str
    os: str = ""
    version: str = ""
    last_keep_alive: str = ""
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class WazuhAlert:
    id: str
    timestamp: str
    rule_id: str
    rule_level: int
    rule_description: str
    agent_id: str
    agent_name: str
    full_log: str = ""
    groups: list[str] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class WazuhStatus:
    connected: bool
    configured: bool
    wazuh_version: str = ""
    api_version: str = ""
    manager: str = ""
    agents_total: int = 0
    agents_active: int = 0
    last_sync_at: datetime | None = None
    read_only: bool = True
    error: str | None = None
    alerts_source: str = "wazuh-indexer-api"
