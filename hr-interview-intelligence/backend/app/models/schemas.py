from pydantic import BaseModel, Field


class CandidateInput(BaseModel):
    name: str = Field(..., min_length=1)
    email: str | None = None
    resume_text: str = Field(..., min_length=20)
    mbti: str | None = Field(default=None, max_length=4)


class JobInput(BaseModel):
    id: str
    title: str
    department: str
    description: str
    required_skills: list[str] = Field(default_factory=list)


class InterviewInput(BaseModel):
    transcript: str = Field(..., min_length=20)
    duration_minutes: float | None = Field(default=None, ge=0)


class CandidateAnalysisRequest(BaseModel):
    candidate: CandidateInput
    job: JobInput
    interview: InterviewInput


class CategoryScoreOut(BaseModel):
    key: str
    label: str
    score: float
    max_score: float
    evidence: list[str]


class MentorRecommendationOut(BaseModel):
    employee_id: str
    name: str
    department: str
    mbti: str | None
    compatibility_score: float
    explanation: str


class AnalysisResponse(BaseModel):
    candidate_name: str
    job_title: str
    total_score: float
    recommendation: str
    critical_minimums_passed: bool
    critical_minimum_failures: list[str]
    category_scores: list[CategoryScoreOut]
    strengths: list[str]
    weaknesses: list[str]
    skill_match_percent: float
    experience_match_percent: float
    keyword_gaps: list[str]
    mentor_recommendations: list[MentorRecommendationOut]
    human_review_required: bool = True
