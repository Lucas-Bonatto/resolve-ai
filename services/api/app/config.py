from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

from pydantic import AliasChoices, Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(ROOT / ".env.local", ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    ai_provider: str = "demo"
    enable_real_ai: bool = False
    openai_api_key: SecretStr | None = None
    openai_model: str = "gpt-6-luna"
    deployment_profile: Literal["local", "public_showcase"] = "local"
    cors_allowed_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    public_rate_limit_requests: int = Field(default=120, ge=10, le=10_000)
    public_rate_limit_window_seconds: int = Field(default=60, ge=10, le=3600)
    persistence_backend: Literal["memory", "postgres"] = "memory"
    database_url: SecretStr | None = None
    code_revision: str = Field(
        default="unknown",
        validation_alias=AliasChoices(
            "code_revision",
            "RESOLVEAI_CODE_REVISION",
            "CODE_REVISION",
            "GITHUB_SHA",
        ),
    )
    evaluation_suite_version: str = "resolveai-benchmark-v1"
    demo_event_delay_ms: int = Field(default=180, ge=0, le=2000)
    max_agent_turns: int = Field(default=12, ge=1, le=50)
    max_tool_calls_per_run: int = Field(default=20, ge=1, le=200)
    max_investigation_seconds: int = Field(default=120, ge=1, le=3600)

    @property
    def allowed_cors_origins(self) -> list[str]:
        return [origin.strip().rstrip("/") for origin in self.cors_allowed_origins.split(",")]

    @model_validator(mode="after")
    def validate_deployment_boundary(self) -> "Settings":
        origins = self.allowed_cors_origins
        if not origins or any(not origin or "*" in origin for origin in origins):
            raise ValueError("CORS_ALLOWED_ORIGINS must be an explicit origin allowlist")
        for origin in origins:
            parsed = urlsplit(origin)
            if (
                parsed.scheme not in {"http", "https"}
                or not parsed.netloc
                or parsed.path not in {"", "/"}
                or parsed.query
                or parsed.fragment
                or parsed.username
                or parsed.password
            ):
                raise ValueError(f"Invalid CORS origin: {origin}")

        if self.deployment_profile == "public_showcase":
            if self.ai_provider != "demo" or self.enable_real_ai:
                raise ValueError(
                    "public_showcase requires AI_PROVIDER=demo and ENABLE_REAL_AI=false"
                )
            if self.persistence_backend != "memory":
                raise ValueError("public_showcase currently requires PERSISTENCE_BACKEND=memory")
            if any(
                urlsplit(origin).hostname in {"localhost", "127.0.0.1", "::1"}
                for origin in origins
            ):
                raise ValueError(
                    "public_showcase requires an explicit non-local CORS_ALLOWED_ORIGINS value"
                )
            if any(urlsplit(origin).scheme != "https" for origin in origins):
                raise ValueError("public_showcase requires HTTPS CORS origins")
        return self


settings = Settings()
