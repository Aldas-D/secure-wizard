"""Aplikacijos konfigūracija pagal aplinką."""

import os
from datetime import timedelta
from pathlib import Path

_DEV_SECRET = "dev-only-change-in-production"  # noqa: S105


class BaseConfig:
    SECRET_KEY = os.environ.get("SECRET_KEY", _DEV_SECRET)

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "sqlite:///" + str(Path(__file__).parent.parent / "instance" / "app.db")
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }

    SESSION_COOKIE_NAME = "sw_session"
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    PERMANENT_SESSION_LIFETIME = timedelta(
        minutes=int(os.environ.get("SESSION_LIFETIME_MINUTES", 60))
    )

    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600

    MAX_CONTENT_LENGTH = 1 * 1024 * 1024

    RATELIMIT_STORAGE_URI = os.environ.get("RATELIMIT_STORAGE_URI", "memory://")
    RATELIMIT_DEFAULT = "60 per minute"
    RATELIMIT_HEADERS_ENABLED = True

    QUIZ_SESSION_LIFETIME_MIN = int(os.environ.get("SESSION_LIFETIME_MINUTES", 60))

    ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD_HASH = os.environ.get("ADMIN_PASSWORD_HASH", "")


class DevelopmentConfig(BaseConfig):
    """Lokalus kūrimas."""

    DEBUG = True
    TESTING = False
    SESSION_COOKIE_SECURE = False
    WTF_CSRF_ENABLED = True


class TestingConfig(BaseConfig):
    TESTING = True
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False
    SESSION_COOKIE_SECURE = False
    RATELIMIT_ENABLED = False


class ProductionConfig(BaseConfig):
    DEBUG = False
    TESTING = False

    SESSION_COOKIE_SECURE = True
    PREFERRED_URL_SCHEME = "https"
    FORCE_HTTPS = True

    @classmethod
    def validate(cls) -> None:
        secret = os.environ.get("SECRET_KEY", "")
        if not secret or secret == _DEV_SECRET:
            raise RuntimeError(
                "SECRET_KEY privalo būti nustatytas produkcijoje (>= 32 baitų atsitiktinis). "
                'Sugeneruokite: python -c "import secrets; print(secrets.token_hex(32))"'
            )
        if len(secret) < 32:
            raise RuntimeError("SECRET_KEY per trumpas - mažiausiai 32 simboliai")
        if not cls.ADMIN_PASSWORD_HASH:
            raise RuntimeError(
                "ADMIN_PASSWORD_HASH privalo būti nustatytas produkcijoje. "
                "Sugeneruokite su: flask --app manage admin-hash"
            )


CONFIG_MAP = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}


def get_config(name: str | None = None) -> type[BaseConfig]:
    selected = name or os.environ.get("FLASK_ENV", "production")
    cfg = CONFIG_MAP.get(selected, ProductionConfig)
    if cfg is ProductionConfig:
        cfg.validate()
    return cfg
