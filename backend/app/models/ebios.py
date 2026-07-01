"""Modèles persistés — module EBIOS RM (GRC)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, JSON, Uuid, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class EbiosAssessment(Base):
    """Analyse de risques EBIOS RM rattachée à un projet."""

    __tablename__ = "ebios_assessments"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id"), index=True)
    title: Mapped[str] = mapped_column(String(255), default="Analyse EBIOS RM")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="draft", index=True)
    current_workshop: Mapped[int] = mapped_column(Integer, default=1)
    version: Mapped[str] = mapped_column(String(20), default="1.0")
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
    extension_flags: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    workshops: Mapped[list["EbiosWorkshop"]] = relationship(back_populates="assessment", cascade="all, delete-orphan")
    records: Mapped[list["EbiosRecord"]] = relationship(back_populates="assessment", cascade="all, delete-orphan")
    links: Mapped[list["EbiosLink"]] = relationship(back_populates="assessment", cascade="all, delete-orphan")


class EbiosWorkshop(Base):
    """État et contenu d'un atelier EBIOS (1 à 5)."""

    __tablename__ = "ebios_workshops"
    __table_args__ = (UniqueConstraint("assessment_id", "workshop_number", name="uq_ebios_workshop"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    assessment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ebios_assessments.id"), index=True)
    workshop_number: Mapped[int] = mapped_column(Integer, index=True)
    code: Mapped[str] = mapped_column(String(50), index=True)
    status: Mapped[str] = mapped_column(String(50), default="available")
    progress_percent: Mapped[int] = mapped_column(Integer, default=0)
    summary: Mapped[dict] = mapped_column(JSON, default=dict)
    content: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    assessment: Mapped["EbiosAssessment"] = relationship(back_populates="workshops")


class EbiosRecord(Base):
    """Entité générique d'un atelier (source de risque, scénario, mesure…)."""

    __tablename__ = "ebios_records"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    assessment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ebios_assessments.id"), index=True)
    workshop_number: Mapped[int] = mapped_column(Integer, index=True)
    record_type: Mapped[str] = mapped_column(String(80), index=True)
    label: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    properties: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(50), default="draft")
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    assessment: Mapped["EbiosAssessment"] = relationship(back_populates="records")
    outgoing_links: Mapped[list["EbiosLink"]] = relationship(
        foreign_keys="EbiosLink.source_record_id", back_populates="source_record"
    )
    incoming_links: Mapped[list["EbiosLink"]] = relationship(
        foreign_keys="EbiosLink.target_record_id", back_populates="target_record"
    )


class EbiosLink(Base):
    """Lien typé entre entités EBIOS (chaînage scénarios, mesures…)."""

    __tablename__ = "ebios_links"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    assessment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ebios_assessments.id"), index=True)
    source_record_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ebios_records.id"), index=True)
    target_record_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ebios_records.id"), index=True)
    link_type: Mapped[str] = mapped_column(String(80), index=True)
    properties: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    assessment: Mapped["EbiosAssessment"] = relationship(back_populates="links")
    source_record: Mapped["EbiosRecord"] = relationship(
        foreign_keys=[source_record_id], back_populates="outgoing_links"
    )
    target_record: Mapped["EbiosRecord"] = relationship(
        foreign_keys=[target_record_id], back_populates="incoming_links"
    )
