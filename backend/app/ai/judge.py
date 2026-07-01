"""Judge Engine — scores responses on urbanisme, conformité, EBIOS, and architecture criteria."""

import json
import re
from typing import Any

from app.ai.interfaces import CriterionScore, JudgeCriteria, JudgeResult, ModelResponse, ProjectContext

_KEYWORDS = {
    "urbanisme": [
        "processus", "métier", "metier", "objectif", "fonctionnel", "applicatif", "technique",
    ],
    "conformite": [
        "rgpd", "rgs", "nis2", "lpm", "iso", "iec", "dora", "hds", "nist", "réglementaire", "reglementaire",
    ],
    "ebios": [
        "ebios", "scénario", "scenario", "risque", "menace", "gravité", "gravite", "traitement", "mesure",
    ],
    "architecture": [
        "zero trust", "ot", "it", "iam", "siem", "soc", "pra", "pca", "architecture", "segmentation",
    ],
}


class JudgeEngine:
    def __init__(self, criteria: JudgeCriteria | None = None):
        self.criteria = criteria or JudgeCriteria()

    def evaluate(self, responses: list[ModelResponse], context: ProjectContext) -> JudgeResult:
        if not responses:
            raise ValueError("No responses to evaluate")

        all_scores: list[float] = []
        all_criteria: list[list[CriterionScore]] = []

        for response in responses:
            parsed = self._parse_content(response.content)
            criteria_scores = self._score_response(parsed, response.content, context)
            weighted = sum(c.score * c.weight for c in criteria_scores)
            all_scores.append(round(weighted, 2))
            all_criteria.append(criteria_scores)

        best_index = all_scores.index(max(all_scores))
        best_criteria = all_criteria[best_index]

        return JudgeResult(
            selected_response_index=best_index,
            total_score=all_scores[best_index],
            criteria_scores=best_criteria,
            summary=self._build_summary(responses, all_scores, best_index),
            all_scores=all_scores,
        )

    def _parse_content(self, content: str) -> dict[str, Any]:
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return {"raw_text": content}

    def _score_response(
        self, parsed: dict[str, Any], raw: str, context: ProjectContext
    ) -> list[CriterionScore]:
        text = raw.lower()
        weights = self.criteria.as_dict()

        scores = []
        for criterion, weight in weights.items():
            keywords = _KEYWORDS[criterion]
            matches = sum(1 for kw in keywords if kw in text)
            keyword_score = min(100, matches * 12)

            structure_score = self._structure_score(parsed, criterion)
            combined = round(keyword_score * 0.4 + structure_score * 0.6, 2)

            strengths, weaknesses, recommendations = self._feedback(parsed, criterion, combined)
            scores.append(
                CriterionScore(
                    name=criterion,
                    score=combined,
                    weight=weight,
                    strengths=strengths,
                    weaknesses=weaknesses,
                    recommendations=recommendations,
                )
            )

        return scores

    def _structure_score(self, parsed: dict[str, Any], criterion: str) -> float:
        if "raw_text" in parsed:
            return 40.0

        checks = {
            "urbanisme": ["processus_critiques", "actifs_critiques"],
            "conformite": ["exigences_reglementaires"],
            "ebios": ["scenarios_ebios"],
            "architecture": ["architecture_cible"],
        }
        expected = checks.get(criterion, [])
        if not expected:
            return 50.0

        found = sum(1 for key in expected if key in parsed and parsed[key])
        return min(100, (found / len(expected)) * 100)

    def _feedback(
        self, parsed: dict[str, Any], criterion: str, score: float
    ) -> tuple[list[str], list[str], list[str]]:
        strengths: list[str] = []
        weaknesses: list[str] = []
        recommendations: list[str] = []

        if score >= 70:
            strengths.append(f"Bonne couverture du critère {criterion}")
        elif score >= 40:
            weaknesses.append(f"Couverture partielle du critère {criterion}")
            recommendations.append(f"Enrichir les éléments liés à {criterion}")
        else:
            weaknesses.append(f"Couverture insuffisante du critère {criterion}")
            recommendations.append(f"Revoir en profondeur le critère {criterion}")

        if criterion == "ebios" and "scenarios_ebios" in parsed:
            scenarios = parsed["scenarios_ebios"]
            if isinstance(scenarios, list) and len(scenarios) >= 2:
                strengths.append(f"{len(scenarios)} scénarios EBIOS identifiés")
            else:
                recommendations.append("Ajouter plus de scénarios EBIOS avec gravité et traitements")

        return strengths, weaknesses, recommendations

    def _build_summary(
        self, responses: list[ModelResponse], scores: list[float], best_index: int
    ) -> str:
        best = responses[best_index]
        return (
            f"Meilleure réponse : {best.model_id} (score {scores[best_index]}/100). "
            f"Évalué sur {len(responses)} modèles. "
            f"Sélection basée sur cohérence métier, conformité, EBIOS et architecture — "
            f"pas uniquement sur la qualité rédactionnelle."
        )
