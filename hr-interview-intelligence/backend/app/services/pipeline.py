from app.seed_data import SEED_EMPLOYEES
from app.services.interview_analyzer import analyze_interview
from app.services.job_matcher import compare_candidate_to_job
from app.services.coworker_matcher import department_fit_score, rank_coworkers
from app.services.resume_parser import parse_resume_text
from app.services.scoring import score_candidate


def analyze_candidate(candidate: dict, job: dict, interview: dict, employees: list[dict] | None = None) -> dict:
    parsed_resume = parse_resume_text(candidate["resume_text"])
    interview_result = analyze_interview(interview["transcript"], interview.get("duration_minutes"))
    job_match = compare_candidate_to_job(
        resume_text=candidate["resume_text"],
        transcript=interview["transcript"],
        required_skills=job.get("required_skills", []),
        years_experience=parsed_resume.years_experience,
    )

    interview_scores = interview_result["category_scores"]
    category_inputs = {
        **interview_scores,
        "technical_competency": round(
            interview_scores["technical_competency"] * 0.6 + (job_match["skill_match_percent"] / 100) * 25 * 0.4,
            2,
        ),
        "experience_alignment": round((job_match["experience_match_percent"] / 100) * 15, 2),
        "personality_compatibility": department_fit_score(candidate.get("mbti"), job["department"]),
    }

    evidence = {
        **interview_result["evidence"],
        "experience_alignment": [
            f"Estimated {parsed_resume.years_experience:g} years of experience from resume text.",
            f"Experience match estimated at {job_match['experience_match_percent']}%.",
        ],
        "cultural_fit": ["Default MVP score requires HR value rubric validation."],
        "personality_compatibility": [
            "MBTI is used only as a lightweight onboarding compatibility signal and must not drive rejection."
        ],
    }

    strengths = list(interview_result["strengths"])
    weaknesses = list(interview_result["weaknesses"])

    if job_match["skill_match_percent"] >= 75:
        strengths.append("Strong keyword alignment with the target job description.")
    if job_match["keyword_gaps"]:
        weaknesses.append(f"Missing or weak evidence for: {', '.join(job_match['keyword_gaps'])}.")

    scorecard = score_candidate(category_inputs, evidence, strengths, weaknesses)
    coworker_matches = (
        rank_coworkers(candidate.get("mbti"), job["department"], employees or SEED_EMPLOYEES)
        if scorecard["recommendation"] in {"Strong Hire", "Hire"}
        else []
    )

    return {
        "candidate_name": candidate["name"],
        "job_title": job["title"],
        **scorecard,
        "skill_match_percent": job_match["skill_match_percent"],
        "experience_match_percent": job_match["experience_match_percent"],
        "keyword_gaps": job_match["keyword_gaps"],
        "coworker_matches": coworker_matches,
    }
