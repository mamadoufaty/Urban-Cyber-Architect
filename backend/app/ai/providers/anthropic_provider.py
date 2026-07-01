"""Anthropic Claude provider — ready for real API integration."""

import httpx

from app.ai.interfaces import ProjectContext, ProviderType
from app.ai.providers.base import BaseLLMProvider
from app.config import settings


class AnthropicProvider(BaseLLMProvider):
    def __init__(self, model_id: str = "claude-sonnet-4-20250514"):
        super().__init__(model_id, ProviderType.ANTHROPIC)

    def is_available(self) -> bool:
        return bool(settings.anthropic_api_key)

    async def _generate(self, prompt: str, context: ProjectContext) -> str:
        if not self.is_available():
            raise RuntimeError("Anthropic API key not configured")

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": settings.anthropic_api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model_id,
                    "max_tokens": 4096,
                    "system": "Tu es un expert en architecture d'entreprise et cybersécurité.",
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["content"][0]["text"]
