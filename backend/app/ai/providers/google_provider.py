"""Google Gemini provider — ready for real API integration."""

import httpx

from app.ai.interfaces import ProjectContext, ProviderType
from app.ai.providers.base import BaseLLMProvider
from app.config import settings


class GoogleProvider(BaseLLMProvider):
    def __init__(self, model_id: str = "gemini-2.0-flash"):
        super().__init__(model_id, ProviderType.GOOGLE)

    def is_available(self) -> bool:
        return bool(settings.google_api_key)

    async def _generate(self, prompt: str, context: ProjectContext) -> str:
        if not self.is_available():
            raise RuntimeError("Google API key not configured")

        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model_id}:generateContent?key={settings.google_api_key}"
        )
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                url,
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "systemInstruction": {
                        "parts": [{"text": "Tu es un expert en architecture d'entreprise et cybersécurité."}]
                    },
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]
