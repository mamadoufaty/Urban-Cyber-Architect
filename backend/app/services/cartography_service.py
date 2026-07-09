"""Service cartographies — CRUD, versionning (copie-sur-écriture) et historique.

Concepts clés
-------------
- Une :class:`Cartography` est une carte nommée d'un projet (ex. « Urbanisme
  Technique »). Un projet peut en contenir plusieurs, totalement indépendantes.
- Chaque cartographie possède une ou plusieurs :class:`CartographyVersion`.
  Une seule version est « courante » (``is_current=True``) à la fois : c'est
  celle affichée par défaut et, si elle est en brouillon, celle qui est
  modifiable.
- Le contenu du graphe (``UrbanismEntity``/``UrbanismRelation``) est toujours
  rattaché à une version précise via ``cartography_version_id``. Dès qu'une
  version validée ou archivée doit être modifiée, une nouvelle version
  brouillon est automatiquement créée par copie complète du graphe
  (:func:`resolve_editable_version`) — la version validée reste inchangée et
  consultable en lecture seule.
- Toute résolution (lecture ou écriture) passe par ce module afin qu'aucun
  autre service n'ait à connaître le mécanisme de versionning.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cartography import Cartography, CartographyHistory, CartographyVersion
from app.models.entities import Project, UrbanismEntity, UrbanismRelation

DEFAULT_CARTOGRAPHY_NAME = "Cartographie principale"
DEFAULT_CARTOGRAPHY_TYPE = "urbanisme_si"
INITIAL_VERSION = "1.0"
FROZEN_STATUSES = {"validated", "archived"}


class CartographyError(Exception):
    """Erreur métier cartographie (404, statut invalide, etc.)."""


# ————————————————————————————————————————————————————————————————
# Historique
# ————————————————————————————————————————————————————————————————


async def log_history(
    db: AsyncSession,
    cartography: Cartography,
    version: CartographyVersion | None,
    *,
    author: str | None,
    action: str,
    comment: str | None = None,
) -> CartographyHistory:
    entry = CartographyHistory(
        cartography_id=cartography.id,
        version_id=version.id if version else None,
        version=version.version if version else cartography.version,
        author=author,
        action=action,
        comment=comment,
    )
    db.add(entry)
    cartography.updated_at = datetime.utcnow()
    await db.flush()
    return entry


def remap_id(id_map: dict[UUID, UUID], entity_id: UUID) -> UUID:
    """Réécrit un identifiant d'entité reçu du client après une éventuelle
    bascule de version (copie-sur-écriture) — no-op si l'id n'a pas changé."""
    return id_map.get(entity_id, entity_id)


async def get_cartography_history(
    db: AsyncSession, cartography_id: UUID
) -> list[CartographyHistory]:
    result = await db.execute(
        select(CartographyHistory)
        .where(CartographyHistory.cartography_id == cartography_id)
        .order_by(CartographyHistory.created_at.desc())
    )
    return list(result.scalars().all())


# ————————————————————————————————————————————————————————————————
# Résolution / création par défaut
# ————————————————————————————————————————————————————————————————


async def get_cartography_or_404(db: AsyncSession, cartography_id: UUID) -> Cartography:
    cartography = await db.get(Cartography, cartography_id)
    if not cartography:
        raise CartographyError("Cartographie introuvable")
    return cartography


async def get_version_or_404(
    db: AsyncSession, version_id: UUID
) -> tuple[Cartography, CartographyVersion]:
    """Résout une version précise (pour une lecture en dehors du fil « courant »),
    utilisée notamment pour consulter en lecture seule une ancienne version depuis
    le sélecteur de version du bandeau du moteur."""
    version = await db.get(CartographyVersion, version_id)
    if not version:
        raise CartographyError("Version introuvable")
    cartography = await get_cartography_or_404(db, version.cartography_id)
    return cartography, version


async def get_current_version(
    db: AsyncSession, cartography: Cartography
) -> CartographyVersion:
    result = await db.execute(
        select(CartographyVersion).where(
            CartographyVersion.cartography_id == cartography.id,
            CartographyVersion.is_current.is_(True),
        )
    )
    version = result.scalars().first()
    if version:
        return version
    # Filet de sécurité défensif — ne devrait pas se produire en usage normal.
    version = CartographyVersion(
        cartography_id=cartography.id,
        version=cartography.version or INITIAL_VERSION,
        status=cartography.status or "draft",
        is_current=True,
    )
    db.add(version)
    await db.flush()
    return version


async def _backfill_legacy_rows(
    db: AsyncSession, project_id: UUID, version: CartographyVersion
) -> None:
    """Rattache les entités/relations déjà en base (avant l'introduction des
    cartographies) à la version par défaut nouvellement créée."""
    result = await db.execute(
        select(UrbanismEntity).where(
            UrbanismEntity.project_id == project_id,
            UrbanismEntity.cartography_version_id.is_(None),
        )
    )
    entities = list(result.scalars().all())
    for entity in entities:
        entity.cartography_version_id = version.id

    result = await db.execute(
        select(UrbanismRelation).where(
            UrbanismRelation.project_id == project_id,
            UrbanismRelation.cartography_version_id.is_(None),
        )
    )
    relations = list(result.scalars().all())
    for relation in relations:
        relation.cartography_version_id = version.id

    if entities or relations:
        await db.flush()


async def ensure_default_cartography(db: AsyncSession, project: Project) -> Cartography:
    """Garantit qu'un projet possède au moins une cartographie.

    Idempotent. Si le projet possédait déjà un graphe d'urbanisme (créé avant
    cette évolution), celui-ci est automatiquement rattaché à la cartographie
    par défaut nouvellement créée — aucune donnée n'est perdue (§15).
    """
    result = await db.execute(
        select(Cartography)
        .where(Cartography.project_id == project.id)
        .order_by(Cartography.created_at)
    )
    existing = result.scalars().first()
    if existing:
        return existing

    cartography = Cartography(
        project_id=project.id,
        name=DEFAULT_CARTOGRAPHY_NAME,
        type=DEFAULT_CARTOGRAPHY_TYPE,
        description=None,
        status="draft",
        version=INITIAL_VERSION,
        is_active=True,
        author=None,
    )
    db.add(cartography)
    await db.flush()

    version = CartographyVersion(
        cartography_id=cartography.id,
        version=INITIAL_VERSION,
        status="draft",
        is_current=True,
    )
    db.add(version)
    await db.flush()

    await _backfill_legacy_rows(db, project.id, version)
    await log_history(
        db,
        cartography,
        version,
        author=None,
        action="created",
        comment="Cartographie par défaut créée automatiquement (migration).",
    )
    return cartography


async def ensure_default_cartography_for_all_projects(db: AsyncSession) -> int:
    """Backfill de démarrage — un appel idempotent sur tous les projets existants."""
    result = await db.execute(select(Project))
    projects = list(result.scalars().all())
    created = 0
    for project in projects:
        existing = await db.execute(
            select(Cartography.id)
            .where(Cartography.project_id == project.id)
            .limit(1)
        )
        if existing.scalar_one_or_none() is not None:
            continue
        await ensure_default_cartography(db, project)
        created += 1
    if created:
        await db.commit()
    return created


async def get_active_cartography(db: AsyncSession, project_id: UUID) -> Cartography:
    project = await db.get(Project, project_id)
    if not project:
        raise CartographyError("Projet introuvable")
    result = await db.execute(
        select(Cartography).where(
            Cartography.project_id == project_id, Cartography.is_active.is_(True)
        )
    )
    active = result.scalars().first()
    if active:
        return active
    return await ensure_default_cartography(db, project)


async def list_cartographies(db: AsyncSession, project_id: UUID) -> list[Cartography]:
    project = await db.get(Project, project_id)
    if not project:
        raise CartographyError("Projet introuvable")
    await ensure_default_cartography(db, project)
    result = await db.execute(
        select(Cartography)
        .where(Cartography.project_id == project_id)
        .order_by(Cartography.created_at)
    )
    return list(result.scalars().all())


async def resolve_read_version(
    db: AsyncSession, project_id: UUID, cartography_id: UUID | None = None
) -> tuple[Cartography, CartographyVersion]:
    """Résout la cartographie + sa version courante pour une lecture (sans COW)."""
    if cartography_id:
        cartography = await get_cartography_or_404(db, cartography_id)
        if cartography.project_id != project_id:
            raise CartographyError("Cette cartographie n'appartient pas au projet")
    else:
        cartography = await get_active_cartography(db, project_id)
    version = await get_current_version(db, cartography)
    return cartography, version


def _next_version_label(current: str) -> str:
    parts = current.split(".")
    try:
        major = int(parts[0])
        minor = int(parts[1]) if len(parts) > 1 else 0
    except ValueError:
        return "1.1"
    return f"{major}.{minor + 1}"


async def _copy_version_content(
    db: AsyncSession, source_version: CartographyVersion, target_version: CartographyVersion
) -> dict[UUID, UUID]:
    """Copie intégrale (nouveaux id) des entités/relations d'une version vers une
    autre. Retourne le dictionnaire {ancien_id_entité: nouvel_id_entité} afin que
    les appelants puissent réécrire des identifiants reçus du client qui
    référencent encore l'ancienne version (cf. ``resolve_editable_version``)."""
    result = await db.execute(
        select(UrbanismEntity).where(
            UrbanismEntity.cartography_version_id == source_version.id
        )
    )
    source_entities = list(result.scalars().all())

    result = await db.execute(
        select(UrbanismRelation).where(
            UrbanismRelation.cartography_version_id == source_version.id
        )
    )
    source_relations = list(result.scalars().all())

    id_map: dict[UUID, UUID] = {}
    for entity in source_entities:
        clone = UrbanismEntity(
            project_id=entity.project_id,
            cartography_version_id=target_version.id,
            entity_type=entity.entity_type,
            couche=entity.couche,
            label=entity.label,
            description=entity.description,
            properties=deepcopy(entity.properties or {}),
        )
        db.add(clone)
        await db.flush()
        id_map[entity.id] = clone.id

    for relation in source_relations:
        new_source = id_map.get(relation.source_id)
        new_target = id_map.get(relation.target_id)
        if not new_source or not new_target:
            continue
        db.add(
            UrbanismRelation(
                project_id=relation.project_id,
                cartography_version_id=target_version.id,
                source_id=new_source,
                target_id=new_target,
                relation_type=relation.relation_type,
                category=relation.category,
                commentaire=relation.commentaire,
                criticite=relation.criticite,
                properties=deepcopy(relation.properties or {}),
            )
        )
    await db.flush()
    return id_map


