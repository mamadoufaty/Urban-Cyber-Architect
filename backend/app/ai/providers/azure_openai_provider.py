"""Azure OpenAI provider — ready for real API integration."""

import httpx

from app.ai.interfaces import ProjectContext, ProviderType
from app.ai.providers.base import BaseLLMProvider
from app.config import settings


class AzureOpenAIProvider(BaseLLMProvider):
    def __init__(self, model_id: str = "gpt-4o", deployment: str = "gpt-4o"):
        super().__init__(model_id, ProviderType.AZURE_OPENAI)
        self.deployment = deployment

    def is_available(self) -> bool:
        return bool(settings.azure_openai_api_key and settings.azure_openai_endpoint)

    async def _generate(self, prompt: str, context: ProjectContext) -> str:
        if not self.is_available():
            raise RuntimeError("Azure OpenAI not configured")

        url = (
            f"{settings.azure_openai_endpoint.rstrip('/')}"
            f"/openai/deployments/{self.deployment}/chat/completions?api-version=2024-02-15-preview"
        )
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                url,
                headers={
                    "api-key": settings.azure_openai_api_key,
                    "Content-Type": "application/json",
                },
                json={
                    "messages": [
                        {"role": "system", "content": "Tu es un expert en architecture d'entreprise et cybersécurité."},
                        {"role": "user", "content": prompt},
                    ],
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
