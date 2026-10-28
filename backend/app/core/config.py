"""Application configuration with validation.

Configuration is loaded from environment variables and an optional `.env` file.
Production mode refuses insecure defaults and fails fast when required secrets
are missing. Development falls back to SQLite and clearly documented insecure
dev defaults that are rejected in production.
"""

from typing import List
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ------------------------------------------------------------------ app
    APP_ENV: str = Field(
        default="development",
        description="development | production | demo",
    )

    DATABASE_URL: str = Field(
        default="sqlite:///./sentinelops.db",
        description="SQLAlchemy database URL (sqlite dev fallback, postgresql prod)",
    )
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis URL for background jobs and rate limiting",
    )

    # ------------------------------------------------------------------ ollama
    OLLAMA_BASE_URL: str = Field(
        default="http://127.0.0.1:11434",
        description="Local Ollama HTTP API base URL",
    )
    OLLAMA_MODEL: str = Field(
        default="codellama:7b-instruct",
        description="Configured local coding model",
    )
    OLLAMA_CONTEXT_SIZE: int = Field(default=4096, description="Model context window")
    OLLAMA_TIMEOUT_SECONDS: int = Field(default=120, description="Request timeout")
    OLLAMA_MAX_CONCURRENT_REQUESTS: int = Field(
        default=1, description="Bounded concurrent inference requests"
    )
    AI_CLOUD_FALLBACK: bool = Field(
        default=False,
        description="Must never silently fall back to a cloud AI provider",
    )
    DEMO_MODE: bool = Field(
        default=False,
        description="Offline demonstration mode using labelled fixtures only",
    )

    # ---------------------------------------------------------------- auth
    SECRET_KEY: str = Field(
        default="dev-insecure-change-me",
        description="Application secret (must be real in production)",
    )
    SESSION_SECRET: str = Field(
        default="dev-insecure-change-me",
        description="Session signing secret (must be real in production)",
    )
    SESSION_COOKIE_NAME: str = Field(default="sentinelops_session")
    SESSION_COOKIE_SECURE: bool = Field(
        default=False, description="Set True when served over HTTPS"
    )
    SESSION_COOKIE_SAMESITE: str = Field(default="lax")
    SESSION_TTL_SECONDS: int = Field(default=86400, description="Session lifetime")
    LOGIN_RATE_LIMIT: str = Field(default="5/min")
    API_RATE_LIMIT: str = Field(default="60/min")
    PASSWORD_RESET_ENABLED: bool = Field(
        default=False,
        description="Only enable when a fully secure flow is implemented",
    )

    # ---------------------------------------------------------------- github
    GITHUB_APP_ID: str = Field(default="")
    GITHUB_APP_PRIVATE_KEY_PATH: str = Field(default="")
    GITHUB_PRIVATE_KEY: str = Field(default="")
    GITHUB_WEBHOOK_SECRET: str = Field(default="")
    GITHUB_TOKEN: str = Field(
        default="",
        description="Narrowly scoped fine-grained PAT (single operator repos only)",
    )
    GITHUB_ALLOWLIST_REPOS: str = Field(
        default="",
        description="Comma-separated allowlist of owner/name repositories",
    )
    GITHUB_READ_ONLY: bool = Field(
        default=True, description="Start read-only; write requires explicit approval"
    )
    GITHUB_API_BASE_URL: str = Field(default="https://api.github.com")

    # ---------------------------------------------------------------- logs
    LOG_MONITORING_ROOTS: str = Field(
        default="",
        description="Semicolon-separated allowed monitoring root paths",
    )
    LOG_RETENTION_DAYS: int = Field(default=30)
    LOG_MAX_RECORD_SIZE: int = Field(default=1024 * 1024)
    LOG_INGESTION_RATE: str = Field(default="100/s")

    # ---------------------------------------------------------------- sandbox
    SANDBOX_IMAGE: str = Field(default="sentinelops-worker:latest")
    SANDBOX_CPU_LIMIT: str = Field(default="1")
    SANDBOX_MEMORY_LIMIT: str = Field(default="512m")
    SANDBOX_NETWORK_DISABLED: bool = Field(default=True)
    SANDBOX_TIMEOUT_SECONDS: int = Field(default=300)

    # ------------------------------------------------------------ approvals
    APPROVAL_LIFETIME_SECONDS: int = Field(default=3600, description="Short expiry")
    APPROVAL_REAUTH_REQUIRED: bool = Field(
        default=False, description="Recent reauthentication for sensitive actions"
    )

    # ------------------------------------------------------------- audit
    AUDIT_RETENTION_DAYS: int = Field(default=90)

    # ------------------------------------------------------------------ validators
    @field_validator("APP_ENV")
    @classmethod
    def _valid_env(cls, v: str) -> str:
        if v not in ("development", "production", "demo"):
            raise ValueError("APP_ENV must be development, production, or demo")
        return v

    @field_validator("SESSION_COOKIE_SAMESITE")
    @classmethod
    def _valid_samesite(cls, v: str) -> str:
        if v not in ("lax", "strict", "none"):
            raise ValueError("SESSION_COOKIE_SAMESITE must be lax, strict, or none")
        return v

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    @property
    def is_demo(self) -> bool:
        return self.APP_ENV == "demo" or self.DEMO_MODE

    @property
    def github_allowlist(self) -> List[str]:
        raw = self.GITHUB_ALLOWLIST_REPOS.strip()
        if not raw:
            return []
        return [item.strip() for item in raw.split(",") if item.strip()]

    @property
    def log_monitoring_roots(self) -> List[str]:
        raw = self.LOG_MONITORING_ROOTS.strip()
        if not raw:
            return []
        return [item.strip() for item in raw.split(";") if item.strip()]

    def require_production_secrets(self) -> None:
        """Fail startup when production settings are missing or insecure."""
        if not self.is_production:
            return
        missing: List[str] = []
        insecure_prefixes = ("dev-insecure-change-me", "")
        for name in ("SECRET_KEY", "SESSION_SECRET", "DATABASE_URL"):
            value = getattr(self, name)
            if not value or value in insecure_prefixes or value.startswith("dev-insecure"):
                missing.append(name)
        if missing:
            raise RuntimeError(
                "Production required secrets missing/insecure: "
                + ", ".join(missing)
                + ". Set real values via environment or .env (never commit .env)."
            )


settings = Settings()
