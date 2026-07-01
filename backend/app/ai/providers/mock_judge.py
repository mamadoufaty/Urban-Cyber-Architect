from app.ai.interfaces import JudgeCriteria, JudgeProvider, JudgeResult, ModelResponse, ProjectContext
from app.ai.judge import JudgeEngine


class MockJudgeProvider(JudgeProvider):
    """Delegates to the rule-based JudgeEngine for V1."""

    async def evaluate(
        self,
        responses: list[ModelResponse],
        context: ProjectContext,
        criteria: JudgeCriteria,
    ) -> JudgeResult:
        engine = JudgeEngine(criteria)
        return engine.evaluate(responses, context)
