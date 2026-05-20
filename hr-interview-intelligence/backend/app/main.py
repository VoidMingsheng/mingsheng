from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import candidates, employees, health, jobs
from app.core.config import get_settings


settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Decision support API for HR interview intelligence workflows.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix=settings.api_prefix, tags=["health"])
app.include_router(candidates.router, prefix=f"{settings.api_prefix}/candidates", tags=["candidates"])
app.include_router(jobs.router, prefix=f"{settings.api_prefix}/jobs", tags=["jobs"])
app.include_router(employees.router, prefix=f"{settings.api_prefix}/employees", tags=["employees"])
