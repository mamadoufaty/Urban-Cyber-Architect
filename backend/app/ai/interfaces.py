from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class ProviderType(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    OLLAMA = "ollama"
    AZURE_OPENAI = "azure_openai"
    MOCK = "mock"


@dataclass
class ProjectContext:
    project_id: str
    organization: dict[str, Any]
    referentials: list[str]
    urbanism: dict[str, Any]
    knowledge_base: dict[str, Any] = field(default_factory=dict)
    objectives: list[str] = field(default_factory=list)
    task: str = ""


@dataclass
class ModelResponse:
    provider: str
    model_id: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    latency_ms: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class CriterionScore:
    name: str
    score: float
    weight: float
    strengths: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)


@dataclass
class JudgeResult:
    selected_response_index: int
    total_score: float
    criteria_scores: list[CriterionScore]
    summary: str
    all_scores: list[float] = field(default_factory=list)


@dataclass
class JudgeCriteria:
    urbanisme_weight: float = 0.20
    conformite_weight: float = 0.25
    ebios_weight: float = 0.30
    architecture_weight: float = 0.25

    def as_dict(self) -> dict[str, float]:
        return {
            "urbanisme": self.urbanisme_weight,
            "conformite": self.conformite_weight,
            "ebios": self.ebios_weight,
            "architecture": self.architecture_weight,
        }


class LLMProvider(ABC):
    """Abstract interface for all LLM providers."""

    provider_type: ProviderType
    model_id: str

    @abstractmethod
    async def complete(self, prompt: str, context: ProjectContext) -> ModelResponse:
        """Generate a completion from the given prompt and project context."""
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if the provider is configured and reachable."""
        ...


class JudgeProvider(ABC):
    """Abstract interface for the judge engine."""

    @abstractmethod
    async def evaluate(
        self,
        responses: list[ModelResponse],
        context: ProjectContext,
        criteria: JudgeCriteria,
    ) -> JudgeResult:
        """Compare and score multiple model responses."""
        ...
