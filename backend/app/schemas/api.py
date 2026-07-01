from datetime import date, datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field


class OrganizationSchema(BaseModel):
    name: str
    sector: str = "generic"
    size: str = "PME"
    country: str = "France"


class ProjectCreate(BaseModel):
    name: str
    description: str | None = None
    template: str | None = None
    organization: OrganizationSchema | None = None
    referentials: list[str] = Field(default_factory=list)
    objectives: list[str] = Field(default_factory=list)
    urbanism: dict[str, Any] = Field(default_factory=dict)
    code: str | None = None
    client: str | None = None
    organization_id: UUID | None = None
    status: str | None = None
    priority: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    owner_id: UUID | None = None
    tags: list[str] = Field(default_factory=list)
    created_by: UUID | None = None


class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    organization: OrganizationSchema | None = None
    referentials: list[str] | None = None
    objectives: list[str] | None = None
    urbanism: dict[str, Any] | None = None
    status: str | None = None
    code: str | None = None
    client: str | None = None
    organization_id: UUID | None = None
    priority: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    owner_id: UUID | None = None
    tags: list[str] | None = None


class ProjectResponse(BaseModel):
    id: UUID
    name: str
    code: str | None = None
    description: str | None
    client: str | None = None
    organization: dict[str, Any]
    organization_id: UUID | None = None
    referentials: list[str]
    urbanism: dict[str, Any]
    objectives: list[str]
    status: str
    priority: str = "medium"
    start_date: date | None = None
    end_date: date | None = None
    owner_id: UUID | None = None
    tags: list[str] = Field(default_factory=list)
    created_by: UUID | None = None
    created_at: datetime
    updated_at: datetime
    archived_at: datetime | None = None

    model_config = {"from_attributes": True}


class ProjectMemberCreate(BaseModel):
    user_id: UUID
    project_role: str


class ProjectMemberResponse(BaseModel):
    id: UUID
    project_id: UUID
    user_id: UUID
    project_role: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ProjectActivityResponse(BaseModel):
    id: UUID
    project_id: UUID
    user_id: UUID | None
    action: str
    details: dict[str, Any]
    created_at: datetime

    model_config = {"from_attributes": True}


class OrchestrateRequest(BaseModel):
    template_name: str = "architecture_analysis"
    models: list[str] | None = None


class HumanDecisionCreate(BaseModel):
    orchestration_id: UUID | None = None
    action: Literal["accept", "modify", "merge", "reject"]
    selected_model: str | None = None
    merged_content: str | None = None
    modified_content: str | None = None
    comment: str | None = None


class HumanDecisionResponse(BaseModel):
    id: UUID
    project_id: UUID
    orchestration_id: UUID | None
    action: str
    selected_model: str | None
    comment: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class AIGovernanceUpdate(BaseModel):
    models: list[str] | None = None
    judge_id: str | None = None
    urbanisme_weight: float | None = Field(None, ge=0, le=1)
    conformite_weight: float | None = Field(None, ge=0, le=1)
    ebios_weight: float | None = Field(None, ge=0, le=1)
    architecture_weight: float | None = Field(None, ge=0, le=1)


class AIGovernanceResponse(BaseModel):
    models: list[str]
    judge_id: str
    urbanisme_weight: float
    conformite_weight: float
    ebios_weight: float
    architecture_weight: float

    model_config = {"from_attributes": True}


class PromptUpdate(BaseModel):
    template: str
    version: str
    description: str = ""


class PromptResponse(BaseModel):
    name: str
    version: str
    description: str
    template: str | None = None
    created_at: str | None = None
