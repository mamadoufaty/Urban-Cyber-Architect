"""Project Context Builder — assembles organization, referentials, urbanism, and knowledge base."""

from pathlib import Path
from typing import Any

import yaml

from app.ai.interfaces import ProjectContext
from app.config import settings

KNOWLEDGE_BASE_ROOT = Path(settings.knowledge_base_path)

DEFAULT_REFERENTIALS = [
    "RGPD", "RGS", "NIS2", "LPM", "ISO 27001", "ISO 27005",
    "IEC 62443", "DORA", "HDS", "NIST",
]

URBANISM_LAYERS = ["objectifs", "metiers", "processus", "fonctionnel", "applicatif", "technique"]


class ContextBuilder:
    def build(self, project_data: dict[str, Any]) -> ProjectContext:
        org = project_data.get("organization", {})
        sector = org.get("sector", "generic")
        kb = self._load_knowledge_base(sector)

        urbanism = {}
        for layer in URBANISM_LAYERS:
            urbanism[layer] = project_data.get(layer, project_data.get("urbanism", {}).get(layer, []))

        return ProjectContext(
            project_id=str(project_data.get("id", "")),
            organization=org,
            referentials=project_data.get("referentials", DEFAULT_REFERENTIALS),
            urbanism=urbanism,
            knowledge_base=kb,
            objectives=project_data.get("objectives", urbanism.get("objectifs", [])),
            task=project_data.get("task", "architecture_analysis"),
        )

    def _load_knowledge_base(self, sector: str) -> dict[str, Any]:
        sector_map = {
            "smart_city": "smart-city",
            "smart city": "smart-city",
            "banque": "banque",
            "banking": "banque",
            "sante": "sante",
            "health": "sante",
            "industrie": "industrie",
            "industry": "industrie",
        }
        folder = sector_map.get(sector.lower().replace(" ", "_"), sector.lower())
        path = KNOWLEDGE_BASE_ROOT / folder / "index.yaml"
        if path.exists():
            with open(path, encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        return {}
