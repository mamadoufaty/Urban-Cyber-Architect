"""Schémas API — Plan de Traitement des Risques (PTR)."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class PtrSeed(BaseModel):
    dashboard_ready: bool = True
    audit_ready: bool = True
    notification_ready: bool = True
    reporting_ready: bool = True
    governance_ready: bool = True


class PtrActionRow(BaseModel):
    ptr_id: str
    action_id: UUID
    associated_risk: str
    risk_source: str
    strategic_scenario: str
    operational_scenario: str
    security_measure: str
    iso27002_reference: str
    responsible: str
    organization: str
    priority: str
    budget: float | None = None
    budget_consumed: float = 0.0
    due_date: str = ""
    status: str
    progress_percent: int = 0
    treatment_decision: str
    residual_risk: str
    updated_at: datetime
    overdue: bool = False
    due_soon: bool = False
    ptr_seed: PtrSeed = Field(default_factory=PtrSeed)


class PtrSummary(BaseModel):
    project_name: str
    generated_at: datetime
    total_actions: int
    open_actions: int
    in_progress_actions: int
    completed_actions: int
    overdue_actions: int
    total_budget: float
    consumed_budget: float
    global_progress_percent: float


class PtrTimelineItem(BaseModel):
    ptr_id: str
    action_id: UUID
    label: str
    responsible: str
    due_date: str
    status: str
    priority: str
    progress_percent: int
    overdue: bool
    due_soon: bool


class PtrTimeline(BaseModel):
    reference_date: date
    overdue: list[PtrTimelineItem] = Field(default_factory=list)
    due_soon: list[PtrTimelineItem] = Field(default_factory=list)
    items: list[PtrTimelineItem] = Field(default_factory=list)


class PtrFilterOptions(BaseModel):
    responsibles: list[str] = Field(default_factory=list)
    organizations: list[str] = Field(default_factory=list)
    priorities: list[str] = Field(default_factory=list)
    statuses: list[str] = Field(default_factory=list)
    treatment_decisions: list[str] = Field(default_factory=list)


class PtrMetadata(BaseModel):
    project_id: UUID
    assessment_id: UUID
    read_only: bool = False
    limited_edit: bool = True
    editable_fields: list[str] = Field(
        default_factory=lambda: [
            "status",
            "progress_percent",
            "budget",
            "budget_consumed",
            "due_date",
            "priority",
        ]
    )


class PtrResponse(BaseModel):
    summary: PtrSummary
    rows: list[PtrActionRow]
    timeline: PtrTimeline
    total: int
    page: int
    page_size: int
    filter_options: PtrFilterOptions
    metadata: PtrMetadata


class PtrActionPatch(BaseModel):
    status: str | None = None
    progress_percent: int | None = Field(None, ge=0, le=100)
    budget: float | None = Field(None, ge=0)
    budget_consumed: float | None = Field(None, ge=0)
    due_date: str | None = None
    priority: str | None = None
