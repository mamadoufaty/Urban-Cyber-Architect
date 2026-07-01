"""Human validation service."""

import json

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import HumanDecision, OrchestrationRun, Project
from app.schemas.api import HumanDecisionCreate
from app.services.knowledge_graph import KnowledgeGraphService


class ValidationService:
    def __init__(self):
        self.graph_service = KnowledgeGraphService()

    async def record_decision(
        self,
        session: AsyncSession,
        project: Project,
        data: HumanDecisionCreate,
    ) -> HumanDecision:
        decision = HumanDecision(
            project_id=project.id,
            orchestration_id=data.orchestration_id,
            action=data.action,
            selected_model=data.selected_model,
            merged_content=data.merged_content,
            modified_content=data.modified_content,
            comment=data.comment,
        )
        session.add(decision)

        if data.action in ("accept", "modify", "merge") and data.orchestration_id:
            orchestration = await session.get(OrchestrationRun, data.orchestration_id)
            if orchestration:
                orchestration.status = f"validated_{data.action}"
                content = self._extract_content(data, orchestration)
                if content:
                    await self.graph_service.build_from_decision(session, project.id, content)
                project.status = "validated"

        elif data.action == "reject" and data.orchestration_id:
            orchestration = await session.get(OrchestrationRun, data.orchestration_id)
            if orchestration:
                orchestration.status = "rejected"

        await session.commit()
        await session.refresh(decision)
        return decision

    def _extract_content(self, data: HumanDecisionCreate, orchestration: OrchestrationRun) -> dict:
        if data.modified_content:
            try:
                return json.loads(data.modified_content)
            except json.JSONDecodeError:
                return {"raw": data.modified_content}

        if data.merged_content:
            try:
                return json.loads(data.merged_content)
            except json.JSONDecodeError:
                return {"raw": data.merged_content}

        if data.selected_model:
            for response in orchestration.responses:
                if response.get("model_id") == data.selected_model:
                    try:
                        return json.loads(response.get("content", "{}"))
                    except json.JSONDecodeError:
                        return {"raw": response.get("content", "")}

        best_idx = orchestration.judge_result.get("selected_response_index", 0)
        if orchestration.responses and best_idx < len(orchestration.responses):
            try:
                return json.loads(orchestration.responses[best_idx].get("content", "{}"))
            except json.JSONDecodeError:
                return {}

        return {}
