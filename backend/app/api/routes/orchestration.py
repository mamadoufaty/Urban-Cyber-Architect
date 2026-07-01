from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.interfaces import JudgeCriteria
from app.ai.orchestrator import AIOrchestrator
from app.database import get_db
from app.models.entities import AIGovernanceConfig, OrchestrationRun, Project
from app.schemas.api import OrchestrateRequest

router = APIRouter(prefix="/projects", tags=["orchestration"])


async def _get_governance(db: AsyncSession) -> AIGovernanceConfig:
    from sqlalchemy import select

    result = await db.execute(select(AIGovernanceConfig).limit(1))
    config = result.scalar_one_or_none()
    if not config:
        config = AIGovernanceConfig()
        db.add(config)
        await db.commit()
        await db.refresh(config)
    return config


@router.post("/{project_id}/orchestrate")
async def orchestrate(
    project_id: UUID,
    request: OrchestrateRequest,
    db: AsyncSession = Depends(get_db),
):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "Project not found")

    governance = await _get_governance(db)
    criteria = JudgeCriteria(
        urbanisme_weight=governance.urbanisme_weight,
        conformite_weight=governance.conformite_weight,
        ebios_weight=governance.ebios_weight,
        architecture_weight=governance.architecture_weight,
    )

    orchestrator = AIOrchestrator(
        model_ids=request.models or governance.models,
        judge_id=governance.judge_id,
        criteria=criteria,
    )

    project_data = {
        "id": str(project.id),
        "organization": project.organization,
        "referentials": project.referentials,
        "urbanism": project.urbanism,
        "objectives": project.objectives,
    }

    result = await orchestrator.run_full_pipeline(project_data, request.template_name)

    run = OrchestrationRun(
        project_id=project.id,
        models=result["models"],
        prompt=result["prompt"],
        template_name=result["template"],
        responses=result["responses"],
        judge_result=result["judge"],
        status="pending_human_validation",
    )
    db.add(run)
    project.status = "orchestrated"
    await db.commit()
    await db.refresh(run)

    result["orchestration_id"] = str(run.id)
    return result
