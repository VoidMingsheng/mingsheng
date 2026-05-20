from app.services.resume_parser import extract_skills


def normalize_skill(skill: str) -> str:
    return skill.strip().lower()


def compare_candidate_to_job(
    resume_text: str,
    transcript: str,
    required_skills: list[str],
    years_experience: float,
) -> dict:
    candidate_text = f"{resume_text}\n{transcript}"
    detected_skills = set(extract_skills(candidate_text, {normalize_skill(skill) for skill in required_skills}))
    normalized_required = [normalize_skill(skill) for skill in required_skills]

    matched = [skill for skill in normalized_required if skill in detected_skills or skill in candidate_text.lower()]
    gaps = [skill for skill in normalized_required if skill not in matched]

    skill_match_percent = 100 if not normalized_required else round((len(matched) / len(normalized_required)) * 100, 2)
    experience_match_percent = min(100, round((years_experience / 5) * 100, 2)) if years_experience else 35

    return {
        "matched_skills": matched,
        "keyword_gaps": gaps,
        "skill_match_percent": skill_match_percent,
        "experience_match_percent": experience_match_percent,
    }