async def resolve_editable_version(
    db: AsyncSession,
    project_id: UUID,
    cartography_id: UUID | None = None,
    *,
    author: str | None = None,
) -> tuple[Cartography, CartographyVersion, dict[UUID, UUID]]:
    """Résout la cartographie + une version modifiable pour une écriture.

    Si la version courante est figée (validée ou archivée), une nouvelle
    version brouillon est automatiquement créée par copie complète du graphe
    (§5 — "Nouvelle modification → Création automatique d'une nouvelle
    version"). Lève :class:`CartographyError` si la cartographie elle-même est
    archivée (celle-ci ne peut plus recevoir de nouvelle version, §9).

    Retourne aussi un dictionnaire de correspondance ``{ancien_id: nouvel_id}``
    des entités copiées (vide si aucune bascule de version n'a eu lieu) : les
    appelants doivent l'utiliser pour réécrire tout identifiant d'entité reçu
    du client et qui référencerait encore l'ancienne version figée.
    """
    cartography, version = await resolve_read_version(db, project_id, cartography_id)
    if cartography.is_archived:
        raise CartographyError(
            "Cette cartographie est archivée : elle est consultable mais ne peut plus être modifiée."
        )
    if version.status not in FROZEN_STATUSES:
        return cartography, version, {}

    new_version, id_map = await _create_next_draft_version(db, cartography, version, author=author)
    return cartography, new_version, id_map


