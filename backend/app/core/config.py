"""Environment-based settings for the RightConnect API."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration loaded from backend/.env in local development."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "RightConnect API"
    api_prefix: str = "/api/v1"
    database_url: str = ""
    cors_origins: str = "http://localhost:8000,http://127.0.0.1:8000"
    supabase_url: str = ""
    supabase_publishable_key: str = ""

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return a cached settings instance."""
    return Settings()