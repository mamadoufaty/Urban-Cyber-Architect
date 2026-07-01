"""Quick pipeline test without database."""

import asyncio
import json

from app.ai.orchestrator import AIOrchestrator


async def main():
    orchestrator = AIOrchestrator()
    project_data = {
        "id": "test-001",
        "organization": {"name": "Ville de Lyon", "sector": "smart_city", "size": "Grande collectivité", "country": "France"},
        "referentials": ["RGPD", "NIS2", "ISO 27001", "IEC 62443"],
        "objectives": ["Sécuriser les services numériques", "Conformité NIS2"],
        "urbanism": {
            "metiers": ["Transport", "Eau", "Energie"],
            "processus": ["Supervision SCADA", "Gestion incidents citoyens"],
        },
    }

    result = await orchestrator.run_full_pipeline(project_data)
    print("=== Urban Cyber Architect — Pipeline Test ===\n")
    print(f"Models: {result['models']}")
    print(f"Judge score: {result['judge']['total_score']}/100")
    print(f"Summary: {result['judge']['summary']}\n")
    print("Criteria scores:")
    for c in result["judge"]["criteria_scores"]:
        print(f"  - {c['name']}: {c['score']} (weight {c['weight']})")
    print(f"\nStatus: {result['status']}")


if __name__ == "__main__":
    asyncio.run(main())