async def _create_next_draft_version(
    db: AsyncSession,
    cartography: Cartography,
    source_version: CartographyVersion,
    *,
    author: str | None,
    comment: str | None = None,
) -> tuple[CartographyVersion, dict[UUID, UUID]]:
    source_version.is_current = False
    new_label = _next_version_label(source_version.version)
    new_version = CartographyVersion(
        cartography_id=cartography.id,
        version=new_label,
        status="draft",
        is_current=True,
        author=author,
    )
    db.add(new_version)
    await db.flush()

    id_map = await _copy_version_content(db, source_version, new_version)

    cartography.version = new_label
    cartography.status = "draft"
    await db.flush()

    await log_history(
        db,
        cartography,
        new_version,
        author=author,
        action="new_version",
        comment=comment
        or f"Nouvelle version créée automatiquement suite à modification de la version {source_version.version} (figée).",
    )
    return new_version, id_map


# ————————————————————————————————————————————————————————————————
# CRUD cartographies
# ————————————————————————————————————————————————————————————————


async def create_cartography(
    db: AsyncSession,
    project_id: UUID,
    *,
    name: str,
    type_: str,
    description: str | None,
    author: str | None,
) -> Cartography:
    project = await db.get(Project, project_id)
    if not project:
        raise CartographyError("Projet introuvable")

    # Une seule cartographie active à la fois — la nouvelle devient active (§3).
    result = await db.execute(
        select(Cartography).where(
            Cartography.project_id == project_id, Cartography.is_active.is_(True)
        )
    )
    for other in result.scalars().all():
        other.is_active = False

    cartography = Cartography(
        project_id=project_id,
        name=name.strip(),
        type=type_,
        description=(description or None),
        status="draft",
        version=INITIAL_VERSION,
        is_active=True,
        author=author,
    )
    db.add(cartography)
    await db.flush()

    version = CartographyVersion(
        cartography_id=cartography.id,
        version=INITIAL_VERSION,
        status="draft",
        is_current=True,
        author=author,
    )
    db.add(version)
    await db.flush()

    await log_history(
        db, cartography, version, author=author, action="created", comment=None
    )
    await db.commit()
    await db.refresh(cartography)
    return cartography


