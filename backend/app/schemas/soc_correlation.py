"""Schémas API — corrélation SOC."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class SocCorrelationSummary(BaseModel):
    project_name: str
    generated_at: datetime
    alerts_total: int
    incidents_count: int
    correlated_risks: int
    assets_matched: int
    read_only: bool = True


class SocCorrelationMetadata(BaseModel):
    project_id: UUID
    assessment_id: UUID
    wazuh_error: str | None = None
    risk_register_rows: int = 0
    urbanism_entities: int = 0
    read_only: bool = True


class SocIncidentResponse(BaseModel):
    incident_id: str
    alert: dict[str, Any]
    agent: dict[str, Any]
    supporting_asset: str = ""
    urbanism_entity_id: str | None = None
    urbanism_entity_label: str = ""
    organization: str = ""
    processus: str = ""
    operational_scenario: str = ""
    strategic_scenario: str = ""
    risk_source: str = ""
    grc_risk: dict[str, Any] = Field(default_factory=dict)
    business_owner: str = ""
    asset_match: dict[str, Any] = Field(default_factory=dict)
    mitre: dict[str, Any] = Field(default_factory=dict)
    correlation_seed: dict[str, Any] = Field(default_factory=dict)
    correlated_at: datetime
    read_only: bool = True


class SocCorrelationsResponse(BaseModel):
    summary: SocCorrelationSummary
    incidents: list[SocIncidentResponse]
    total: int
    limit: int
    offset: int
    metadata: SocCorrelationMetadata
