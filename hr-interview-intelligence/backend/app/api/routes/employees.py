from fastapi import APIRouter

from app.seed_data import SEED_EMPLOYEES

router = APIRouter()


@router.get("/coworkers")
def list_coworkers() -> list[dict]:
    return SEED_EMPLOYEES