async def update_cartography(
    db: AsyncSession,
    cartography_id: UUID,
    *,
    name: str | None = None,
    description: str | None = None,
    type_: str | None = None,
    author: str | None = None,
) -> Cartography:
    cartography = await get_cartography_or_404(db, cartography_id)
    if name is not None:
        cartography.name = name.strip()
    if description is not None:
        cartography.description = description or None
    if type_ is not None:
        cartography.type = type_
    cartography.updated_at = datetime.utcnow()
    await log_history(db, cartography, None, author=author, action="updated")
    await db.commit()
    await db.refresh(cartography)
    return cartography


async def delete_cartography(db: AsyncSession, cartography_id: UUID) -> None:
    cartography = await get_cartography_or_404(db, cartography_id)
    version_ids = list(
        (
            await db.execute(
                select(CartographyVersion.id).where(
                    CartographyVersion.cartography_id == cartography_id
                )
            )
        )
        .scalars()
        .all()
    )
    if version_ids:
        await db.execute(
            UrbanismRelation.__table__.delete().where(
                UrbanismRelation.cartography_version_id.in_(version_ids)
            )
        )
        await db.execute(
            UrbanismEntity.__table__.delete().where(
                UrbanismEntity.cartography_version_id.in_(version_ids)
            )
        )
    was_active = cartography.is_active
    project_id = cartography.project_id
    await db.delete(cartography)
    await db.flush()

    if was_active:
        result = await db.execute(
            select(Cartography)
            .where(Cartography.project_id == project_id)
            .order_by(Cartography.created_at)
        )
        remaining = result.scalars().first()
        if remaining:
            remaining.is_active = True
    await db.commit()


