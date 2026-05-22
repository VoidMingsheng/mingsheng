from app.services.coworker_matcher import rank_coworkers


def test_rank_coworkers_prioritizes_same_department_and_availability() -> None:
    employees = [
        {
            "employee_id": "a",
            "name": "A",
            "department": "Sales",
            "mbti": "ENFJ",
            "onboarding_score": 5,
            "availability": 1,
        },
        {
            "employee_id": "b",
            "name": "B",
            "department": "Software Engineering",
            "mbti": "INTJ",
            "onboarding_score": 4.5,
            "availability": 0.8,
        },
    ]

    ranked = rank_coworkers("INTJ", "Software Engineering", employees)

    assert ranked[0]["employee_id"] == "b"
