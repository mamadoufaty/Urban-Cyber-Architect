"""OpenAI provider — ready for real API integration."""

import httpx

from app.ai.interfaces import ProjectContext, ProviderType
from app.ai.providers.base import BaseLLMProvider
from app.config import settings


class OpenAIProvider(BaseLLMProvider):
    def __init__(self, model_id: str = "gpt-4o"):
        super().__init__(model_id, ProviderType.OPENAI)

    def is_available(self) -> bool:
        return bool(settings.openai_api_key)

    async def _generate(self, prompt: str, context: ProjectContext) -> str:
        if not self.is_available():
            raise RuntimeError("OpenAI API key not configured")

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.openai_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model_id,
                    "messages": [
                        {"role": "system", "content": "Tu es un expert en architecture d'entreprise et cybersécurité."},
                        {"role": "user", "content": prompt},
                    ],
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
