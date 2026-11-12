"""Validated application settings."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Settings loaded from environment variables and an optional .env file."""

    model_config = SettingsConfigDict(
        env_prefix="NEXDROP_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "NexDrop API"
    environment: Literal["development", "testing", "staging", "production"] = "development"
    api_v1_prefix: str = "/api/v1"
    log_level: str = "INFO"
    cors_origins: list[str] = Field(default_factory=list)
    database_url: str | None = None

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, value: str | None) -> str | None:
        """Require the async SQLAlchemy Psycopg dialect."""
        if value is not None and not value.startswith("postgresql+psycopg://"):
            raise ValueError("NEXDROP_DATABASE_URL must use postgresql+psycopg://")
        return value


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide settings instance."""
    return Settings()
