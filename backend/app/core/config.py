"""Environment-based settings for the RightConnect API."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration loaded from backend/.env in local development."""

    model_config = SettingsConfigDict(env_file=(".env", "backend/.env"), env_file_encoding="utf-8", extra="ignore")

    app_name: str = "RightConnect API"
    api_prefix: str = "/api/v1"
    database_url: str = ""
    # Only enable with Supabase's session pooler (port 5432) or a direct connection, never port 6543.
    db_statement_cache: bool = False
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
    razorpay_kattam_report_amount_paise: int = 9900
    razorpay_porutham_pack_amount_paise: int = 29900
    porutham_pack_reports: int = 20
    porutham_pack_days: int = 90
    porutham_history_limit: int = 30
    porutham_admin_history_limit: int = 200
    app_base_url: str = "http://127.0.0.1:8000"
    # Admin console is only served when ADMIN_PATH is set, e.g. "/ops-7f3k2", behind HTTP Basic auth.
    admin_path: str = ""
    admin_basic_user: str = ""
    admin_basic_password: str = ""
    # Comma-separated; when set, only these platform_admin emails may call /admin APIs.
    admin_emails: str = ""
    # Android TWA: package name + comma-separated SHA-256 cert fingerprints from Play Console > App signing.
    android_package_name: str = "app.rightconnect.twa"
    android_sha256_fingerprints: str = ""
    ai_reports_enabled: bool = False
    ai_report_api_key: str = ""
    ai_report_api_url: str = "https://api.openai.com/v1/chat/completions"
    ai_report_model: str = ""
    ai_report_rate_salt: str = ""
    ai_report_hourly_limit: int = 5
    ai_report_daily_limit: int = 100
    ai_report_retention_days: int = 30
    ai_report_family_limit: int = 20

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