from app.services.scoring import recommendation_for_score, score_candidate


def test_recommendation_thresholds() -> None:
    assert recommendation_for_score(90) == "Strong Hire"
    assert recommendation_for_score(80) == "Hire"
    assert recommendation_for_score(70) == "Consider"
    assert recommendation_for_score(55) == "Weak Fit"
    assert recommendation_for_score(40) == "Reject"


def test_critical_minimums_downgrade_hire_recommendation() -> None:
    result = score_candidate(
        {
            "technical_competency": 14,
            "experience_alignment": 15,
            "communication_skills": 15,
            "problem_solving_ability": 10,
            "cultural_fit": 10,
            "personality_compatibility": 10,
            "learning_potential": 5,
            "confidence_professionalism": 5,
            "leadership_initiative": 5,
        }
    )

    assert result["total_score"] == 89
    assert result["recommendation"] == "Consider"
    assert result["critical_minimums_passed"] is False
