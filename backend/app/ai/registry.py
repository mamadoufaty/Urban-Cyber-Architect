"""Provider registry — maps model IDs to provider instances without coupling the rest of the app."""

from app.ai.interfaces import JudgeProvider, LLMProvider
from app.ai.providers.anthropic_provider import AnthropicProvider
from app.ai.providers.azure_openai_provider import AzureOpenAIProvider
from app.ai.providers.google_provider import GoogleProvider
from app.ai.providers.mock import MockClaudeProvider, MockGPTProvider, MockGeminiProvider
from app.ai.providers.mock_judge import MockJudgeProvider
from app.ai.providers.ollama_provider import OllamaProvider
from app.ai.providers.openai_provider import OpenAIProvider

_LLM_FACTORIES: dict[str, callable] = {
    "mock-gpt": lambda: MockGPTProvider(),
    "mock-claude": lambda: MockClaudeProvider(),
    "mock-gemini": lambda: MockGeminiProvider(),
    "gpt-4o": lambda: OpenAIProvider("gpt-4o"),
    "claude-sonnet-4-20250514": lambda: AnthropicProvider("claude-sonnet-4-20250514"),
    "gemini-2.0-flash": lambda: GoogleProvider("gemini-2.0-flash"),
    "llama3.2": lambda: OllamaProvider("llama3.2"),
    "azure-gpt-4o": lambda: AzureOpenAIProvider("gpt-4o", "gpt-4o"),
}

_JUDGE_FACTORIES: dict[str, callable] = {
    "mock-judge": lambda: MockJudgeProvider(),
}


def get_llm_provider(model_id: str) -> LLMProvider:
    factory = _LLM_FACTORIES.get(model_id)
    if factory is None:
        raise ValueError(f"Unknown model: {model_id}. Available: {list(_LLM_FACTORIES.keys())}")
    return factory()


def get_judge_provider(judge_id: str) -> JudgeProvider:
    factory = _JUDGE_FACTORIES.get(judge_id)
    if factory is None:
        raise ValueError(f"Unknown judge: {judge_id}")
    return factory()


def list_available_models() -> list[dict]:
    return [
        {
            "model_id": model_id,
            "provider": factory().provider_type.value,
            "available": factory().is_available(),
        }
        for model_id, factory in _LLM_FACTORIES.items()
    ]


def list_available_judges() -> list[str]:
    return list(_JUDGE_FACTORIES.keys())
