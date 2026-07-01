"""Ollama local provider — ready for real API integration."""

import httpx

from app.ai.interfaces import ProjectContext, ProviderType
from app.ai.providers.base import BaseLLMProvider
from app.config import settings


class OllamaProvider(BaseLLMProvider):
    def __init__(self, model_id: str = "llama3.2"):
        super().__init__(model_id, ProviderType.OLLAMA)

    def is_available(self) -> bool:
        return True

    async def _generate(self, prompt: str, context: ProjectContext) -> str:
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                f"{settings.ollama_base_url}/api/generate",
                json={
                    "model": self.model_id,
                    "prompt": prompt,
                    "stream": False,
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["response"]
