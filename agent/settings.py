"""Typed application settings, loaded from environment variables / .env."""
from __future__ import annotations

from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class ConfigError(RuntimeError):
    """Raised when a required setting is missing at the point it is needed."""


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore", case_sensitive=False
    )

    azure_ai_foundry_endpoint: str = ""
    azure_ai_foundry_api_key: SecretStr = SecretStr("")
    azure_ai_foundry_deployment_name: str = ""

    supabase_url: str = ""
    supabase_service_role_key: SecretStr = SecretStr("")

    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    # Explicit ceilings so no run can spin forever.
    max_graph_steps: int = Field(default=30, ge=5, le=200)
    max_budget_revisions: int = Field(default=4, ge=0, le=6)
    llm_timeout_seconds: float = Field(default=60.0, gt=0, le=300)
    llm_max_tokens: int = Field(default=2048, ge=256, le=8192)
    max_message_chars: int = Field(default=2000, ge=100, le=10000)
    rate_limit_per_minute: int = Field(default=20, ge=0, le=1000)  # chat turns per client per minute; 0 disables
    db_timeout_seconds: float = Field(default=10.0, gt=0, le=60)

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip().rstrip("/") for o in self.cors_origins.split(",") if o.strip()]

    def require_llm(self) -> None:
        missing = [
            name
            for name, value in (
                ("AZURE_AI_FOUNDRY_ENDPOINT", self.azure_ai_foundry_endpoint),
                ("AZURE_AI_FOUNDRY_API_KEY", self.azure_ai_foundry_api_key.get_secret_value()),
                ("AZURE_AI_FOUNDRY_DEPLOYMENT_NAME", self.azure_ai_foundry_deployment_name),
            )
            if not value
        ]
        if missing:
            raise ConfigError("Azure AI Foundry is not configured; missing " + ", ".join(missing))

    def require_supabase(self) -> None:
        missing = [
            name
            for name, value in (
                ("SUPABASE_URL", self.supabase_url),
                ("SUPABASE_SERVICE_ROLE_KEY", self.supabase_service_role_key.get_secret_value()),
            )
            if not value
        ]
        if missing:
            raise ConfigError("Supabase is not configured; missing " + ", ".join(missing))


@lru_cache
def get_settings() -> Settings:
    return Settings()
