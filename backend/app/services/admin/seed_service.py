"""Initialisation idempotente — données Administration.

Seed des utilisateurs de démonstration
--------------------------------------
Emplacement : ``backend/app/services/admin/seed_service.py`` (constante ``DEMO_USERS``).

Déclenchement : au démarrage de l'API via ``run_admin_seed`` appelé dans le
``lifespan`` de ``backend/app/main.py``.

Méthode :
- pour chaque compte de ``DEMO_USERS``, recherche par ``User.username`` ;
- création uniquement si le login est absent (pas de doublon, pas de mise à jour) ;
- mot de passe haché avec ``app.services.password_service.hash_password`` (bcrypt).
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admin import Organization, Permission, Role, RolePermission, User
from app.services.password_service import hash_password, verify_password

DEFAULT_ORG = {
    "name": "Métropolis Test",
    "code": "metropolis-test",
    "description": "Organisation de démonstration par défaut",
}

SYSTEM_ROLES = [
    ("Super Administrateur", "superadmin", "Accès super administrateur à la plateforme", True),
    ("Administrateur", "admin", "Accès complet à la plateforme", True),
    ("RSSI", "rssi", "Pilotage cybersécurité et GRC", True),
    ("Consultant", "consultant", "Accompagnement projet et urbanisme", True),
    ("SOC", "soc", "Opérations SOC et connecteurs", True),
    ("Métier", "metier", "Accès urbanisme métier", True),
]

BASE_PERMISSIONS: list[tuple[str, str, str, str]] = [
    ("dashboard", "read", "dashboard:read", "Consulter le tableau de bord"),
    ("projects", "read", "projects:read", "Consulter les projets"),
    ("projects", "create", "projects:create", "Créer des projets"),
    ("urbanism", "read", "urbanism:read", "Consulter l'urbanisme"),
    ("urbanism", "write", "urbanism:write", "Modifier l'urbanisme"),
    ("ebios", "read", "ebios:read", "Consulter EBIOS RM"),
    ("ebios", "write", "ebios:write", "Modifier EBIOS RM"),
    ("grc", "read", "grc:read", "Consulter la GRC"),
    ("grc", "write", "grc:write", "Modifier la GRC"),
    ("soc", "read", "soc:read", "Consulter le SOC"),
    ("soc", "write", "soc:write", "Modifier le SOC"),
    ("wazuh", "read", "wazuh:read", "Consulter Wazuh"),
    ("wazuh", "configure", "wazuh:configure", "Configurer Wazuh"),
    ("deliverables", "read", "deliverables:read", "Consulter les livrables"),
    ("deliverables", "generate", "deliverables:generate", "Générer des livrables"),
    ("administration", "read", "administration:read", "Consulter l'administration"),
    ("administration", "write", "administration:write", "Gérer l'administration"),
]

ALL_PERMISSION_CODES = [p[2] for p in BASE_PERMISSIONS]

ROLE_PERMISSION_CODES: dict[str, list[str]] = {
    "superadmin": ALL_PERMISSION_CODES,
    "admin": ALL_PERMISSION_CODES,
    "rssi": [
        "dashboard:read",
        "projects:read",
        "projects:create",
        "urbanism:read",
        "urbanism:write",
        "ebios:read",
        "ebios:write",
        "grc:read",
        "grc:write",
        "soc:read",
        "soc:write",
        "wazuh:read",
        "wazuh:configure",
        "deliverables:read",
        "deliverables:generate",
        "administration:read",
    ],
    "consultant": [
        "dashboard:read",
        "projects:read",
        "projects:create",
        "urbanism:read",
        "urbanism:write",
        "ebios:read",
        "ebios:write",
        "grc:read",
        "grc:write",
        "deliverables:read",
        "deliverables:generate",
    ],
    "soc": [
        "dashboard:read",
        "projects:read",
        "soc:read",
        "soc:write",
        "wazuh:read",
        "wazuh:configure",
    ],
    "metier": [
        "dashboard:read",
        "urbanism:read",
    ],
}

# (username, mot de passe en clair, code rôle, libellé affiché)
DEMO_USERS: list[tuple[str, str, str, str]] = [
    ("admin", "Admin@123", "superadmin", "Super Administrateur"),
    ("admin1", "Admin1@123", "admin", "Administrateur 1"),
    ("admin2", "Admin2@123", "admin", "Administrateur 2"),
    ("admin3", "Admin3@123", "admin", "Administrateur 3"),
    ("demo", "Demo@123", "consultant", "Consultant démo"),
]


async def _get_or_create_organization(db: AsyncSession) -> Organization:
    result = await db.execute(select(Organization).where(Organization.code == DEFAULT_ORG["code"]))
    org = result.scalar_one_or_none()
    if org:
        return org
    org = Organization(**DEFAULT_ORG)
    db.add(org)
    await db.flush()
    return org


async def _get_or_create_role(
    db: AsyncSession, name: str, code: str, description: str, is_system: bool
) -> Role:
    result = await db.execute(select(Role).where(Role.code == code))
    role = result.scalar_one_or_none()
    if role:
        return role
    role = Role(name=name, code=code, description=description, is_system=is_system)
    db.add(role)
    await db.flush()
    return role


async def _get_or_create_permission(
    db: AsyncSession, module: str, action: str, code: str, description: str
) -> Permission:
    result = await db.execute(select(Permission).where(Permission.code == code))
    perm = result.scalar_one_or_none()
    if perm:
        return perm
    perm = Permission(module=module, action=action, code=code, description=description)
    db.add(perm)
    await db.flush()
    return perm


async def _get_user_by_username(db: AsyncSession, username: str) -> User | None:
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def _ensure_demo_user(
    db: AsyncSession,
    org: Organization,
    roles_by_code: dict[str, Role],
    username: str,
    password: str,
    role_code: str,
    display: str,
) -> None:
    if await _get_user_by_username(db, username):
        return
    role = roles_by_code[role_code]
    db.add(
        User(
            username=username,
            password_hash=hash_password(password),
            first_name=display,
            organization_id=org.id,
            role_id=role.id,
            status="active",
        )
    )


async def _ensure_role_permission(db: AsyncSession, role: Role, permission: Permission) -> None:
    result = await db.execute(
        select(RolePermission).where(
            RolePermission.role_id == role.id,
            RolePermission.permission_id == permission.id,
        )
    )
    if result.scalar_one_or_none():
        return
    db.add(RolePermission(role_id=role.id, permission_id=permission.id))


async def run_admin_seed(db: AsyncSession) -> None:
    """Seed idempotent — organisations, rôles, permissions, utilisateurs de démo."""
    org = await _get_or_create_organization(db)

    permissions_by_code: dict[str, Permission] = {}
    for module, action, code, description in BASE_PERMISSIONS:
        permissions_by_code[code] = await _get_or_create_permission(
            db, module, action, code, description
        )

    roles_by_code: dict[str, Role] = {}
    for name, code, description, is_system in SYSTEM_ROLES:
        role = await _get_or_create_role(db, name, code, description, is_system)
        roles_by_code[code] = role
        for perm_code in ROLE_PERMISSION_CODES.get(code, []):
            perm = permissions_by_code.get(perm_code)
            if perm:
                await _ensure_role_permission(db, role, perm)

    for username, password, role_code, display in DEMO_USERS:
        await _ensure_demo_user(db, org, roles_by_code, username, password, role_code, display)

    from app.services.admin.referential_service import run_referential_seed

    await run_referential_seed(db)


async def verify_seed_password(username: str, plain_password: str, db: AsyncSession) -> bool:
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if not user:
        return False
    return verify_password(plain_password, user.password_hash)
