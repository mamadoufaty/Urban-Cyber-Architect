"""Schémas API — livrables documentaires."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


DELIVERABLE_TYPES = [
    ("project_management_plan", "Plan de management de projet"),
    ("stakeholder_analysis", "Analyse des parties prenantes"),
    ("requirements_matrix", "Matrice des exigences"),
    ("constraints_matrix", "Matrice des contraintes"),
    ("technical_specs", "Spécifications techniques"),
    ("ebios_report", "Rapport EBIOS RM"),
    ("risk_register", "Registre des risques"),
    ("soa", "SoA"),
    ("ptr", "PTR"),
    ("rssi_report", "Rapport RSSI"),
    ("soc_report", "Rapport SOC"),
    ("other", "Autre"),
]

DATA_SOURCE_OPTIONS = ["urbanism", "ebios", "grc", "soc", "wazuh", "ai"]
EXPORT_FORMATS = ["pdf", "docx", "markdown"]


class DeliverableGenerateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=512)
    deliverable_type: str = Field(..., max_length=100)
    user_need: str = Field(default="", max_length=10000)
    data_sources: list[str] = Field(default_factory=list)
    export_format: str = Field(default="markdown", pattern="^(pdf|docx|markdown)$")
    preview: bool = False


class DeliverableSummary(BaseModel):
    id: UUID
    project_id: UUID
    title: str
    deliverable_type: str
    user_need: str
    data_sources: list[str]
    export_format: str
    status: str
    created_at: datetime
    updated_at: datetime


class DeliverableDetail(DeliverableSummary):
    generated_content: dict[str, Any] = Field(default_factory=dict)


class DeliverableListResponse(BaseModel):
    deliverables: list[DeliverableSummary]
    total: int
    types: list[dict[str, str]]
    data_sources: list[str]
    export_formats: list[str]


class DeliverableGenerateResponse(BaseModel):
    deliverable: DeliverableDetail | None = None
    preview: bool = False
    generated_content: dict[str, Any] = Field(default_factory=dict)
