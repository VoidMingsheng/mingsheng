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


def mbti_score(candidate_mbti: str | None, coworker_mbti: str | None) -> float:
    if not candidate_mbti or not coworker_mbti:
        return 12

    candidate = candidate_mbti.upper()
    coworker = coworker_mbti.upper()

    if candidate == coworker:
        return 20
    if coworker in COMPLEMENTARY_PAIRS.get(candidate, set()):
        return 25
    if candidate[:2] == coworker[:2] or candidate[2:] == coworker[2:]:
        return 16
    return 10


def department_fit_score(candidate_mbti: str | None, department: str) -> float:
    if not candidate_mbti:
        return 6
    return 9 if candidate_mbti.upper() in DEPARTMENT_MBTI_TENDENCIES.get(department, set()) else 6


def rank_coworkers(
    candidate_mbti: str | None,
    target_department: str,
    employees: list[dict],
    limit: int = 4,
) -> list[dict]:
    ranked = []

    for employee in employees:
        same_department = employee.get("department") == target_department
        department_score = 35 if same_department else 12
        personality_score = mbti_score(candidate_mbti, employee.get("mbti"))
        onboarding_score = min(float(employee.get("onboarding_score", 0)) / 5, 1) * 20
        availability_score = min(float(employee.get("availability", 0)), 1) * 20
        total = round(department_score + personality_score + onboarding_score + availability_score, 2)

        ranked.append(
            {
                "employee_id": employee["employee_id"],
                "name": employee["name"],
                "department": employee["department"],
                "mbti": employee.get("mbti"),
                "compatibility_score": total,
                "availability": employee.get("availability", 0),
                "explanation": (
                    "Prioritized for onboarding fit using department match, onboarding score, "
                    "availability, and MBTI compatibility as a support signal only."
                ),
            }
        )

    return sorted(ranked, key=lambda item: item["compatibility_score"], reverse=True)[:limit]
