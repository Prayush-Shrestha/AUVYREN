import pytest
from app.core.config import Settings
from pydantic import ValidationError

BASE = {
    "database_url": "postgresql://user:pass@localhost:5432/auvyren",
    "secret_key": "a" * 48,
}


def test_plain_postgres_url_is_normalized_to_asyncpg() -> None:
    settings = Settings(**BASE)

    assert settings.database_url.startswith("postgresql+asyncpg://")


def test_production_requires_secure_cookies() -> None:
    with pytest.raises(ValidationError):
        Settings(**BASE, app_env="production", session_cookie_secure=False)


def test_production_rejects_placeholder_secret() -> None:
    with pytest.raises(ValidationError):
        Settings(
            database_url=BASE["database_url"],
            secret_key="replace-with-at-least-32-random-characters",
            app_env="production",
            session_cookie_secure=True,
        )


def test_production_rejects_wildcard_cors() -> None:
    with pytest.raises(ValidationError):
        Settings(
            **BASE,
            app_env="production",
            session_cookie_secure=True,
            cors_origins="*",
        )
