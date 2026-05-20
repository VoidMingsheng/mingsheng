from fastapi import APIRouter

from app.models.schemas import AnalysisResponse, CandidateAnalysisRequest
from app.services.pipeline import analyze_candidate

router = APIRouter()


@router.post("/analyze", response_model=AnalysisResponse)
def analyze_candidate_endpoint(payload: CandidateAnalysisRequest) -> dict:
    return analyze_candidate(
        candidate=payload.candidate.model_dump(),
        job=payload.job.model_dump(),
        interview=payload.interview.model_dump(),
    )
