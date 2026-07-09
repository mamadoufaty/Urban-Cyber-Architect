"""Cartographies — plusieurs graphes d'urbanisme indépendants et versionnés par projet.

Une :class:`Cartography` représente une carte nommée (ex. « Urbanisme Technique »,
« Cybersécurité »...) au sein d'un projet. Son contenu (objets/relations du
métamodèle Club Urba, cf. ``UrbanismEntity``/``UrbanismRelation``) est toujours
rattaché à une :class:`CartographyVersion` précise — jamais directement au
projet ni à la cartographie — afin qu'aucune donnée ne soit partagée entre deux
cartographies, y compris entre deux versions successives d'une même cartographie
une fois qu'une version est validée (figée en lecture seule).

Le cycle de vie d'une version est : ``draft`` → (``in_validation``) → ``validated``
(figée) → toute nouvelle modification déclenche automatiquement la création
d'une nouvelle version ``draft`` (copie complète du graphe, cf.
``cartography_service.resolve_editable_version``).

Chaque évènement notable (création, modification, validation, nouvelle version,
restauration, duplication, archivage) est journalisé dans
:class:`CartographyHistory`.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

CARTOGRAPHY_TYPES: list[str] = [
    "urbanisme_si",
    "urbanisme_metier",
    "urbanisme_fonctionnel",
    "urbanisme_applicatif",
    "urbanisme_technique",
    "cybersecurite",
    "architecture_actuelle",
    "architecture_cible",
    "reseau",
    "cloud",
    "libre",
]

CARTOGRAPHY_TYPE_LABELS: dict[str, str] = {
    "urbanisme_si": "Urbanisme SI",
    "urbanisme_metier": "Urbanisme Métier",
    "urbanisme_fonctionnel": "Urbanisme Fonctionnel",
    "urbanisme_applicatif": "Urbanisme Applicatif",
    "urbanisme_technique": "Urbanisme Technique",
    "cybersecurite": "Cybersécurité",
    "architecture_actuelle": "Architecture actuelle",
    "architecture_cible": "Architecture cible",
    "reseau": "Réseau",
    "cloud": "Cloud",
    "libre": "Libre",
}

# Statuts partagés par Cartography.status et CartographyVersion.status.
CARTOGRAPHY_STATUSES: list[str] = ["draft", "in_validation", "validated", "archived"]

# Actions journalisées dans CartographyHistory.
HISTORY_ACTIONS: list[str] = [
    "created",
    "updated",
    "submitted_for_validation",
    "validated",
    "new_version",
    "restored",
    "duplicated",
    "archived",
    "unarchived",
    "imported",
    "deleted",
]


class Cartography(Base):
    """Une carte nommée d'un projet (ex. « Urbanisme Technique »)."""

    __tablename__ = "cartographies"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    type: Mapped[str] = mapped_column(String(50), default="libre", index=True)
    # Dénormalisé pour affichage rapide — reflète toujours la version courante (is_current=True).
    status: Mapped[str] = mapped_column(String(20), default="draft", index=True)
    version: Mapped[str] = mapped_column(String(20), default="1.0")
    author: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    validated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    validated_by: Mapped[str | None] = mapped_column(String(255), nullable=True)

    versions: Mapped[list["CartographyVersion"]] = relationship(
        "CartographyVersion",
        back_populates="cartography",
        cascade="all, delete-orphan",
        order_by="CartographyVersion.created_at",
    )
    history: Mapped[list["CartographyHistory"]] = relationship(
        "CartographyHistory",
        back_populates="cartography",
        cascade="all, delete-orphan",
        order_by="CartographyHistory.created_at.desc()",
    )


class CartographyVersion(Base):
    """Une version figée ou brouillon du graphe d'une cartographie."""

    __tablename__ = "cartography_versions"
    __table_args__ = (
        UniqueConstraint("cartography_id", "version", name="uq_cartography_version"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    cartography_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cartographies.id"), index=True
    )
    version: Mapped[str] = mapped_column(String(20), index=True)
    status: Mapped[str] = mapped_column(String(20), default="draft", index=True)
    # Une seule version "courante" (tête éditable ou dernière figée) par cartographie.
    is_current: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    author: Mapped[str | None] = mapped_column(String(255), nullable=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    validated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    validated_by: Mapped[str | None] = mapped_column(String(255), nullable=True)

    cartography: Mapped["Cartography"] = relationship(
        "Cartography", back_populates="versions"
    )


class CartographyHistory(Base):
    """Journal d'audit d'une cartographie (une ligne par évènement notable)."""

    __tablename__ = "cartography_history"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    cartography_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cartographies.id"), index=True
    )
    version_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("cartography_versions.id"), nullable=True, index=True
    )
    version: Mapped[str] = mapped_column(String(20))
    author: Mapped[str | None] = mapped_column(String(255), nullable=True)
    action: Mapped[str] = mapped_column(String(50), index=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    cartography: Mapped["Cartography"] = relationship(
        "Cartography", back_populates="history"
    )
