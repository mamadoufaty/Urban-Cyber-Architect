"""Routes API — module Administration."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.admin import (
    AuditLogListResponse,
    AuditLogRead,
    OrganizationCreate,
    OrganizationListResponse,
    OrganizationRead,
    OrganizationUpdate,
    PermissionListResponse,
    PermissionRead,
    RoleCreate,
    RoleListResponse,
    RolePermissionsUpdate,
    RoleRead,
    RoleUpdate,
    UserCreate,
    UserListResponse,
    UserRead,
    UserResetPassword,
    UserUpdate,
)
from app.services.admin import audit_service, organization_service, permission_service, role_service, user_service

router = APIRouter(prefix="/admin", tags=["administration"])


def _http_error(exc: ValueError) -> HTTPException:
    return HTTPException(status_code=400, detail=str(exc))


@router.get("/users", response_model=UserListResponse)
async def api_list_users(db: AsyncSession = Depends(get_db)):
    items, total = await user_service.list_users(db)
    return UserListResponse(total=total, items=items)


@router.post("/users", response_model=UserRead, status_code=201)
async def api_create_user(body: UserCreate, db: AsyncSession = Depends(get_db)):
    try:
        user = await user_service.create_user(db, body)
        await audit_service.log_action(
            db, action="user.create", object_type="user", object_id=str(user.id)
        )
        await db.commit()
        return user
    except ValueError as e:
        raise _http_error(e) from e


@router.get("/users/{user_id}", response_model=UserRead)
async def api_get_user(user_id: UUID, db: AsyncSession = Depends(get_db)):
    try:
        return await user_service.get_user(db, user_id)
    except ValueError as e:
        raise HTTPException(404, str(e)) from e


@router.put("/users/{user_id}", response_model=UserRead)
async def api_update_user(user_id: UUID, body: UserUpdate, db: AsyncSession = Depends(get_db)):
    try:
        user = await user_service.update_user(db, user_id, body)
        await audit_service.log_action(
            db, action="user.update", object_type="user", object_id=str(user_id)
        )
        await db.commit()
        return user
    except ValueError as e:
        raise HTTPException(404, str(e)) from e


@router.delete("/users/{user_id}", status_code=204)
async def api_delete_user(user_id: UUID, db: AsyncSession = Depends(get_db)):
    try:
        await user_service.delete_user(db, user_id)
        await audit_service.log_action(
            db, action="user.delete", object_type="user", object_id=str(user_id)
        )
        await db.commit()
    except ValueError as e:
        raise HTTPException(404, str(e)) from e


@router.patch("/users/{user_id}/disable", response_model=UserRead)
async def api_disable_user(user_id: UUID, db: AsyncSession = Depends(get_db)):
    try:
        user = await user_service.disable_user(db, user_id)
        await audit_service.log_action(
            db, action="user.disable", object_type="user", object_id=str(user_id)
        )
        await db.commit()
        return user
    except ValueError as e:
        raise HTTPException(404, str(e)) from e


@router.patch("/users/{user_id}/enable", response_model=UserRead)
async def api_enable_user(user_id: UUID, db: AsyncSession = Depends(get_db)):
    try:
        user = await user_service.enable_user(db, user_id)
        await audit_service.log_action(
            db, action="user.enable", object_type="user", object_id=str(user_id)
        )
        await db.commit()
        return user
    except ValueError as e:
        raise HTTPException(404, str(e)) from e


@router.patch("/users/{user_id}/reset-password", response_model=UserRead)
async def api_reset_password(
    user_id: UUID, body: UserResetPassword, db: AsyncSession = Depends(get_db)
):
    try:
        user = await user_service.reset_password(db, user_id, body.password)
        await audit_service.log_action(
            db, action="user.reset_password", object_type="user", object_id=str(user_id)
        )
        await db.commit()
        return user
    except ValueError as e:
        raise HTTPException(404, str(e)) from e


@router.get("/organizations", response_model=OrganizationListResponse)
async def api_list_organizations(db: AsyncSession = Depends(get_db)):
    items, total = await organization_service.list_organizations(db)
    return OrganizationListResponse(
        total=total, items=[OrganizationRead.model_validate(o) for o in items]
    )


@router.post("/organizations", response_model=OrganizationRead, status_code=201)
async def api_create_organization(body: OrganizationCreate, db: AsyncSession = Depends(get_db)):
    try:
        org = await organization_service.create_organization(db, body)
        await audit_service.log_action(
            db, action="organization.create", object_type="organization", object_id=str(org.id)
        )
        await db.commit()
        return OrganizationRead.model_validate(org)
    except ValueError as e:
        raise _http_error(e) from e


@router.get("/organizations/{organization_id}", response_model=OrganizationRead)
async def api_get_organization(organization_id: UUID, db: AsyncSession = Depends(get_db)):
    try:
        org = await organization_service.get_organization(db, organization_id)
        return OrganizationRead.model_validate(org)
    except ValueError as e:
        raise HTTPException(404, str(e)) from e


@router.put("/organizations/{organization_id}", response_model=OrganizationRead)
async def api_update_organization(
    organization_id: UUID, body: OrganizationUpdate, db: AsyncSession = Depends(get_db)
):
    try:
        org = await organization_service.update_organization(db, organization_id, body)
        await audit_service.log_action(
            db,
            action="organization.update",
            object_type="organization",
            object_id=str(organization_id),
        )
        await db.commit()
        return OrganizationRead.model_validate(org)
    except ValueError as e:
        raise HTTPException(404, str(e)) from e


@router.get("/roles", response_model=RoleListResponse)
async def api_list_roles(db: AsyncSession = Depends(get_db)):
    items, total = await role_service.list_roles(db)
    return RoleListResponse(total=total, items=items)


@router.post("/roles", response_model=RoleRead, status_code=201)
async def api_create_role(body: RoleCreate, db: AsyncSession = Depends(get_db)):
    try:
        role = await role_service.create_role(db, body)
        await audit_service.log_action(
            db, action="role.create", object_type="role", object_id=str(role.id)
        )
        await db.commit()
        return role
    except ValueError as e:
        raise _http_error(e) from e


@router.get("/roles/{role_id}", response_model=RoleRead)
async def api_get_role(role_id: UUID, db: AsyncSession = Depends(get_db)):
    try:
        return await role_service.get_role(db, role_id)
    except ValueError as e:
        raise HTTPException(404, str(e)) from e


@router.put("/roles/{role_id}", response_model=RoleRead)
async def api_update_role(role_id: UUID, body: RoleUpdate, db: AsyncSession = Depends(get_db)):
    try:
        role = await role_service.update_role(db, role_id, body)
        await audit_service.log_action(
            db, action="role.update", object_type="role", object_id=str(role_id)
        )
        await db.commit()
        return role
    except ValueError as e:
        raise HTTPException(404, str(e)) from e


@router.put("/roles/{role_id}/permissions", response_model=RoleRead)
async def api_assign_role_permissions(
    role_id: UUID, body: RolePermissionsUpdate, db: AsyncSession = Depends(get_db)
):
    try:
        role = await role_service.assign_permissions(db, role_id, body.permission_ids)
        await audit_service.log_action(
            db,
            action="role.assign_permissions",
            object_type="role",
            object_id=str(role_id),
            details={"permission_count": len(body.permission_ids)},
        )
        await db.commit()
        return role
    except ValueError as e:
        raise _http_error(e) from e


@router.get("/permissions", response_model=PermissionListResponse)
async def api_list_permissions(db: AsyncSession = Depends(get_db)):
    items, total = await permission_service.list_permissions(db)
    return PermissionListResponse(
        total=total, items=[PermissionRead.model_validate(p) for p in items]
    )


@router.get("/audit-logs", response_model=AuditLogListResponse)
async def api_list_audit_logs(db: AsyncSession = Depends(get_db)):
    items, total = await audit_service.list_audit_logs(db)
    return AuditLogListResponse(total=total, items=items)
