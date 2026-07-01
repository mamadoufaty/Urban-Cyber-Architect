"""Tests — sérialisation project_activity.details."""

from __future__ import annotations

import asyncio
import json
import uuid
from datetime import date, datetime

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base
from app.models.entities import Project
from app.models.project_core import ProjectActivity
from app.services.projects.activity_service import log_project_activity, serialize_activity_details
import app.models.project_core  # noqa: F401


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def db_session() -> AsyncSession:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        yield session
    await engine.dispose()


def test_serialize_activity_details_converts_date_datetime_uuid():
    owner_id = uuid.uuid4()
    payload = {
        "start_date": date(2025, 6, 15),
        "updated_at": datetime(2025, 6, 15, 14, 30, 0),
        "owner_id": owner_id,
        "nested": {
            "ids": [owner_id],
            "dates": [date(2025, 1, 1)],
        },
    }

    result = serialize_activity_details(payload)

    assert result["start_date"] == "2025-06-15"
    assert result["updated_at"] == "2025-06-15T14:30:00"
    assert result["owner_id"] == str(owner_id)
    assert result["nested"]["ids"] == [str(owner_id)]
    assert result["nested"]["dates"] == ["2025-01-01"]
    json.dumps(result)


@pytest.mark.asyncio
async def test_log_project_activity_accepts_dates_and_uuids(db_session: AsyncSession):
    project = Project(name="Projet activité")
    db_session.add(project)
    await db_session.flush()

    owner_id = uuid.uuid4()
    details = {
        "fields": ["start_date", "owner_id"],
        "changes": {
            "start_date": date(2025, 3, 10),
            "owner_id": owner_id,
            "archived_at": datetime(2025, 3, 10, 9, 0, 0),
        },
    }

    entry = await log_project_activity(
        db_session,
        project_id=project.id,
        action="project.updated",
        user_id=owner_id,
        details=details,
    )
    await db_session.commit()

    stored = await db_session.scalar(
        select(ProjectActivity).where(ProjectActivity.id == entry.id)
    )
    assert stored is not None
    assert stored.details["changes"]["start_date"] == "2025-03-10"
    assert stored.details["changes"]["owner_id"] == str(owner_id)
    assert stored.details["changes"]["archived_at"] == "2025-03-10T09:00:00"
    json.dumps(stored.details)
