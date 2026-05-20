from fastapi import APIRouter

from app.seed_data import SEED_EMPLOYEES

router = APIRouter()


@router.get("/mentors")
def list_mentors() -> list[dict]:
    return SEED_EMPLOYEES
