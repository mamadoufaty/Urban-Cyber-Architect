"""Schémas API — connecteur Wazuh."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class WazuhConfigResponse(BaseModel):
    base_url: str = ""
    username: str = ""
    password_configured: bool = False
    verify_ssl: bool = True
    indexer_url: str = ""
    indexer_username: str = ""
    indexer_password_configured: bool = False
    enabled: bool = False
    last_sync_at: datetime | None = None
    updated_at: datetime | None = None


class WazuhConfigUpdate(BaseModel):
    base_url: str | None = None
    username: str | None = None
    password: str | None = None
    verify_ssl: bool | None = None
    indexer_url: str | None = None
    indexer_username: str | None = None
    indexer_password: str | None = None
    enabled: bool | None = None


class WazuhTestResponse(BaseModel):
    success: bool
    error: str | None = None
    api_version: str | None = None
    wazuh_version: str | None = None
    manager: str | None = None
    agents_total: int | None = None


class WazuhStatusResponse(BaseModel):
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


class WazuhAgentItem(BaseModel):
    id: str
    name: str
    ip: str
    status: str
    os: str = ""
    version: str = ""
    last_keep_alive: str = ""


class WazuhAgentsResponse(BaseModel):
    agents: list[WazuhAgentItem]
    total: int
    limit: int
    offset: int
    read_only: bool = True


class WazuhAlertItem(BaseModel):
    id: str
    timestamp: str
    rule_id: str
    rule_level: int
    rule_description: str
    agent_id: str
    agent_name: str
    full_log: str = ""
    groups: list[str] = Field(default_factory=list)


class WazuhAlertsResponse(BaseModel):
    alerts: list[WazuhAlertItem]
    total: int
    limit: int
    offset: int
    read_only: bool = True
    source: str = "wazuh-indexer-api"


class WazuhAlertDetailResponse(BaseModel):
    alert: WazuhAlertItem
    read_only: bool = True
    raw: dict[str, Any] | None = None
