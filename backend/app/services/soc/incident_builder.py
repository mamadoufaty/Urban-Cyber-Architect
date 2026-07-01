"""Construction d'incidents SOC enrichis — lecture seule."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.services.soc.alert_classifier import NormalizedAlert
from app.services.soc.asset_resolver import AssetResolution


def build_incident(
    alert: NormalizedAlert,
    asset: AssetResolution,
    *,
    ebios_context: dict[str, Any] | None = None,
    grc_risk: dict[str, Any] | None = None,
    mitre: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Assemble un incident corrélé prêt pour affichage et sprints futurs."""
    ebios = ebios_context or {}
    risk = grc_risk or {}
    mitre_data = mitre or {}

    correlation_seed = {
        "urbanism_ready": bool(asset.urbanism_entity_id),
        "ebios_ready": bool(ebios.get("operational_scenario")),
        "grc_ready": bool(risk.get("risk_id")),
        "mitre_ready": mitre_data.get("mitre_ready", False),
        "incident_response_ready": True,
        "notification_ready": True,
    }

    return {
        "incident_id": str(uuid4()),
        "alert": {
            "id": alert.alert_id,
            "timestamp": alert.timestamp,
            "rule_id": alert.rule_id,
            "rule_level": alert.rule_level,
            "rule_description": alert.rule_description,
            "severity": alert.severity_label,
            "category": alert.category,
            "full_log": alert.full_log,
        },
        "agent": {
            "id": asset.agent_id or alert.agent_id,
            "name": asset.agent_name or alert.agent_name,
            "ip": asset.agent_ip or alert.agent_ip,
        },
        "supporting_asset": asset.supporting_asset_label or ebios.get("supporting_asset", ""),
        "urbanism_entity_id": asset.urbanism_entity_id,
        "urbanism_entity_label": asset.urbanism_entity_label,
        "organization": asset.organization or ebios.get("organization", "") or risk.get("organization", ""),
        "processus": asset.processus or ebios.get("processus", ""),
        "operational_scenario": ebios.get("operational_scenario", "") or risk.get("operational_scenario", ""),
        "strategic_scenario": ebios.get("strategic_scenario", "") or risk.get("strategic_scenario", ""),
        "risk_source": ebios.get("risk_source", "") or risk.get("risk_source", ""),
        "grc_risk": {
            "risk_id": risk.get("risk_id", ""),
            "criticality": risk.get("criticality", ""),
            "treatment_decision": risk.get("treatment_decision", ""),
            "residual_risk": risk.get("residual_risk", ""),
            "status": risk.get("status", ""),
        },
        "business_owner": risk.get("owner_actor", "") or ebios.get("owner_actor", ""),
        "asset_match": {
            "method": asset.match_method,
            "confidence": asset.confidence,
        },
        "mitre": mitre_data,
        "correlation_seed": correlation_seed,
        "correlated_at": datetime.now(timezone.utc),
        "read_only": True,
    }
