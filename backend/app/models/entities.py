import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, Text, JSON, Uuid, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    organization: Mapped[dict] = mapped_column(JSON, default=dict)
    referentials: Mapped[list] = mapped_column(JSON, default=list)
    urbanism: Mapped[dict] = mapped_column(JSON, default=dict)
    objectives: Mapped[list] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(50), default="draft")
    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("organizations.id"), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    orchestrations: Mapped[list["OrchestrationRun"]] = relationship(back_populates="project")
    decisions: Mapped[list["HumanDecision"]] = relationship(back_populates="project")
    graph_nodes: Mapped[list["GraphNode"]] = relationship(back_populates="project")
    tenant_organization: Mapped["Organization | None"] = relationship(
        "Organization", back_populates="projects"
    )


class OrchestrationRun(Base):
    __tablename__ = "orchestration_runs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id"))
    models: Mapped[list] = mapped_column(JSON)
    prompt: Mapped[str] = mapped_column(Text)
    template_name: Mapped[str] = mapped_column(String(100))
    responses: Mapped[list] = mapped_column(JSON)
    judge_result: Mapped[dict] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(50), default="pending_human_validation")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    project: Mapped["Project"] = relationship(back_populates="orchestrations")


class HumanDecision(Base):
    __tablename__ = "human_decisions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id"))
    orchestration_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("orchestration_runs.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(50))
    selected_model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    merged_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    modified_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    project: Mapped["Project"] = relationship(back_populates="decisions")


class AIGovernanceConfig(Base):
    __tablename__ = "ai_governance_config"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    models: Mapped[list] = mapped_column(JSON, default=lambda: ["mock-gpt", "mock-claude", "mock-gemini"])
    judge_id: Mapped[str] = mapped_column(String(100), default="mock-judge")
    urbanisme_weight: Mapped[float] = mapped_column(Float, default=0.20)
    conformite_weight: Mapped[float] = mapped_column(Float, default=0.25)
    ebios_weight: Mapped[float] = mapped_column(Float, default=0.30)
    architecture_weight: Mapped[float] = mapped_column(Float, default=0.25)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class WazuhConnectorConfig(Base):
    """Configuration singleton du connecteur Wazuh (lecture seule)."""

    __tablename__ = "wazuh_connector_config"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    base_url: Mapped[str] = mapped_column(String(512), default="")
    username: Mapped[str] = mapped_column(String(255), default="")
    password: Mapped[str] = mapped_column(String(255), default="")
    verify_ssl: Mapped[bool] = mapped_column(default=True)
    indexer_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    indexer_username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    indexer_password: Mapped[str | None] = mapped_column(String(255), nullable=True)
    enabled: Mapped[bool] = mapped_column(default=False)
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class GraphNode(Base):
    __tablename__ = "graph_nodes"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id"))
    node_type: Mapped[str] = mapped_column(String(50))
    label: Mapped[str] = mapped_column(String(255))
    properties: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    project: Mapped["Project"] = relationship(back_populates="graph_nodes")


class GraphEdge(Base):
    __tablename__ = "graph_edges"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id"))
    source_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("graph_nodes.id"))
    target_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("graph_nodes.id"))
    relation: Mapped[str] = mapped_column(String(50))


class UrbanismEntity(Base):
    """Objet du métamodèle Club Urba — source de vérité du moteur d'urbanisme."""

    __tablename__ = "urbanism_entities"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id"), index=True)
    entity_type: Mapped[str] = mapped_column(String(50), index=True)
    couche: Mapped[str] = mapped_column(String(50), index=True)
    label: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    properties: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    outgoing: Mapped[list["UrbanismRelation"]] = relationship(
        foreign_keys="UrbanismRelation.source_id", back_populates="source_entity"
    )
    incoming: Mapped[list["UrbanismRelation"]] = relationship(
        foreign_keys="UrbanismRelation.target_id", back_populates="target_entity"
    )


class UrbanismRelation(Base):
    """Relation nommée persistée entre deux entités d'urbanisme."""

    __tablename__ = "urbanism_relations"
    __table_args__ = (
        UniqueConstraint(
            "project_id", "source_id", "relation_type", "target_id",
            name="uq_urbanism_relation",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id"), index=True)
    source_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("urbanism_entities.id"), index=True)
    target_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("urbanism_entities.id"), index=True)
    relation_type: Mapped[str] = mapped_column(String(100))
    category: Mapped[str] = mapped_column(String(50), index=True)
    commentaire: Mapped[str | None] = mapped_column(Text, nullable=True)
    criticite: Mapped[str | None] = mapped_column(String(20), nullable=True)
    properties: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    source_entity: Mapped["UrbanismEntity"] = relationship(
        foreign_keys=[source_id], back_populates="outgoing"
    )
    target_entity: Mapped["UrbanismEntity"] = relationship(
        foreign_keys=[target_id], back_populates="incoming"
    )
