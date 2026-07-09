"""Schémas API — module EBIOS RM."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class EbiosAssessmentCreate(BaseModel):
    title: str = "Analyse EBIOS RM"
    description: str | None = None
    cartography_id: UUID | None = None


class EbiosAssessmentUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: str | None = None
    current_workshop: int | None = Field(None, ge=1, le=5)
    metadata: dict[str, Any] | None = None
    extension_flags: dict[str, Any] | None = None


class EbiosAssessmentResponse(BaseModel):
    id: UUID
    project_id: UUID
    cartography_id: UUID | None
    title: str
    description: str | None
    status: str
    current_workshop: int
    version: str
    metadata: dict[str, Any] = Field(
        validation_alias="metadata_",
        serialization_alias="metadata",
        default_factory=dict,
    )
    extension_flags: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True, "populate_by_name": True}


class EbiosWorkshopResponse(BaseModel):
    id: UUID
    assessment_id: UUID
    workshop_number: int
    code: str
    status: str
    progress_percent: int
    summary: dict[str, Any]
    content: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EbiosWorkshopUpdate(BaseModel):
    status: str | None = None
    progress_percent: int | None = Field(None, ge=0, le=100)
    summary: dict[str, Any] | None = None
    content: dict[str, Any] | None = None


class EbiosRecordCreate(BaseModel):
    workshop_number: int = Field(..., ge=1, le=5)
    record_type: str
    label: str
    description: str | None = None
    properties: dict[str, Any] = Field(default_factory=dict)
    status: str = "draft"
    sort_order: int = 0


class EbiosRecordUpdate(BaseModel):
    label: str | None = None
    description: str | None = None
    properties: dict[str, Any] | None = None
    status: str | None = None
    sort_order: int | None = None


class EbiosRecordResponse(BaseModel):
    id: UUID
    assessment_id: UUID
    workshop_number: int
    record_type: str
    label: str
    description: str | None
    properties: dict[str, Any]
    status: str
    sort_order: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EbiosLinkCreate(BaseModel):
    source_record_id: UUID
    target_record_id: UUID
    link_type: str
    properties: dict[str, Any] = Field(default_factory=dict)


class EbiosLinkResponse(BaseModel):
    id: UUID
    assessment_id: UUID
    source_record_id: UUID
    target_record_id: UUID
    link_type: str
    properties: dict[str, Any]
    created_at: datetime

    model_config = {"from_attributes": True}


class EbiosOverviewResponse(BaseModel):
    assessment: EbiosAssessmentResponse
    workshops: list[EbiosWorkshopResponse]
    record_counts_by_workshop: dict[str, int]
    link_count: int
    overall_progress_percent: int


class EbiosUrbanismImportResponse(BaseModel):
    imported_count: int
    records: list[EbiosRecordResponse]


class EbiosGenerateScenariosResponse(BaseModel):
    generated_count: int
    records: list[EbiosRecordResponse]


class EbiosGenerateWorkshop1Response(BaseModel):
    generated_count: int
    records: list[EbiosRecordResponse]


class EbiosGenerateWorkshop2Response(BaseModel):
    generated_count: int
    records: list[EbiosRecordResponse]


class EbiosWorkshop4Response(BaseModel):
    scenarios: list[EbiosRecordResponse]
    validated_strategic_count: int
    operational_count: int


class EbiosGenerateOperationalResponse(BaseModel):
    generated_count: int
    records: list[EbiosRecordResponse]


class EbiosOperationalScenarioPatch(BaseModel):
    label: str | None = None
    properties: dict[str, Any] | None = None
    set_validated: bool = False


class EbiosUrbanismActorRef(BaseModel):
    id: str
    label: str
    entity_type: str
    description: str | None = None
    couche: str | None = None


class EbiosWorkshop5Bundle(BaseModel):
    evaluation: EbiosRecordResponse
    measures: list[EbiosRecordResponse]
    actions: list[EbiosRecordResponse]
    residual_risk: EbiosRecordResponse | None = None


class EbiosWorkshop5Response(BaseModel):
    evaluations: list[EbiosWorkshop5Bundle]
    validated_operational_count: int
    urbanism_acteurs: list[EbiosUrbanismActorRef]
    treatment_decisions: list[str]


class EbiosGenerateTreatmentResponse(BaseModel):
    generated_count: int
    records: list[EbiosRecordResponse]


class EbiosRiskEvaluationPatch(BaseModel):
    treatment_decision: str | None = None
    properties: dict[str, Any] | None = None
    set_validated: bool = False


class EbiosRecordPropertiesPatch(BaseModel):
    properties: dict[str, Any]


class EbiosDeliverableSection(BaseModel):
    id: str
    title: str
    content: str | None = None
    bullets: list[str] = Field(default_factory=list)


class EbiosDeliverableResponse(BaseModel):
    deliverable_type: str
    title: str
    project_id: UUID
    project_name: str
    assessment_id: UUID
    generated_at: datetime
    overall_progress_percent: int
    is_complete: bool
    completeness_warning: str | None = None
    sections: list[EbiosDeliverableSection] = Field(default_factory=list)
    data: dict[str, Any] = Field(default_factory=dict)
