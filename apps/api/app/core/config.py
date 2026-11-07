"""Application configuration.

All environment values are loaded once at process startup. Secrets exist only
on the server and are never exposed through API responses.
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[4]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Application
    app_name: str = "Auvyren API"
    app_version: str = "0.1.0"
    app_env: Literal["development", "test", "production"] = "development"
    debug: bool = False
    docs_enabled: bool = True
    api_v1_prefix: str = "/api/v1"

    # Infrastructure
    database_url: str
    secret_key: str = Field(min_length=32)

    # Browser boundaries
    cors_origins: str = "http://localhost:3000"
    allowed_hosts: str = "localhost,127.0.0.1,testserver"
    web_app_url: str = "http://localhost:3000"

    # Sessions
    session_cookie_name: str = "auv_session"
    session_cookie_secure: bool = False
    session_cookie_domain: str | None = None
    session_ttl_days: int = Field(default=30, ge=1, le=90)
    session_absolute_ttl_days: int = Field(default=90, ge=1, le=365)
    session_refresh_minutes: int = Field(default=5, ge=1, le=60)
    csrf_cookie_name: str = "auv_csrf"
    csrf_header_name: str = "X-CSRF-Token"

    # Password reset
    password_reset_ttl_minutes: int = Field(default=30, ge=5, le=120)

    # Email
    email_provider: Literal["console", "smtp"] = "console"
    email_from: str = "no-reply@auvyren.local"
    smtp_host: str | None = None
    smtp_port: int = Field(default=587, ge=1, le=65535)
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_use_tls: bool = True

    # Local AI (activated in Phase 4)
    ollama_base_url: str = "http://localhost:11434"
    ollama_request_timeout_seconds: int = Field(default=120, ge=5, le=600)
    ai_key_encryption_key: str | None = None

    @field_validator("database_url")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        if value.startswith("postgresql://"):
            return value.replace("postgresql://", "postgresql+asyncpg://", 1)
        if not value.startswith("postgresql+asyncpg://"):
            raise ValueError("DATABASE_URL must be a PostgreSQL URL")
        return value

    @field_validator("cors_origins", "allowed_hosts")
    @classmethod
    def normalize_csv(cls, value: str) -> str:
        items = [item.strip() for item in value.split(",") if item.strip()]
        if not items:
            raise ValueError("Comma-separated value must contain at least one item")
        return ",".join(items)

    @field_validator("session_cookie_domain", mode="before")
    @classmethod
    def blank_cookie_domain_is_none(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @field_validator("web_app_url")
    @classmethod
    def validate_web_app_url(cls, value: str) -> str:
        value = value.rstrip("/")
        if not value.startswith(("http://", "https://")):
            raise ValueError("WEB_APP_URL must be an absolute http(s) URL")
        return value

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin for origin in self.cors_origins.split(",") if origin]

    @property
    def allowed_host_list(self) -> list[str]:
        return [host for host in self.allowed_hosts.split(",") if host]

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @model_validator(mode="after")
    def validate_environment(self) -> "Settings":
        if self.is_production:
            if not self.session_cookie_secure:
                raise ValueError("SESSION_COOKIE_SECURE must be true in production")
            if self.secret_key.startswith(("replace-", "dev-only", "change-me")):
                raise ValueError("SECRET_KEY must be replaced in production")
            if "*" in self.cors_origin_list:
                raise ValueError("Wildcard CORS origins are not allowed in production")
            if self.email_provider != "smtp":
                raise ValueError("EMAIL_PROVIDER must be smtp in production")
            if not self.smtp_host:
                raise ValueError("SMTP_HOST is required in production")

        if self.session_absolute_ttl_days < self.session_ttl_days:
            raise ValueError("SESSION_ABSOLUTE_TTL_DAYS must be at least SESSION_TTL_DAYS")

        if self.email_provider == "smtp" and not self.smtp_host:
            raise ValueError("SMTP_HOST is required when EMAIL_PROVIDER=smtp")

        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
