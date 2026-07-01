"""Service connecteur Wazuh — configuration, cache et agrégation."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.connectors.wazuh.auth import invalidate_shared_authenticators
from app.connectors.wazuh.cache import get_wazuh_cache
from app.connectors.wazuh.client import WazuhClient
from app.connectors.wazuh.errors import WazuhClientError, classify_wazuh_exception
from app.connectors.wazuh.models import WazuhConnectionConfig, WazuhStatus
from app.models.entities import WazuhConnectorConfig

logger = logging.getLogger(__name__)


def _to_config(record: WazuhConnectorConfig | None) -> WazuhConnectionConfig:
    if not record:
        return WazuhConnectionConfig()
    verify_ssl = record.verify_ssl
    if verify_ssl is None:
        verify_ssl = True
    return WazuhConnectionConfig(
        base_url=record.base_url or "",
        username=record.username or "",
        password=record.password or "",
        verify_ssl=bool(verify_ssl),
        indexer_url=record.indexer_url,
        indexer_username=record.indexer_username,
        indexer_password=record.indexer_password,
        enabled=bool(record.enabled),
    )


async def get_or_create_config(db: AsyncSession) -> WazuhConnectorConfig:
    result = await db.execute(select(WazuhConnectorConfig).limit(1))
    record = result.scalar_one_or_none()
    if not record:
        record = WazuhConnectorConfig()
        db.add(record)
        await db.commit()
        await db.refresh(record)
    return record


def config_to_public_dict(record: WazuhConnectorConfig) -> dict[str, Any]:
    return {
        "base_url": record.base_url or "",
        "username": record.username or "",
        "password_configured": bool(record.password),
        "verify_ssl": bool(record.verify_ssl),
        "indexer_url": record.indexer_url or "",
        "indexer_username": record.indexer_username or "",
        "indexer_password_configured": bool(record.indexer_password),
        "enabled": bool(record.enabled),
        "last_sync_at": record.last_sync_at,
        "updated_at": record.updated_at,
    }


async def update_config(
    db: AsyncSession,
    *,
    base_url: str | None = None,
    username: str | None = None,
    password: str | None = None,
    verify_ssl: bool | None = None,
    indexer_url: str | None = None,
    indexer_username: str | None = None,
    indexer_password: str | None = None,
    enabled: bool | None = None,
) -> WazuhConnectorConfig:
    record = await get_or_create_config(db)
    if base_url is not None:
        record.base_url = base_url.strip()
    if username is not None:
        record.username = username.strip()
    if password is not None and password != "":
        record.password = password
    if verify_ssl is not None:
        record.verify_ssl = verify_ssl
    if indexer_url is not None:
        record.indexer_url = indexer_url.strip() or None
    if indexer_username is not None:
        record.indexer_username = indexer_username.strip() or None
    if indexer_password is not None and indexer_password != "":
        record.indexer_password = indexer_password
    if enabled is not None:
        record.enabled = enabled
    record.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(record)
    get_wazuh_cache().invalidate()
    invalidate_shared_authenticators()
    return record


def _client_from_record(record: WazuhConnectorConfig) -> WazuhClient:
    return WazuhClient(_to_config(record))


async def run_wazuh_connection_test(db: AsyncSession) -> dict[str, Any]:
    try:
        record = await get_or_create_config(db)
        config = _to_config(record)
        if not config.is_configured():
            return {
                "success": False,
                "error": "Connecteur non configuré (URL, utilisateur, mot de passe requis).",
            }
        result = await _client_from_record(record).test_connection()
        if result.get("success"):
            record.last_sync_at = datetime.now(timezone.utc)
            await db.commit()
            get_wazuh_cache().invalidate()
            invalidate_shared_authenticators()
        return result
    except Exception as exc:
        return {"success": False, "error": classify_wazuh_exception(exc)}


async def get_wazuh_status(db: AsyncSession) -> dict[str, Any]:
    record = await get_or_create_config(db)
    config = _to_config(record)
    cache = get_wazuh_cache()
    cached = cache.get("status")
    if cached:
        return cached

    if not config.is_configured() or not config.enabled:
        status = WazuhStatus(
            connected=False,
            configured=config.is_configured(),
            last_sync_at=record.last_sync_at,
            error=None if config.is_configured() else "Connecteur Wazuh non configuré",
        )
        payload = _status_to_dict(status)
        cache.set("status", payload, ttl_seconds=15)
        return payload

    try:
        client = _client_from_record(record)
        api_info = await client.get_api_info()
        manager = await client.get_manager_info()
        agents, total = await client.list_agents(limit=500)
        active = sum(1 for a in agents if a.status.lower() == "active")
        record.last_sync_at = datetime.now(timezone.utc)
        await db.commit()

        status = WazuhStatus(
            connected=True,
            configured=True,
            wazuh_version=str(manager.get("version", "")),
            api_version=str(api_info.get("api_version", "")),
            manager=str(manager.get("name", "")),
            agents_total=total,
            agents_active=active,
            last_sync_at=record.last_sync_at,
        )
        payload = _status_to_dict(status)
        cache.set("status", payload)
        return payload
    except (WazuhClientError, Exception) as exc:
        status = WazuhStatus(
            connected=False,
            configured=True,
            last_sync_at=record.last_sync_at,
            error=classify_wazuh_exception(exc),
        )
        payload = _status_to_dict(status)
        cache.set("status", payload, ttl_seconds=15)
        return payload


def _status_to_dict(status: WazuhStatus) -> dict[str, Any]:
    return {
        "connected": status.connected,
        "configured": status.configured,
        "wazuh_version": status.wazuh_version,
        "api_version": status.api_version,
        "manager": status.manager,
        "agents_total": status.agents_total,
        "agents_active": status.agents_active,
        "last_sync_at": status.last_sync_at,
        "read_only": status.read_only,
        "error": status.error,
        "alerts_source": status.alerts_source,
    }


async def get_wazuh_agents(
    db: AsyncSession, *, limit: int = 100, offset: int = 0
) -> dict[str, Any]:
    record = await get_or_create_config(db)
    config = _to_config(record)
    if not config.is_configured() or not config.enabled:
        raise ValueError("Connecteur Wazuh non configuré ou désactivé")

    cache_key = f"agents:{limit}:{offset}"
    cache = get_wazuh_cache()
    cached = cache.get(cache_key)
    if cached:
        return cached

    client = _client_from_record(record)
    agents, total = await client.list_agents(limit=limit, offset=offset)
    payload = {
        "agents": [_agent_to_dict(a) for a in agents],
        "total": total,
        "limit": limit,
        "offset": offset,
        "read_only": True,
    }
    cache.set(cache_key, payload)
    return payload


async def get_wazuh_alerts(
    db: AsyncSession, *, limit: int = 50, offset: int = 0
) -> dict[str, Any]:
    record = await get_or_create_config(db)
    config = _to_config(record)
    if not config.is_configured() or not config.enabled:
        raise ValueError("Connecteur Wazuh non configuré ou désactivé")

    cache_key = f"alerts:{limit}:{offset}"
    cache = get_wazuh_cache()
    cached = cache.get(cache_key)
    if cached:
        return cached

    client = _client_from_record(record)
    logger.info("get_wazuh_alerts — recherche indexer (limit=%s, offset=%s)", limit, offset)
    try:
        alerts, total = await client.search_alerts(limit=limit, offset=offset)
    except WazuhClientError:
        logger.exception("get_wazuh_alerts — échec après tentative indexer")
        raise
    logger.info("get_wazuh_alerts — %s alerte(s) récupérée(s)", total)
    payload = {
        "alerts": [_alert_to_dict(a) for a in alerts],
        "total": total,
        "limit": limit,
        "offset": offset,
        "read_only": True,
        "source": "wazuh-indexer-api",
    }
    cache.set(cache_key, payload, ttl_seconds=30)
    return payload


async def get_wazuh_alert(db: AsyncSession, alert_id: str) -> dict[str, Any]:
    record = await get_or_create_config(db)
    config = _to_config(record)
    if not config.is_configured() or not config.enabled:
        raise ValueError("Connecteur Wazuh non configuré ou désactivé")

    client = _client_from_record(record)
    alert = await client.get_alert(alert_id)
    if not alert:
        raise ValueError("Alerte introuvable")
    return {"alert": _alert_to_dict(alert), "read_only": True}


def _agent_to_dict(agent) -> dict[str, Any]:
    return {
        "id": agent.id,
        "name": agent.name,
        "ip": agent.ip,
        "status": agent.status,
        "os": agent.os,
        "version": agent.version,
        "last_keep_alive": agent.last_keep_alive,
    }


def _alert_to_dict(alert) -> dict[str, Any]:
    return {
        "id": alert.id,
        "timestamp": alert.timestamp,
        "rule_id": alert.rule_id,
        "rule_level": alert.rule_level,
        "rule_description": alert.rule_description,
        "agent_id": alert.agent_id,
        "agent_name": alert.agent_name,
        "full_log": alert.full_log,
        "groups": alert.groups,
    }
