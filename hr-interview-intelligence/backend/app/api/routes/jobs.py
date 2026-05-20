from fastapi import APIRouter

from app.seed_data import SEED_JOBS

router = APIRouter()


@router.get("/")
def list_jobs() -> list[dict]:
    return SEED_JOBS
