from dataclasses import asdict, dataclass
from typing import Mapping


@dataclass(frozen=True)
class RubricCategory:
    key: str
    label: str
    max_score: float


@dataclass(frozen=True)
class CategoryScore:
    key: str
    label: str
    score: float
    max_score: float
    evidence: list[str]


RUBRIC = [
    RubricCategory("technical_competency", "Technical Competency", 25),
    RubricCategory("experience_alignment", "Experience Alignment", 15),
    RubricCategory("communication_skills", "Communication Skills", 15),
    RubricCategory("problem_solving_ability", "Problem Solving Ability", 10),
    RubricCategory("cultural_fit", "Cultural Fit", 10),
    RubricCategory("personality_compatibility", "Personality Compatibility", 10),
    RubricCategory("learning_potential", "Learning Potential", 5),
    RubricCategory("confidence_professionalism", "Confidence And Professionalism", 5),
    RubricCategory("leadership_initiative", "Leadership And Initiative", 5),
]

CATEGORY_LOOKUP = {category.key: category for category in RUBRIC}
CRITICAL_MINIMUMS = {
    "technical_competency": 15,
    "communication_skills": 8,
}


def clamp_score(value: float, max_score: float) -> float:
    return round(max(0, min(float(value), max_score)), 2)


def recommendation_for_score(total_score: float) -> str:
    if total_score >= 85:
        return "Strong Hire"
    if total_score >= 75:
        return "Hire"
    if total_score >= 65:
        return "Consider"
    if total_score >= 50:
        return "Weak Fit"
    return "Reject"


def normalize_category_scores(
    scores: Mapping[str, float],
    evidence: Mapping[str, list[str]] | None = None,
) -> list[CategoryScore]:
    evidence = evidence or {}
    normalized: list[CategoryScore] = []

    for category in RUBRIC:
        normalized.append(
            CategoryScore(
                key=category.key,
                label=category.label,
                score=clamp_score(scores.get(category.key, 0), category.max_score),
                max_score=category.max_score,
                evidence=evidence.get(category.key, []),
            )
        )

    return normalized


def missing_critical_minimums(category_scores: list[CategoryScore]) -> list[str]:
    by_key = {score.key: score.score for score in category_scores}
    missing = []

    for key, minimum in CRITICAL_MINIMUMS.items():
        if by_key.get(key, 0) < minimum:
            missing.append(f"{CATEGORY_LOOKUP[key].label} below minimum {minimum}")

    return missing


def score_candidate(
    scores: Mapping[str, float],
    evidence: Mapping[str, list[str]] | None = None,
    strengths: list[str] | None = None,
    weaknesses: list[str] | None = None,
) -> dict:
    category_scores = normalize_category_scores(scores, evidence)
    total_score = round(sum(item.score for item in category_scores), 2)
    critical_failures = missing_critical_minimums(category_scores)
    recommendation = recommendation_for_score(total_score)

    if critical_failures and recommendation in {"Strong Hire", "Hire"}:
        recommendation = "Consider"

    return {
        "total_score": total_score,
        "recommendation": recommendation,
        "critical_minimums_passed": not critical_failures,
        "critical_minimum_failures": critical_failures,
        "category_scores": [asdict(item) for item in category_scores],
        "strengths": strengths or [],
        "weaknesses": weaknesses or [],
        "human_review_required": True,
    }
