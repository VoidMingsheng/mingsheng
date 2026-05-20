DEPARTMENT_MBTI_TENDENCIES = {
    "Sales": {"ENTP", "ENFJ", "ESFP"},
    "Software Engineering": {"INTJ", "INTP"},
    "HR": {"ENFJ", "ESFJ"},
    "Project Management": {"ENTJ", "ESTJ"},
    "Research": {"INTP", "INFJ"},
}

COMPLEMENTARY_PAIRS = {
    "INTJ": {"ENFP", "ENTP", "INTJ", "INTP"},
    "INTP": {"ENTJ", "ENTP", "INTJ", "INTP"},
    "ENTJ": {"INTP", "INTJ", "ENTJ", "ESTJ"},
    "ENFJ": {"INFP", "INFJ", "ENFJ", "ESFJ"},
    "ESFJ": {"ISFP", "ENFJ", "ESFJ"},
    "ESTJ": {"ISTJ", "ENTJ", "ESTJ"},
    "ENTP": {"INTJ", "INTP", "ENTP"},
    "ESFP": {"ISFJ", "ENFJ", "ESFP"},
    "INFJ": {"ENFP", "ENFJ", "INFJ"},
    "INFP": {"ENFJ", "ENTJ", "INFP"},
}


def mbti_score(candidate_mbti: str | None, mentor_mbti: str | None) -> float:
    if not candidate_mbti or not mentor_mbti:
        return 12

    candidate = candidate_mbti.upper()
    mentor = mentor_mbti.upper()

    if candidate == mentor:
        return 20
    if mentor in COMPLEMENTARY_PAIRS.get(candidate, set()):
        return 25
    if candidate[:2] == mentor[:2] or candidate[2:] == mentor[2:]:
        return 16
    return 10


def department_fit_score(candidate_mbti: str | None, department: str) -> float:
    if not candidate_mbti:
        return 6
    return 9 if candidate_mbti.upper() in DEPARTMENT_MBTI_TENDENCIES.get(department, set()) else 6


def rank_mentors(
    candidate_mbti: str | None,
    target_department: str,
    employees: list[dict],
    limit: int = 3,
) -> list[dict]:
    ranked = []

    for employee in employees:
        same_department = employee.get("department") == target_department
        department_score = 35 if same_department else 12
        personality_score = mbti_score(candidate_mbti, employee.get("mbti"))
        mentoring_score = min(float(employee.get("mentoring_score", 0)) / 5, 1) * 20
        availability_score = min(float(employee.get("availability", 0)), 1) * 20
        total = round(department_score + personality_score + mentoring_score + availability_score, 2)

        ranked.append(
            {
                "employee_id": employee["employee_id"],
                "name": employee["name"],
                "department": employee["department"],
                "mbti": employee.get("mbti"),
                "compatibility_score": total,
                "explanation": (
                    "Prioritized for onboarding fit using department match, mentor quality, "
                    "availability, and MBTI compatibility as a support signal only."
                ),
            }
        )

    return sorted(ranked, key=lambda item: item["compatibility_score"], reverse=True)[:limit]
