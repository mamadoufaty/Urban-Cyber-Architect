"""Schémas Pydantic — cartographies, versions et historique."""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

CartographyType = Literal[
    "urbanisme_si",
    "urbanisme_metier",
    "urbanisme_fonctionnel",
    "urbanisme_applicatif",
    "urbanisme_technique",
    "cybersecurite",
    "architecture_actuelle",
    "architecture_cible",
    "reseau",
    "cloud",
    "libre",
]

CartographyStatus = Literal["draft", "in_validation", "validated", "archived"]


class CartographyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    type: CartographyType = "libre"
    description: str | None = None
    author: str | None = None


class CartographyUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    type: CartographyType | None = None


class CartographyRead(BaseModel):
    id: UUID
    project_id: UUID
    name: str
    description: str | None
    type: str
    status: str
    version: str
    author: str | None
    is_active: bool
    is_archived: bool
    created_at: datetime
    updated_at: datetime
    validated_at: datetime | None
    validated_by: str | None

    model_config = {"from_attributes": True}


class CartographyListResponse(BaseModel):
    total: int
    items: list[CartographyRead]


class CartographyDuplicateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    author: str | None = None


class CartographyValidateRequest(BaseModel):
    validated_by: str | None = None
    comment: str | None = None


class CartographyVersionRead(BaseModel):
    id: UUID
    cartography_id: UUID
    version: str
    status: str
    is_current: bool
    author: str | None
    comment: str | None
    created_at: datetime
    validated_at: datetime | None
    validated_by: str | None

    model_config = {"from_attributes": True}


class CartographyVersionListResponse(BaseModel):
    items: list[CartographyVersionRead]


class CartographyRestoreRequest(BaseModel):
    version_id: UUID
    author: str | None = None


class CartographyHistoryRead(BaseModel):
    id: UUID
    cartography_id: UUID
    version_id: UUID | None
    version: str
    author: str | None
    action: str
    comment: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class CartographyHistoryListResponse(BaseModel):
    items: list[CartographyHistoryRead]
