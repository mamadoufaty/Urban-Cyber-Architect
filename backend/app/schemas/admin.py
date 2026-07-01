"""Schémas Pydantic — module Administration."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class OrganizationCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    code: str = Field(..., min_length=1, max_length=100)
    description: str | None = None
    status: str = "active"


class OrganizationUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    status: str | None = None


class OrganizationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    code: str
    description: str | None
    status: str
    created_at: datetime
    updated_at: datetime


class UserCreate(BaseModel):
    username: str = Field(..., min_length=2, max_length=100)
    password: str = Field(..., min_length=6, max_length=128)
    first_name: str | None = None
    last_name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    organization_id: UUID | None = None
    function: str | None = None
    role_id: UUID | None = None
    status: str = "active"
    avatar: str | None = None


class UserUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    organization_id: UUID | None = None
    function: str | None = None
    role_id: UUID | None = None
    status: str | None = None
    avatar: str | None = None


class UserResetPassword(BaseModel):
    password: str = Field(..., min_length=6, max_length=128)


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    username: str
    first_name: str | None
    last_name: str | None
    email: str | None
    phone: str | None
    organization_id: UUID | None
    function: str | None
    role_id: UUID | None
    status: str
    avatar: str | None
    last_login_at: datetime | None
    failed_login_count: int
    locked_until: datetime | None
    created_at: datetime
    updated_at: datetime
    role_code: str | None = None
    organization_name: str | None = None


class RoleCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    code: str = Field(..., min_length=1, max_length=50)
    description: str | None = None


class RoleUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = None


class PermissionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    module: str
    action: str
    code: str
    description: str | None
    created_at: datetime
    updated_at: datetime


class RoleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    code: str
    description: str | None
    is_system: bool
    created_at: datetime
    updated_at: datetime
    permissions: list[PermissionRead] = []


class RolePermissionsUpdate(BaseModel):
    permission_ids: list[UUID]


class AuditLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID | None
    action: str
    object_type: str | None
    object_id: str | None
    result: str
    ip_address: str | None
    user_agent: str | None
    details: dict
    created_at: datetime
    username: str | None = None


class UserListResponse(BaseModel):
    total: int
    items: list[UserRead]


class OrganizationListResponse(BaseModel):
    total: int
    items: list[OrganizationRead]


class RoleListResponse(BaseModel):
    total: int
    items: list[RoleRead]


class PermissionListResponse(BaseModel):
    total: int
    items: list[PermissionRead]


class AuditLogListResponse(BaseModel):
    total: int
    items: list[AuditLogRead]
