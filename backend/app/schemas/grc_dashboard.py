"""Schémas API — Dashboard RSSI / COMEX."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class DashboardKpi(BaseModel):
    total_risks: int = 0
    critical_risks: int = 0
    high_risks: int = 0
    moderate_risks: int = 0
    low_risks: int = 0
    critical_residual_risks: int = 0
    ptr_open_actions: int = 0
    ptr_completed_actions: int = 0
    treatment_rate_percent: float = 0.0
    iso27002_coverage_percent: float = 0.0


class HeatmapCell(BaseModel):
    severity_score: int
    likelihood_score: int
    severity_label: str
    likelihood_label: str
    count: int
    risk_ids: list[str] = Field(default_factory=list)
    dominant_criticality: str = ""


class RiskHeatmap(BaseModel):
    severity_labels: list[str]
    likelihood_labels: list[str]
    cells: list[HeatmapCell]
    max_count: int = 0


class TopRiskItem(BaseModel):
    risk_id: str
    supporting_asset: str
    organization: str
    risk_source: str
    criticality: str
    residual_risk: str
    treatment_decision: str
    initial_risk_score: int = 0


class ExposureItem(BaseModel):
    label: str
    count: int
    critical_count: int = 0


class PtrActionItem(BaseModel):
    action_id: str
    label: str
    status: str
    due_date: str = ""
    priority: str = ""
    budget: float | None = None
    evaluation_uid: str = ""
    overdue: bool = False


class PtrTracking(BaseModel):
    open_count: int = 0
    planned_count: int = 0
    in_progress_count: int = 0
    completed_count: int = 0
    overdue_count: int = 0
    actions: list[PtrActionItem] = Field(default_factory=list)


class ComexSummary(BaseModel):
    global_risk_level: str
    residual_risk_level: str
    decisions_to_arbitrate: int
    estimated_budget_total: float
    executive_message: str


class DashboardExportEndpoints(BaseModel):
    dashboard_pdf: str
    comex_summary: str
    rssi_report: str
    implemented: bool = False


class RssiDashboardMetadata(BaseModel):
    project_id: UUID
    project_name: str
    assessment_id: UUID
    generated_at: datetime
    read_only: bool = True
    export_endpoints: DashboardExportEndpoints


class RssiDashboardResponse(BaseModel):
    kpis: DashboardKpi
    heatmap: RiskHeatmap
    top_risks: list[TopRiskItem]
    exposure_by_organization: list[ExposureItem]
    exposure_by_supporting_asset: list[ExposureItem]
    ptr_tracking: PtrTracking
    comex: ComexSummary
    metadata: RssiDashboardMetadata
