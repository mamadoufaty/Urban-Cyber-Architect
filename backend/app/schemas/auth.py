"""Schémas — authentification."""

from __future__ import annotations

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=1, max_length=128)


class AuthUserResponse(BaseModel):
    id: str
    username: str
    displayName: str
    role: str
    organizationId: str | None = None


class LoginResponse(BaseModel):
    user: AuthUserResponse


class BootstrapStatusResponse(BaseModel):
    needs_bootstrap: bool
    bootstrap_enabled: bool
    message: str | None = None


class BootstrapAdminRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=100)
    password: str = Field(..., min_length=6, max_length=128)
    first_name: str | None = Field(None, max_length=100)
    last_name: str | None = Field(None, max_length=100)
    email: str | None = Field(None, max_length=255)


class BootstrapAdminResponse(BaseModel):
    action: str
    username: str
    role: str
