"""Schémas API — module GRC (Registre des risques et extensions futures)."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class RiskRegisterRow(BaseModel):
    """Ligne consolidée du registre des risques (lecture seule)."""

    risk_id: str
    evaluation_id: UUID
    organization: str
    supporting_asset: str
    risk_source: str
    strategic_scenario: str
    operational_scenario: str
    owner_actor: str
    decision_maker: str
    severity: str
    likelihood: str
    criticality: str
    treatment_decision: str
    retained_measures: list[str]
    retained_measure_count: int
    residual_risk: str
    residual_risk_score: int
    initial_risk_score: int
    status: str
    updated_at: datetime
    grc_analytics: dict[str, Any] = Field(default_factory=dict)


class RiskRegisterFilterOptions(BaseModel):
    organizations: list[str] = Field(default_factory=list)
    severities: list[str] = Field(default_factory=list)
    criticalities: list[str] = Field(default_factory=list)
    treatment_decisions: list[str] = Field(default_factory=list)
    statuses: list[str] = Field(default_factory=list)


class RiskRegisterMetadata(BaseModel):
    project_id: UUID
    assessment_id: UUID
    total_risks: int
    generated_at: datetime
    read_only: bool = True
    extensions_ready: dict[str, bool] = Field(
        default_factory=lambda: {
            "rssi_dashboard": True,
            "heatmap": True,
            "kpi": True,
            "kri": True,
            "comex_board": True,
        }
    )


class RiskRegisterResponse(BaseModel):
    rows: list[RiskRegisterRow]
    total: int
    page: int
    page_size: int
    filter_options: RiskRegisterFilterOptions
    metadata: RiskRegisterMetadata
