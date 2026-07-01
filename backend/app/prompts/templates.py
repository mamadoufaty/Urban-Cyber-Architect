"""Prompt Studio — versioned prompt templates."""

from dataclasses import dataclass, field
from datetime import datetime

from app.ai.interfaces import ProjectContext

DEFAULT_TEMPLATES: dict[str, dict] = {
    "architecture_analysis": {
        "version": "1.0.0",
        "description": "Analyse architecture et cybersécurité complète",
        "template": """# Mission — Urban Cyber Architect

Tu es un expert en architecture d'entreprise et cybersécurité.

## Organisation
- Nom : {org_name}
- Secteur : {org_sector}
- Taille : {org_size}
- Pays : {org_country}

## Référentiels applicables
{referentials}

## Couches Urbanisme
- Objectifs : {objectifs}
- Métiers : {metiers}
- Processus : {processus}
- Fonctionnel : {fonctionnel}
- Applicatif : {applicatif}
- Technique : {technique}

## Contexte Knowledge Base
{knowledge_base}

## Ta mission
Identifie et structure ta réponse en JSON avec les clés suivantes :
1. `processus_critiques` — liste des processus critiques
2. `actifs_critiques` — liste des actifs critiques
3. `scenarios_ebios` — scénarios de risque (nom, gravité, vraisemblance, traitements)
4. `exigences_reglementaires` — exigences liées aux référentiels
5. `architecture_cible` — recommandations (Zero Trust, OT/IT, IAM, SIEM, SOC, PRA/PCA)

Réponds uniquement en JSON valide.""",
    },
    "ebios_analysis": {
        "version": "1.0.0",
        "description": "Analyse EBIOS RM focalisée",
        "template": """# Analyse EBIOS RM

Organisation : {org_name} ({org_sector})
Référentiels : {referentials}

Processus : {processus}
Actifs connus : {knowledge_base}

Produis une analyse EBIOS structurée en JSON :
- scenarios_ebios (avec sources de risque, événements redoutés, mesures)
- risques_prioritaires
- plan_traitement""",
    },
}


@dataclass
class PromptVersion:
    name: str
    version: str
    description: str
    template: str
    created_at: datetime = field(default_factory=datetime.utcnow)


class PromptTemplateManager:
    def __init__(self):
        self._templates: dict[str, PromptVersion] = {}
        for name, data in DEFAULT_TEMPLATES.items():
            self._templates[name] = PromptVersion(
                name=name,
                version=data["version"],
                description=data["description"],
                template=data["template"],
            )

    def list_templates(self) -> list[dict]:
        return [
            {
                "name": t.name,
                "version": t.version,
                "description": t.description,
                "created_at": t.created_at.isoformat(),
            }
            for t in self._templates.values()
        ]

    def get_template(self, name: str) -> PromptVersion | None:
        return self._templates.get(name)

    def render(self, name: str, context: ProjectContext) -> str:
        template = self._templates.get(name)
        if not template:
            raise ValueError(f"Template not found: {name}")

        org = context.organization
        urbanism = context.urbanism
        kb_summary = str(context.knowledge_base.get("domains", context.knowledge_base))[:500]

        return template.template.format(
            org_name=org.get("name", "N/A"),
            org_sector=org.get("sector", "N/A"),
            org_size=org.get("size", "N/A"),
            org_country=org.get("country", "France"),
            referentials="\n".join(f"- {r}" for r in context.referentials),
            objectifs=", ".join(urbanism.get("objectifs", context.objectives)) or "Non défini",
            metiers=", ".join(urbanism.get("metiers", [])) or "Non défini",
            processus=", ".join(urbanism.get("processus", [])) or "Non défini",
            fonctionnel=", ".join(urbanism.get("fonctionnel", [])) or "Non défini",
            applicatif=", ".join(urbanism.get("applicatif", [])) or "Non défini",
            technique=", ".join(urbanism.get("technique", [])) or "Non défini",
            knowledge_base=kb_summary,
        )

    def update_template(self, name: str, template: str, version: str, description: str = "") -> PromptVersion:
        pv = PromptVersion(
            name=name,
            version=version,
            description=description or self._templates.get(name, PromptVersion(name, "0", "", "")).description,
            template=template,
        )
        self._templates[name] = pv
        return pv
