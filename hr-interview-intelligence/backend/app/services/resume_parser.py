import re
from dataclasses import dataclass, field


SKILL_CATALOG = {
    "python",
    "fastapi",
    "postgresql",
    "sql",
    "aws",
    "docker",
    "kubernetes",
    "react",
    "next.js",
    "typescript",
    "machine learning",
    "nlp",
    "rag",
    "langchain",
    "sales",
    "crm",
    "negotiation",
    "agile",
    "risk management",
    "stakeholder management",
    "communication",
    "system design",
    "testing",
}


@dataclass
class ParsedResume:
    skills: list[str] = field(default_factory=list)
    years_experience: float = 0
    education: list[str] = field(default_factory=list)
    certifications: list[str] = field(default_factory=list)
    projects: list[str] = field(default_factory=list)


def extract_years_experience(text: str) -> float:
    matches = re.findall(r"(\d+(?:\.\d+)?)\+?\s+years?", text, flags=re.IGNORECASE)
    if not matches:
        return 0
    return max(float(match) for match in matches)


def extract_skills(text: str, catalog: set[str] | None = None) -> list[str]:
    catalog = catalog or SKILL_CATALOG
    lowered = text.lower()
    return sorted(skill for skill in catalog if skill in lowered)


def extract_lines_with_keywords(text: str, keywords: tuple[str, ...]) -> list[str]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    results = []
    for line in lines:
        lowered = line.lower()
        if any(keyword in lowered for keyword in keywords):
            results.append(line)
    return results[:5]


def parse_resume_text(text: str) -> ParsedResume:
    return ParsedResume(
        skills=extract_skills(text),
        years_experience=extract_years_experience(text),
        education=extract_lines_with_keywords(text, ("university", "degree", "bachelor", "master", "diploma")),
        certifications=extract_lines_with_keywords(text, ("certified", "certification", "certificate")),
        projects=extract_lines_with_keywords(text, ("project", "built", "implemented", "designed")),
    )
