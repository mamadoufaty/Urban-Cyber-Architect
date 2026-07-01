import time
from abc import abstractmethod

from app.ai.interfaces import LLMProvider, ModelResponse, ProjectContext, ProviderType


class BaseLLMProvider(LLMProvider):
    """Base class with shared timing and response formatting."""

    def __init__(self, model_id: str, provider_type: ProviderType):
        self.model_id = model_id
        self.provider_type = provider_type

    async def complete(self, prompt: str, context: ProjectContext) -> ModelResponse:
        start = time.perf_counter()
        content = await self._generate(prompt, context)
        latency_ms = int((time.perf_counter() - start) * 1000)
        return ModelResponse(
            provider=self.provider_type.value,
            model_id=self.model_id,
            content=content,
            latency_ms=latency_ms,
        )

    @abstractmethod
    async def _generate(self, prompt: str, context: ProjectContext) -> str:
        ...
