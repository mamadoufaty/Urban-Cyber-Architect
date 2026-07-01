"""AI Orchestrator — coordinates the full multi-LLM pipeline."""

import asyncio
import uuid
from dataclasses import asdict
from datetime import datetime
from typing import Any

from app.ai.interfaces import JudgeCriteria, ModelResponse, ProjectContext
from app.ai.registry import get_judge_provider, get_llm_provider
from app.context.builder import ContextBuilder
from app.prompts.templates import PromptTemplateManager


class AIOrchestrator:
    def __init__(
        self,
        model_ids: list[str] | None = None,
        judge_id: str = "mock-judge",
        criteria: JudgeCriteria | None = None,
    ):
        self.model_ids = model_ids or ["mock-gpt", "mock-claude", "mock-gemini"]
        self.judge_id = judge_id
        self.criteria = criteria or JudgeCriteria()
        self.prompt_manager = PromptTemplateManager()
        self.context_builder = ContextBuilder()

    def build_context(self, project_data: dict[str, Any]) -> ProjectContext:
        return self.context_builder.build(project_data)

    def generate_prompt(self, context: ProjectContext, template_name: str = "architecture_analysis") -> str:
        return self.prompt_manager.render(template_name, context)

    async def launch_models(self, prompt: str, context: ProjectContext) -> list[ModelResponse]:
        tasks = []
        for model_id in self.model_ids:
            provider = get_llm_provider(model_id)
            tasks.append(provider.complete(prompt, context))
        results = await asyncio.gather(*tasks, return_exceptions=True)

        responses: list[ModelResponse] = []
        for model_id, result in zip(self.model_ids, results):
            if isinstance(result, Exception):
                responses.append(
                    ModelResponse(
                        provider="error",
                        model_id=model_id,
                        content=f'{{"error": "{str(result)}"}}',
                        metadata={"error": True},
                    )
                )
            else:
                responses.append(result)
        return responses

    def collect_responses(self, responses: list[ModelResponse]) -> list[dict[str, Any]]:
        return [asdict(r) for r in responses]

    async def launch_judge(
        self, responses: list[ModelResponse], context: ProjectContext
    ) -> dict[str, Any]:
        judge = get_judge_provider(self.judge_id)
        result = await judge.evaluate(responses, context, self.criteria)
        return asdict(result)

    def save_decision(self, orchestration_result: dict[str, Any]) -> dict[str, Any]:
        orchestration_result["decision_id"] = str(uuid.uuid4())
        orchestration_result["saved_at"] = datetime.utcnow().isoformat()
        orchestration_result["status"] = "pending_human_validation"
        return orchestration_result

    async def run_full_pipeline(
        self, project_data: dict[str, Any], template_name: str = "architecture_analysis"
    ) -> dict[str, Any]:
        context = self.build_context(project_data)
        prompt = self.generate_prompt(context, template_name)
        responses = await self.launch_models(prompt, context)
        judge_result = await self.launch_judge(responses, context)

        return self.save_decision(
            {
                "context": asdict(context),
                "prompt": prompt,
                "template": template_name,
                "models": self.model_ids,
                "responses": self.collect_responses(responses),
                "judge": judge_result,
            }
        )
