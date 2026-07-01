from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.entities import AIGovernanceConfig, HumanDecision, Project
from app.schemas.api import AIGovernanceResponse, AIGovernanceUpdate, HumanDecisionCreate, HumanDecisionResponse
from app.services.knowledge_graph import KnowledgeGraphService
from app.services.validation import ValidationService

router = APIRouter(tags=["validation", "governance", "graph"])

validation_service = ValidationService()
graph_service = KnowledgeGraphService()


@router.post("/projects/{project_id}/decisions", response_model=HumanDecisionResponse)
async def create_decision(
    project_id: UUID,
    data: HumanDecisionCreate,
    db: AsyncSession = Depends(get_db),
):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    return await validation_service.record_decision(db, project, data)


@router.get("/projects/{project_id}/decisions", response_model=list[HumanDecisionResponse])
async def list_decisions(project_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(HumanDecision)
        .where(HumanDecision.project_id == project_id)
        .order_by(HumanDecision.created_at.desc())
    )
    return result.scalars().all()


@router.get("/projects/{project_id}/graph")
async def get_knowledge_graph(project_id: UUID, db: AsyncSession = Depends(get_db)):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    return await graph_service.get_graph(db, project_id)


@router.get("/ai-governance", response_model=AIGovernanceResponse)
async def get_governance(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AIGovernanceConfig).limit(1))
    config = result.scalar_one_or_none()
    if not config:
        config = AIGovernanceConfig()
        db.add(config)
        await db.commit()
        await db.refresh(config)
    return config


@router.put("/ai-governance", response_model=AIGovernanceResponse)
async def update_governance(data: AIGovernanceUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AIGovernanceConfig).limit(1))
    config = result.scalar_one_or_none()
    if not config:
        config = AIGovernanceConfig()
        db.add(config)

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(config, field, value)

    await db.commit()
    await db.refresh(config)
    return config
