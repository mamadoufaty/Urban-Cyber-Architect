"""Moteur de corrélation SOC — Wazuh ↔ Urbanisme ↔ EBIOS ↔ GRC."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.connectors.wazuh.errors import WazuhClientError
from app.connectors.wazuh.service import get_wazuh_agents, get_wazuh_alerts, get_wazuh_status
from app.services.ebios.assessment_service import get_or_create_assessment, list_records
from app.services.ebios.urbanism_actor_resolver import load_urbanism_graph
from app.services.grc.risk_register_service import build_risk_register_rows
from app.services.soc.alert_classifier import classify_alert
from app.services.soc.asset_resolver import resolve_agent_to_asset
from app.services.soc.incident_builder import build_incident
from app.services.soc.mitre_mapper import map_mitre_from_alert

logger = logging.getLogger(__name__)


def _norm(value: str) -> str:
    return str(value or "").strip().lower()


def _index_risk_rows(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    index: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        key = _norm(row.get("supporting_asset", ""))
        if key:
            index.setdefault(key, []).append(row)
    return index


def _pick_best_risk(
    asset_label: str,
    risk_index: dict[str, list[dict[str, Any]]],
    *,
    agent_name: str = "",
) -> dict[str, Any]:
    if not asset_label and not agent_name:
        return {}
    for key, rows in risk_index.items():
        if asset_label and (_norm(asset_label) == key or _norm(asset_label) in key or key in _norm(asset_label)):
            return rows[0]
        if agent_name and (_norm(agent_name) in key or key in _norm(agent_name)):
            return rows[0]
    return {}


def _ebios_labels_from_workshop2(records) -> list[str]:
    return [r.label for r in records if r.record_type == "supporting_asset"]


def _ebios_context_from_risk(risk: dict[str, Any]) -> dict[str, Any]:
    if not risk:
        return {}
    return {
        "supporting_asset": risk.get("supporting_asset", ""),
        "organization": risk.get("organization", ""),
        "operational_scenario": risk.get("operational_scenario", ""),
        "strategic_scenario": risk.get("strategic_scenario", ""),
        "risk_source": risk.get("risk_source", ""),
        "owner_actor": risk.get("owner_actor", ""),
        "processus": "",
    }


async def get_soc_correlations(
    db: AsyncSession,
    project_id: UUID,
    *,
    limit: int = 50,
    offset: int = 0,
    project_name: str = "",
) -> dict[str, Any]:
    """Corrèle les alertes Wazuh aux référentiels Urbanisme, EBIOS et GRC."""
    assessment = await get_or_create_assessment(db, project_id)
    entities, relations = await load_urbanism_graph(db, project_id)

    w2_records = await list_records(db, assessment.id, workshop_number=2)
    ebios_asset_labels = _ebios_labels_from_workshop2(w2_records)

    risk_rows = await build_risk_register_rows(db, assessment.id, project_id)
    risk_index = _index_risk_rows(risk_rows)

    alerts_payload: dict[str, Any] = {"alerts": [], "total": 0}
    wazuh_error: str | None = None
    wazuh_status: dict[str, Any] | None = None
    wazuh_agents_total: int | None = None

    try:
        wazuh_status = await get_wazuh_status(db)
        logger.info(
            "SOC corrélations — get_wazuh_status : connected=%s agents_total=%s",
            wazuh_status.get("connected"),
            wazuh_status.get("agents_total"),
        )
        if not wazuh_status.get("connected"):
            wazuh_error = wazuh_status.get("error") or "Connecteur Wazuh déconnecté"
    except Exception as exc:
        logger.exception("SOC corrélations — get_wazuh_status échoué")
        wazuh_error = f"Statut Wazuh indisponible : {exc}"

    if not wazuh_error:
        try:
            agents_payload = await get_wazuh_agents(db, limit=1, offset=0)
            wazuh_agents_total = int(agents_payload.get("total") or 0)
            logger.info("SOC corrélations — get_wazuh_agents : total=%s", wazuh_agents_total)
        except Exception as exc:
            logger.exception("SOC corrélations — get_wazuh_agents échoué")
            wazuh_error = f"Agents Wazuh indisponibles : {exc}"

    if not wazuh_error:
        try:
            alerts_payload = await get_wazuh_alerts(db, limit=limit, offset=offset)
            logger.info(
                "SOC corrélations — get_wazuh_alerts : total=%s",
                alerts_payload.get("total"),
            )
        except ValueError as exc:
            logger.warning("SOC corrélations — get_wazuh_alerts : %s", exc)
            wazuh_error = str(exc)
        except WazuhClientError as exc:
            logger.error("SOC corrélations — get_wazuh_alerts (401/403 indexer) : %s", exc)
            wazuh_error = f"Alertes Wazuh indisponibles : {exc}"
        except Exception as exc:
            logger.exception("SOC corrélations — get_wazuh_alerts échoué")
            wazuh_error = f"Alertes Wazuh indisponibles : {exc}"

    incidents: list[dict[str, Any]] = []
    for raw_alert in alerts_payload.get("alerts") or []:
        normalized = classify_alert(raw_alert)
        asset = resolve_agent_to_asset(
            agent_id=normalized.agent_id,
            agent_name=normalized.agent_name,
            agent_ip=normalized.agent_ip,
            entities=entities,
            relations=relations,
            ebios_asset_labels=ebios_asset_labels,
        )
        risk = _pick_best_risk(
            asset.supporting_asset_label or asset.urbanism_entity_label,
            risk_index,
            agent_name=normalized.agent_name,
        )
        ebios_ctx = _ebios_context_from_risk(risk)
        if asset.processus:
            ebios_ctx["processus"] = asset.processus
        mitre = map_mitre_from_alert(normalized)
        incidents.append(
            build_incident(normalized, asset, ebios_context=ebios_ctx, grc_risk=risk, mitre=mitre)
        )

    correlated_count = sum(1 for i in incidents if i["correlation_seed"].get("grc_ready"))
    asset_matched = sum(1 for i in incidents if i["correlation_seed"].get("urbanism_ready"))

    return {
        "summary": {
            "project_name": project_name or "Projet",
            "generated_at": datetime.now(timezone.utc),
            "alerts_total": int(alerts_payload.get("total") or len(incidents)),
            "incidents_count": len(incidents),
            "correlated_risks": correlated_count,
            "assets_matched": asset_matched,
            "read_only": True,
        },
        "incidents": incidents,
        "total": int(alerts_payload.get("total") or len(incidents)),
        "limit": limit,
        "offset": offset,
        "metadata": {
            "project_id": project_id,
            "assessment_id": assessment.id,
            "wazuh_error": wazuh_error,
            "wazuh_connected": bool(wazuh_status and wazuh_status.get("connected")),
            "wazuh_agents_total": wazuh_agents_total,
            "risk_register_rows": len(risk_rows),
            "urbanism_entities": len(entities),
            "read_only": True,
        },
    }
