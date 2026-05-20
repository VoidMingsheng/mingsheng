import re


FILLER_WORDS = {"um", "uh", "like", "basically", "actually", "you know", "sort of", "kind of"}
TECHNICAL_TERMS = {
    "architecture",
    "api",
    "database",
    "testing",
    "deployment",
    "performance",
    "security",
    "scalability",
    "debug",
    "design",
}
PROBLEM_SOLVING_TERMS = {"tradeoff", "root cause", "hypothesis", "debug", "prioritize", "risk", "constraint"}
LEADERSHIP_TERMS = {"led", "owned", "mentored", "coordinated", "initiated", "improved", "delivered"}
LEARNING_TERMS = {"learned", "adapted", "curious", "feedback", "improved", "experimented"}


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z']+", text.lower())


def count_phrase_hits(text: str, phrases: set[str]) -> int:
    lowered = text.lower()
    return sum(1 for phrase in phrases if phrase in lowered)


def analyze_interview(transcript: str, duration_minutes: float | None = None) -> dict:
    words = tokenize(transcript)
    word_count = len(words)
    duration = duration_minutes or max(word_count / 135, 1)
    pace = round(word_count / duration, 2)
    filler_count = sum(1 for word in words if word in FILLER_WORDS)
    filler_rate = filler_count / max(word_count, 1)

    technical_hits = count_phrase_hits(transcript, TECHNICAL_TERMS)
    problem_hits = count_phrase_hits(transcript, PROBLEM_SOLVING_TERMS)
    leadership_hits = count_phrase_hits(transcript, LEADERSHIP_TERMS)
    learning_hits = count_phrase_hits(transcript, LEARNING_TERMS)

    communication_score = 12
    if filler_rate > 0.05:
        communication_score -= 3
    if pace < 95 or pace > 180:
        communication_score -= 2
    if word_count < 80:
        communication_score -= 2

    category_scores = {
        "technical_competency": min(25, 9 + technical_hits * 3),
        "communication_skills": max(4, communication_score),
        "problem_solving_ability": min(10, 4 + problem_hits * 2),
        "cultural_fit": 7,
        "personality_compatibility": 7,
        "learning_potential": min(5, 2 + learning_hits),
        "confidence_professionalism": 4 if filler_rate <= 0.05 else 3,
        "leadership_initiative": min(5, 2 + leadership_hits),
    }

    evidence = {
        "technical_competency": [f"Detected {technical_hits} technical evidence terms in transcript."],
        "communication_skills": [f"Speaking pace estimated at {pace} words per minute.", f"Filler rate estimated at {filler_rate:.2%}."],
        "problem_solving_ability": [f"Detected {problem_hits} problem-solving evidence terms."],
        "learning_potential": [f"Detected {learning_hits} learning or adaptability evidence terms."],
        "leadership_initiative": [f"Detected {leadership_hits} ownership or leadership evidence terms."],
    }

    strengths = []
    weaknesses = []
    if technical_hits >= 3:
        strengths.append("Clear technical vocabulary and project explanation signals.")
    if problem_hits >= 2:
        strengths.append("Shows structured problem-solving evidence.")
    if filler_rate > 0.05:
        weaknesses.append("Communication may need coaching due to filler-heavy responses.")
    if word_count < 80:
        weaknesses.append("Transcript is short, so confidence in analysis is limited.")

    return {
        "category_scores": category_scores,
        "evidence": evidence,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "speaking_pace": pace,
        "filler_rate": round(filler_rate, 4),
    }
