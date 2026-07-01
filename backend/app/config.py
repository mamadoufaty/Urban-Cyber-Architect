from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Urban Cyber Architect"
    debug: bool = False
  # SQLite par défaut (dev local sans Docker). PostgreSQL via DATABASE_URL.
    database_url: str = "sqlite+aiosqlite:///./urban_cyber_architect.db"
    knowledge_base_path: str = str(_PROJECT_ROOT / "knowledge-base")

    # Provider API keys (optional in V1 — mocks used when absent)
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    google_api_key: str | None = None
    azure_openai_api_key: str | None = None
    azure_openai_endpoint: str | None = None
    ollama_base_url: str = "http://localhost:11434"

    default_models: list[str] = ["mock-gpt", "mock-claude", "mock-gemini"]
    default_judge: str = "mock-judge"


settings = Settings()
