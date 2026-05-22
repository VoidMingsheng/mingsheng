from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "HR Interview Intelligence System"
    app_env: str = "development"
    api_prefix: str = "/api/v1"
    backend_cors_origins: str = "http://localhost:3000"
    database_url: str = "postgresql://hr_user:hr_password@localhost:5432/hr_intelligence"
    llm_model: str = "gpt-5.4"
    embedding_model: str = "text-embedding-3-large"
    whisper_model: str = "large-v3"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.backend_cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
