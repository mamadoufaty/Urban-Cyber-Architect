"""Calcul des risques initial et résiduel — atelier 5."""

from __future__ import annotations

LEVEL_SCORE = {"Faible": 1, "Modérée": 2, "Élevée": 3, "Critique": 4}
SCORE_LABEL = {1: "Faible", 2: "Modérée", 3: "Élevée", 4: "Critique", 5: "Critique"}


def risk_score(severity: str, likelihood: str) -> int:
    return LEVEL_SCORE.get(severity, 2) * LEVEL_SCORE.get(likelihood, 2)


def score_to_label(score: int) -> str:
    if score <= 2:
        return "Faible"
    if score <= 4:
        return "Modérée"
    if score <= 8:
        return "Élevée"
    return "Critique"


def compute_initial_risk(severity: str, likelihood: str, criticality: str) -> dict:
    score = risk_score(severity, likelihood)
    return {
        "initial_risk_score": score,
        "initial_risk_label": criticality or score_to_label(score),
        "severity": severity,
        "likelihood": likelihood,
        "criticality": criticality,
    }


def compute_residual_risk(
    initial_score: int,
    retained_measure_count: int,
    treatment_decision: str,
) -> dict:
    if treatment_decision == "Accepter":
        residual = initial_score
    elif treatment_decision == "Éviter":
        residual = 1
    elif treatment_decision == "Transférer":
        residual = max(1, initial_score - 2)
    else:
        reduction = min(retained_measure_count * 2, initial_score - 1)
        residual = max(1, initial_score - reduction)
    return {
        "residual_risk_score": residual,
        "residual_risk_label": score_to_label(residual),
        "retained_measure_count": retained_measure_count,
    }
