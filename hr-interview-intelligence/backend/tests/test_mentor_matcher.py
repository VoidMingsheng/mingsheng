from app.services.mentor_matcher import rank_mentors


def test_rank_mentors_prioritizes_same_department_and_availability() -> None:
    employees = [
        {
            "employee_id": "a",
            "name": "A",
            "department": "Sales",
            "mbti": "ENFJ",
            "mentoring_score": 5,
            "availability": 1,
        },
        {
            "employee_id": "b",
            "name": "B",
            "department": "Software Engineering",
            "mbti": "INTJ",
            "mentoring_score": 4.5,
            "availability": 0.8,
        },
    ]

    ranked = rank_mentors("INTJ", "Software Engineering", employees)

    assert ranked[0]["employee_id"] == "b"
