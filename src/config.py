"""Centralized app configuration loaded from environment variables (.env locally)."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Local SQLite file, stored inside this project folder -> override in .env if needed.
    database_url: str = "sqlite+aiosqlite:///./data/app.db"

    # OpenAI credentials -> plug in real value in .env / Render dashboard.
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    # Meta WhatsApp Cloud API credentials -> plug in real value in .env / Render dashboard.
    whatsapp_token: str = ""
    whatsapp_verify_token: str = ""
    whatsapp_api_version: str = "v20.0"

    # Shared secret protecting /admin endpoints.
    admin_api_key: str = "change-me-admin-secret"

    env: str = "development"


@lru_cache
def get_settings() -> Settings:
    return Settings()
