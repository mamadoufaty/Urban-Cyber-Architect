"""Routes API — connecteur Wazuh (lecture seule)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.wazuh import (
    WazuhAgentsResponse,
    WazuhAlertDetailResponse,
    WazuhAlertsResponse,
    WazuhConfigResponse,
    WazuhConfigUpdate,
    WazuhStatusResponse,
    WazuhTestResponse,
)
from app.connectors.wazuh.service import (
    config_to_public_dict,
    get_or_create_config,
    get_wazuh_agents,
    get_wazuh_alert,
    get_wazuh_alerts,
    get_wazuh_status,
    run_wazuh_connection_test,
    update_config,
)

router = APIRouter(tags=["connectors-wazuh"])


@router.get("/connectors/wazuh/config", response_model=WazuhConfigResponse)
async def read_wazuh_config(db: AsyncSession = Depends(get_db)):
    record = await get_or_create_config(db)
    return config_to_public_dict(record)


@router.put("/connectors/wazuh/config", response_model=WazuhConfigResponse)
async def save_wazuh_config(data: WazuhConfigUpdate, db: AsyncSession = Depends(get_db)):
    record = await update_config(db, **data.model_dump(exclude_unset=True))
    return config_to_public_dict(record)


@router.post("/connectors/wazuh/test", response_model=WazuhTestResponse)
async def test_wazuh_connector(db: AsyncSession = Depends(get_db)):
    return await run_wazuh_connection_test(db)


@router.get("/connectors/wazuh/status", response_model=WazuhStatusResponse)
async def wazuh_status(db: AsyncSession = Depends(get_db)):
    return await get_wazuh_status(db)


@router.get("/connectors/wazuh/agents", response_model=WazuhAgentsResponse)
async def wazuh_agents(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await get_wazuh_agents(db, limit=limit, offset=offset)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e


@router.get("/connectors/wazuh/alerts", response_model=WazuhAlertsResponse)
async def wazuh_alerts(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await get_wazuh_alerts(db, limit=limit, offset=offset)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e


@router.get("/connectors/wazuh/alert/{alert_id}", response_model=WazuhAlertDetailResponse)
async def wazuh_alert_detail(alert_id: str, db: AsyncSession = Depends(get_db)):
    try:
        data = await get_wazuh_alert(db, alert_id)
        alert = data["alert"]
        return {"alert": alert, "read_only": True}
    except ValueError as e:
        raise HTTPException(404, str(e)) from e