# ————————————————————————————————————————————————————————————————
# Versionning — validation, nouvelle version manuelle, restauration, duplication
# ————————————————————————————————————————————————————————————————


async def submit_for_validation(
    db: AsyncSession, cartography_id: UUID, *, author: str | None
) -> Cartography:
    cartography = await get_cartography_or_404(db, cartography_id)
    version = await get_current_version(db, cartography)
    if version.status != "draft":
        raise CartographyError("Seule une version en brouillon peut être soumise à validation.")
    version.status = "in_validation"
    cartography.status = "in_validation"
    await log_history(
        db, cartography, version, author=author, action="submitted_for_validation"
    )
    await db.commit()
    await db.refresh(cartography)
    return cartography


async def validate_cartography(
    db: AsyncSession,
    cartography_id: UUID,
    *,
    validated_by: str | None,
    comment: str | None = None,
) -> Cartography:
    cartography = await get_cartography_or_404(db, cartography_id)
    version = await get_current_version(db, cartography)
    if version.status == "archived":
        raise CartographyError("Une version archivée ne peut pas être validée.")
    now = datetime.now(timezone.utc)
    version.status = "validated"
    version.validated_at = now
    version.validated_by = validated_by
    cartography.status = "validated"
    cartography.validated_at = now
    cartography.validated_by = validated_by
    await log_history(
        db, cartography, version, author=validated_by, action="validated", comment=comment
    )
    await db.commit()
    await db.refresh(cartography)
    return cartography


async def create_new_version(
    db: AsyncSession, cartography_id: UUID, *, author: str | None, comment: str | None = None
) -> Cartography:
    """Action manuelle « Créer une nouvelle version » — force une nouvelle
    version brouillon même si la version courante n'est pas figée."""
    cartography = await get_cartography_or_404(db, cartography_id)
    if cartography.is_archived:
        raise CartographyError("Cette cartographie est archivée.")
    version = await get_current_version(db, cartography)
    await _create_next_draft_version(db, cartography, version, author=author, comment=comment)
    await db.commit()
    await db.refresh(cartography)
    return cartography


async def create_new_version_full(
    db: AsyncSession, cartography_id: UUID, *, author: str | None, comment: str | None = None
) -> tuple[Cartography, CartographyVersion, dict[UUID, UUID]]:
    """Variante de :func:`create_new_version` qui retourne aussi la nouvelle
    version et la correspondance d'identifiants (utile aux appelants API)."""
    cartography = await get_cartography_or_404(db, cartography_id)
    if cartography.is_archived:
        raise CartographyError("Cette cartographie est archivée.")
    version = await get_current_version(db, cartography)
    new_version, id_map = await _create_next_draft_version(
        db, cartography, version, author=author, comment=comment
    )
    await db.commit()
    await db.refresh(cartography)
    await db.refresh(new_version)
    return cartography, new_version, id_map


