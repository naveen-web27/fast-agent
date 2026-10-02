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
    resend_api_key: str = ""
    resend_from_email: str = "RightConnect <onboarding@resend.dev>"
    razorpay_key_id: str = ""
    razorpay_key_secret: str = ""
    razorpay_webhook_secret: str = ""
    razorpay_pro_amount_paise: int = 0
    razorpay_enterprise_amount_paise: int = 0
    app_base_url: str = "http://127.0.0.1:8000"
    # Admin console is only served when ADMIN_PATH is set, e.g. "/ops-7f3k2", behind HTTP Basic auth.
    admin_path: str = ""
    admin_basic_user: str = ""
    admin_basic_password: str = ""
    # Comma-separated; when set, only these platform_admin emails may call /admin APIs.
    admin_emails: str = ""

    @property
    def admin_email_list(self) -> set[str]:
        return {email.strip().lower() for email in self.admin_emails.split(",") if email.strip()}

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return a cached settings instance."""
    return Settings()