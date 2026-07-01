"""Sérialisation récursive pour champs JSON (SQLite / PostgreSQL)."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any
from uuid import UUID


def serialize_json(value: Any) -> Any:
    """Convertit récursivement les valeurs non JSON-serialisables."""
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, dict):
        return {
            serialize_json(k) if isinstance(k, (UUID, datetime, date)) else k: serialize_json(v)
            for k, v in value.items()
        }
    if isinstance(value, tuple):
        return [serialize_json(item) for item in value]
    if isinstance(value, list):
        return [serialize_json(item) for item in value]
    return value
