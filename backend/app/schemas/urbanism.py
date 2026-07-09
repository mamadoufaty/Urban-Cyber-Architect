from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class UrbanismEntityCreate(BaseModel):
    entity_type: str
    label: str
    description: str | None = None
    properties: dict[str, Any] = Field(default_factory=dict)
    relations: list["UrbanismRelationInline"] = Field(default_factory=list)


class UrbanismRelationInline(BaseModel):
    relation_type: str
    target_id: UUID | None = None
    source_id: UUID | None = None
    commentaire: str | None = None
    criticite: Literal["faible", "moyenne", "élevée", "critique"] | None = None


class UrbanismEntityUpdate(BaseModel):
    label: str | None = None
    description: str | None = None
    properties: dict[str, Any] | None = None


class UrbanismRelationCreate(BaseModel):
    source_id: UUID
    target_id: UUID
    relation_type: str
    commentaire: str | None = None
    criticite: Literal["faible", "moyenne", "élevée", "critique"] | None = None
    properties: dict[str, Any] = Field(default_factory=dict)


class EdgeLayoutPoint(BaseModel):
    x: float
    y: float


class EdgeLayoutOverride(BaseModel):
    mode: Literal["manual"] = "manual"
    locked: bool = True
    pathType: Literal["custom"] = "custom"
    waypoints: list[EdgeLayoutPoint] = Field(default_factory=list)
    sourceHandle: str
    targetHandle: str
    labelPosition: float = 0.5
    labelOffsetX: float = 0
    labelOffsetY: float = -12


class UrbanismRelationLayoutUpdate(BaseModel):
    layout: EdgeLayoutOverride


class EntityLayoutPosition(BaseModel):
    x: float
    y: float


class UrbanismEntityLayoutUpdate(BaseModel):
    layout: EntityLayoutPosition


class EntityLayoutBulkItem(BaseModel):
    entity_id: UUID
    layout: EntityLayoutPosition


class UrbanismEntityLayoutBulkUpdate(BaseModel):
    layouts: list[EntityLayoutBulkItem]


class UrbanismRelationResponse(BaseModel):
    id: UUID
    project_id: UUID
    source_id: UUID
    target_id: UUID
    relation_type: str
    category: str
    commentaire: str | None
    criticite: str | None
    properties: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    model_config = {"from_attributes": True}

    @field_validator("properties", mode="before")
    @classmethod
    def normalize_properties(cls, value: Any) -> dict[str, Any]:
        return value if isinstance(value, dict) else {}


class UrbanismEntityResponse(BaseModel):
    id: UUID
    project_id: UUID
    entity_type: str
    couche: str
    label: str
    description: str | None
    properties: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


UrbanismEntityCreate.model_rebuild()


class AssistedFieldOption(BaseModel):
    entity_id: str
    label: str
    entity_type: str


class AssistedFormField(BaseModel):
    field_id: str
    rule_id: str
    label: str
    relation_type: str
    peer_type: str
    direction: Literal["incoming", "outgoing"]
    required: bool
    cardinality: dict[str, int | None]
    widget: Literal["select", "multi-select"]
    options: list[AssistedFieldOption]
    selected: list[str] = Field(default_factory=list)
    visible: bool = True


class AssistedFormSchema(BaseModel):
    entity_type: str
    entity_label: str
    label_field: dict[str, Any]
    fields: list[AssistedFormField]
    required_field_ids: list[str] = Field(default_factory=list)
    hints: list[str] = Field(default_factory=list)
    creation_order: int = 99


class AssistedCreateRequest(BaseModel):
    entity_type: str
    label: str
    bindings: dict[str, list[str]] = Field(default_factory=dict)


class AssistedCreateResponse(BaseModel):
    entity: UrbanismEntityResponse
    relations_created: list[UrbanismRelationResponse]
    analysis: dict[str, Any]
    bindings_applied: int
    reused: bool = False


class DeduplicateResponse(BaseModel):
    merged_groups: int
    entities_removed: int
    relations_relocated: int
    analysis: dict[str, Any]


class AssistedLinkRequest(BaseModel):
    action: Literal["add", "remove", "replace"]
    rule_id: str
    source_id: UUID
    target_id: UUID


class AssistedLinkResponse(BaseModel):
    action: str
    relation: UrbanismRelationResponse | None = None
    analysis: dict[str, Any]


class UrbanismImportPreviewResponse(BaseModel):
    counts: dict[str, int]
    issues: list[dict[str, Any]]
    sample_rows: list[dict[str, Any]]
    mode: Literal["replace", "merge"]
    can_import: bool


class UrbanismImportReportResponse(BaseModel):
    created: dict[str, int]
    updated: dict[str, int]
    relations_created: int
    orphans: int
    inconsistencies: int
    completeness_rate: float
    urbanism_progress: dict[str, Any]
    flux_stored: int
    issues: list[dict[str, Any]]

