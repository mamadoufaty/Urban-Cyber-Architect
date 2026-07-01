"""Mock LLM providers for V1 development and testing."""

import json
from app.ai.interfaces import ProjectContext, ProviderType
from app.ai.providers.base import BaseLLMProvider


class MockGPTProvider(BaseLLMProvider):
    def __init__(self):
        super().__init__("mock-gpt", ProviderType.MOCK)

    def is_available(self) -> bool:
        return True

    async def _generate(self, prompt: str, context: ProjectContext) -> str:
        org = context.organization.get("name", "Organisation")
        sector = context.organization.get("sector", "générique")
        refs = ", ".join(context.referentials) or "aucun"
        return json.dumps(
            {
                "source": "mock-gpt",
                "processus_critiques": [
                    f"Gestion des accès - {org}",
                    "Traitement des données personnelles",
                    "Continuité de service métier",
                ],
                "actifs_critiques": ["SI métier", "Base de données clients", "Infrastructure réseau"],
                "scenarios_ebios": [
                    {
                        "nom": "Compromission compte privilégié",
                        "gravite": "élevée",
                        "vraisemblance": "moyenne",
                    },
                    {
                        "nom": "Ransomware sur postes utilisateurs",
                        "gravite": "critique",
                        "vraisemblance": "élevée",
                    },
                ],
                "exigences_reglementaires": [f"Conformité {r}" for r in context.referentials[:3]],
                "architecture_cible": {
                    "zero_trust": "Segmentation réseau et MFA obligatoire",
                    "iam": "SSO fédéré avec PAM",
                    "siem_soc": "Centralisation des logs et SOC mutualisé",
                    "pra_pca": "RTO 4h / RPO 1h pour processus critiques",
                },
                "sector": sector,
                "referentials": refs,
            },
            ensure_ascii=False,
            indent=2,
        )


class MockClaudeProvider(BaseLLMProvider):
    def __init__(self):
        super().__init__("mock-claude", ProviderType.MOCK)

    def is_available(self) -> bool:
        return True

    async def _generate(self, prompt: str, context: ProjectContext) -> str:
        return json.dumps(
            {
                "source": "mock-claude",
                "processus_critiques": [
                    "Onboarding / offboarding collaborateurs",
                    "Gestion des incidents de sécurité",
                    "Supervision OT/IT",
                ],
                "actifs_critiques": ["Active Directory", "ERP", "Systèmes SCADA/OT"],
                "scenarios_ebios": [
                    {
                        "nom": "Exfiltration de données sensibles",
                        "gravite": "critique",
                        "traitements": ["DLP", "Chiffrement au repos"],
                    },
                    {
                        "nom": "Indisponibilité service critique",
                        "gravite": "élevée",
                        "traitements": ["PRA", "Redondance géographique"],
                    },
                ],
                "exigences_reglementaires": [
                    "Cartographie des traitements RGPD",
                    "Analyse d'impact NIS2",
                    "Politique de gestion des risques ISO 27005",
                ],
                "architecture_cible": {
                    "ot_it": "DMZ industrielle avec bastion d'accès",
                    "zero_trust": "Micro-segmentation et contrôle d'accès contextuel",
                    "iam": "RBAC + revue trimestrielle des droits",
                    "siem": "Corrélation multi-sources OT/IT",
                },
            },
            ensure_ascii=False,
            indent=2,
        )


class MockGeminiProvider(BaseLLMProvider):
    def __init__(self):
        super().__init__("mock-gemini", ProviderType.MOCK)

    def is_available(self) -> bool:
        return True

    async def _generate(self, prompt: str, context: ProjectContext) -> str:
        objectives = context.objectives or ["Sécuriser le SI", "Conformité réglementaire"]
        return json.dumps(
            {
                "source": "mock-gemini",
                "objectifs_pris_en_compte": objectives,
                "processus_critiques": [
                    "Production / exploitation",
                    "Relation client",
                    "Gouvernance des données",
                ],
                "actifs_critiques": ["Applications SaaS", "Cloud privé", "Téléphonie IP"],
                "scenarios_ebios": [
                    {
                        "nom": "Attaque supply chain",
                        "gravite": "élevée",
                        "mesures": ["SBOM", "Revue fournisseurs"],
                    }
                ],
                "exigences_reglementaires": context.referentials,
                "architecture_cible": {
                    "soc": "SOC 24/7 avec playbooks automatisés",
                    "dora": "Résilience opérationnelle numérique",
                    "architecture": "Cloud hybride avec landing zone sécurisée",
                },
            },
            ensure_ascii=False,
            indent=2,
        )
