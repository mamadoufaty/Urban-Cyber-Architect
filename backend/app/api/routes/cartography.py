"""Routes API — cartographies multiples par projet + versionning."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.cartography import (
    CartographyCreate,
    CartographyDuplicateRequest,
    CartographyHistoryListResponse,
    CartographyHistoryRead,
    CartographyListResponse,
    CartographyRead,
    CartographyRestoreRequest,
    CartographyUpdate,
    CartographyValidateRequest,
    CartographyVersionListResponse,
    CartographyVersionRead,
)
from app.services import cartography_service
from app.services.cartography_service import CartographyError

router = APIRouter(tags=["cartography"])


def _http_error(e: CartographyError) -> HTTPException:
    message = str(e)
    status_code = 404 if "introuvable" in message.lower() else 400
    return HTTPException(status_code, message)


@router.get("/projects/{project_id}/cartographies", response_model=CartographyListResponse)
async def list_cartographies(project_id: UUID, db: AsyncSession = Depends(get_db)):
    try:
        items = await cartography_service.list_cartographies(db, project_id)
    except CartographyError as e:
        raise _http_error(e) from e
    return CartographyListResponse(
        total=len(items), items=[CartographyRead.model_validate(c) for c in items]
    )


@router.post(
    "/projects/{project_id}/cartographies", response_model=CartographyRead, status_code=201
)
async def create_cartography(
    project_id: UUID, data: CartographyCreate, db: AsyncSession = Depends(get_db)
):
    try:
        cartography = await cartography_service.create_cartography(
            db,
            project_id,
            name=data.name,
            type_=data.type,
            description=data.description,
            author=data.author,
        )
    except CartographyError as e:
        raise _http_error(e) from e
    return CartographyRead.model_validate(cartography)


@router.get("/cartographies/{cartography_id}", response_model=CartographyRead)
async def get_cartography(cartography_id: UUID, db: AsyncSession = Depends(get_db)):
    try:
        cartography = await cartography_service.get_cartography_or_404(db, cartography_id)
    except CartographyError as e:
        raise _http_error(e) from e
    return CartographyRead.model_validate(cartography)


@router.put("/cartographies/{cartography_id}", response_model=CartographyRead)
async def update_cartography(
    cartography_id: UUID, data: CartographyUpdate, db: AsyncSession = Depends(get_db)
):
    try:
        cartography = await cartography_service.update_cartography(
            db,
            cartography_id,
            name=data.name,
            description=data.description,
            type_=data.type,
        )
    except CartographyError as e:
        raise _http_error(e) from e
    return CartographyRead.model_validate(cartography)


@router.delete("/cartographies/{cartography_id}", status_code=204)
async def delete_cartography(cartography_id: UUID, db: AsyncSession = Depends(get_db)):
    try:
        await cartography_service.delete_cartography(db, cartography_id)
    except CartographyError as e:
        raise _http_error(e) from e


@router.post("/cartographies/{cartography_id}/activate", response_model=CartographyRead)
async def activate_cartography(cartography_id: UUID, db: AsyncSession = Depends(get_db)):
    try:
        cartography = await cartography_service.activate_cartography(db, cartography_id)
    except CartographyError as e:
        raise _http_error(e) from e
    return CartographyRead.model_validate(cartography)


@router.post("/cartographies/{cartography_id}/duplicate", response_model=CartographyRead)
async def duplicate_cartography(
    cartography_id: UUID, data: CartographyDuplicateRequest, db: AsyncSession = Depends(get_db)
):
    try:
        clone = await cartography_service.duplicate_cartography(
            db, cartography_id, name=data.name, author=data.author
        )
    except CartographyError as e:
        raise _http_error(e) from e
    return CartographyRead.model_validate(clone)


@router.post("/cartographies/{cartography_id}/new-version", response_model=CartographyRead)
async def new_version(
    cartography_id: UUID,
    author: str | None = Query(None),
    comment: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    try:
        cartography = await cartography_service.create_new_version(
            db, cartography_id, author=author, comment=comment
        )
    except CartographyError as e:
        raise _http_error(e) from e
    return CartographyRead.model_validate(cartography)


@router.post("/cartographies/{cartography_id}/submit-for-validation", response_model=CartographyRead)
async def submit_for_validation(
    cartography_id: UUID, author: str | None = Query(None), db: AsyncSession = Depends(get_db)
):
    try:
        cartography = await cartography_service.submit_for_validation(
            db, cartography_id, author=author
        )
    except CartographyError as e:
        raise _http_error(e) from e
    return CartographyRead.model_validate(cartography)


@router.post("/cartographies/{cartography_id}/validate", response_model=CartographyRead)
async def validate_cartography(
    cartography_id: UUID, data: CartographyValidateRequest, db: AsyncSession = Depends(get_db)
):
    try:
        cartography = await cartography_service.validate_cartography(
            db, cartography_id, validated_by=data.validated_by, comment=data.comment
        )
    except CartographyError as e:
        raise _http_error(e) from e
    return CartographyRead.model_validate(cartography)


@router.post("/cartographies/{cartography_id}/archive", response_model=CartographyRead)
async def archive_cartography(
    cartography_id: UUID, author: str | None = Query(None), db: AsyncSession = Depends(get_db)
):
    try:
        cartography = await cartography_service.archive_cartography(
            db, cartography_id, author=author
        )
    except CartographyError as e:
        raise _http_error(e) from e
    return CartographyRead.model_validate(cartography)


@router.post("/cartographies/{cartography_id}/unarchive", response_model=CartographyRead)
async def unarchive_cartography(
    cartography_id: UUID, author: str | None = Query(None), db: AsyncSession = Depends(get_db)
):
    try:
        cartography = await cartography_service.unarchive_cartography(
            db, cartography_id, author=author
        )
    except CartographyError as e:
        raise _http_error(e) from e
    return CartographyRead.model_validate(cartography)


@router.get(
    "/cartographies/{cartography_id}/versions", response_model=CartographyVersionListResponse
)
async def list_versions(cartography_id: UUID, db: AsyncSession = Depends(get_db)):
    await cartography_service.get_cartography_or_404(db, cartography_id)
    versions = await cartography_service.list_versions(db, cartography_id)
    return CartographyVersionListResponse(
        items=[CartographyVersionRead.model_validate(v) for v in versions]
    )


@router.post("/cartographies/{cartography_id}/restore", response_model=CartographyRead)
async def restore_version(
    cartography_id: UUID, data: CartographyRestoreRequest, db: AsyncSession = Depends(get_db)
):
    try:
        cartography = await cartography_service.restore_version(
            db, cartography_id, data.version_id, author=data.author
        )
    except CartographyError as e:
        raise _http_error(e) from e
    return CartographyRead.model_validate(cartography)


@router.get(
    "/cartographies/{cartography_id}/history", response_model=CartographyHistoryListResponse
)
async def get_history(cartography_id: UUID, db: AsyncSession = Depends(get_db)):
    await cartography_service.get_cartography_or_404(db, cartography_id)
    entries = await cartography_service.get_cartography_history(db, cartography_id)
    return CartographyHistoryListResponse(
        items=[CartographyHistoryRead.model_validate(h) for h in entries]
    )
