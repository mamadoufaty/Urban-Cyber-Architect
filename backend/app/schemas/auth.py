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


class LoginResponse(BaseModel):
    user: AuthUserResponse