async def restore_version(
    db: AsyncSession,
    cartography_id: UUID,
    version_id: UUID,
    *,
    author: str | None,
) -> Cartography:
    """Restaure une version historique — crée une nouvelle version brouillon
    dont le contenu est une copie de la version restaurée."""
    cartography = await get_cartography_or_404(db, cartography_id)
    if cartography.is_archived:
        raise CartographyError("Cette cartographie est archivée.")
    target = await db.get(CartographyVersion, version_id)
    if not target or target.cartography_id != cartography_id:
        raise CartographyError("Version introuvable pour cette cartographie.")

    current = await get_current_version(db, cartography)
    current.is_current = False
    new_label = _next_version_label(current.version)
    new_version = CartographyVersion(
        cartography_id=cartography.id,
        version=new_label,
        status="draft",
        is_current=True,
        author=author,
    )
    db.add(new_version)
    await db.flush()
    await _copy_version_content(db, target, new_version)

    cartography.version = new_label
    cartography.status = "draft"
    await log_history(
        db,
        cartography,
        new_version,
        author=author,
        action="restored",
        comment=f"Restauration du contenu de la version {target.version}.",
    )
    await db.commit()
    await db.refresh(cartography)
    return cartography


async def duplicate_cartography(
    db: AsyncSession,
    cartography_id: UUID,
    *,
    name: str,
    author: str | None,
) -> Cartography:
    source = await get_cartography_or_404(db, cartography_id)
    source_version = await get_current_version(db, source)

    clone = Cartography(
        project_id=source.project_id,
        name=name.strip(),
        type=source.type,
        description=source.description,
        status="draft",
        version=INITIAL_VERSION,
        is_active=False,
        author=author,
    )
    db.add(clone)
    await db.flush()

    clone_version = CartographyVersion(
        cartography_id=clone.id,
        version=INITIAL_VERSION,
        status="draft",
        is_current=True,
        author=author,
    )
    db.add(clone_version)
    await db.flush()

    await _copy_version_content(db, source_version, clone_version)

    await log_history(
        db,
        clone,
        clone_version,
        author=author,
        action="duplicated",
        comment=f"Dupliqué depuis « {source.name} » (v{source_version.version}).",
    )
    await db.commit()
    await db.refresh(clone)
    return clone


async def archive_cartography(
    db: AsyncSession, cartography_id: UUID, *, author: str | None
) -> Cartography:
    cartography = await get_cartography_or_404(db, cartography_id)
    cartography.is_archived = True
    cartography.status = "archived"
    if cartography.is_active:
        cartography.is_active = False
    version = await get_current_version(db, cartography)
    version.status = "archived"
    await log_history(db, cartography, version, author=author, action="archived")
    await db.commit()
    await db.refresh(cartography)
    return cartography


async def unarchive_cartography(
    db: AsyncSession, cartography_id: UUID, *, author: str | None
) -> Cartography:
    cartography = await get_cartography_or_404(db, cartography_id)
    cartography.is_archived = False
    version = await get_current_version(db, cartography)
    cartography.status = version.status if version.status != "archived" else "draft"
    if version.status == "archived":
        version.status = "draft"
    await log_history(db, cartography, version, author=author, action="unarchived")
    await db.commit()
    await db.refresh(cartography)
    return cartography


async def activate_cartography(
    db: AsyncSession, cartography_id: UUID, *, author: str | None = None
) -> Cartography:
    """Rend une cartographie « active » pour le projet (une seule à la fois).

    C'est cette cartographie active qui est utilisée implicitement par les
    modules qui ne connaissent pas encore la notion de sélection explicite
    (EBIOS, imports historiques, etc. — cf. §12/§15)."""
    cartography = await get_cartography_or_404(db, cartography_id)
    result = await db.execute(
        select(Cartography).where(
            Cartography.project_id == cartography.project_id, Cartography.is_active.is_(True)
        )
    )
    for other in result.scalars().all():
        if other.id != cartography.id:
            other.is_active = False
    cartography.is_active = True
    await db.commit()
    await db.refresh(cartography)
    return cartography


async def list_versions(
    db: AsyncSession, cartography_id: UUID
) -> list[CartographyVersion]:
    result = await db.execute(
        select(CartographyVersion)
        .where(CartographyVersion.cartography_id == cartography_id)
        .order_by(CartographyVersion.created_at.desc())
    )
    return list(result.scalars().all())
