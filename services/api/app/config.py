from pathlib import Path
from typing import Literal

from pydantic import AliasChoices, Field, SecretStr
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


settings = Settings()
