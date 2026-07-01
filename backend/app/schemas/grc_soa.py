"""Schémas API — Déclaration d'Applicabilité (SoA) ISO/IEC 27001:2022."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class SoaSeed(BaseModel):
    risk_register_ready: bool = True
    audit_ready: bool = True
    certification_ready: bool = True
    dashboard_ready: bool = True


class SoaControlRow(BaseModel):
    control_id: str
    iso_reference: str
    control_name: str
    applicable: str
    justification: str
    implemented: str
    ebios_source: str
    associated_measure: str
    decision: str
    responsible: str
    status: str
    comment: str = ""
    soa_seed: SoaSeed = Field(default_factory=SoaSeed)


class SoaSummary(BaseModel):
    soa_version: str
    project_name: str
    generated_at: datetime
    total_controls: int
    applicable_controls: int
    non_applicable_controls: int
    implemented_controls: int
    coverage_rate_percent: float


class SoaFilterOptions(BaseModel):
    iso_references: list[str] = Field(default_factory=list)
    responsibles: list[str] = Field(default_factory=list)
    statuses: list[str] = Field(default_factory=list)


class SoaMetadata(BaseModel):
    project_id: UUID
    assessment_id: UUID
    read_only: bool = True
    standard: str = "ISO/IEC 27001:2022"
    framework: str = "ISO/IEC 27002:2022"


class SoaResponse(BaseModel):
    summary: SoaSummary
    rows: list[SoaControlRow]
    total: int
    page: int
    page_size: int
    filter_options: SoaFilterOptions
    metadata: SoaMetadata
