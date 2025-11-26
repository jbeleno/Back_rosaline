"""Application configuration settings.

This module centralizes environment-driven settings so they can be injected
throughout the app without re-reading environment variables in every module.
"""

from functools import lru_cache
from typing import List

from dotenv import load_dotenv
from pydantic import Field, FieldValidationInfo, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


load_dotenv()


class Settings(BaseSettings):
    """Environment configuration for the FastAPI backend."""

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = Field(default="development", env="APP_ENV")
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=False, env="DEBUG")

    database_url: str = Field(..., env="DATABASE_URL")

    secret_key: str = Field(..., env="SECRET_KEY")
    access_token_expire_minutes: int = Field(default=60, env="ACCESS_TOKEN_EXPIRE_MINUTES")

    cors_origins_raw: str = Field(default="*", env="CORS_ORIGINS")

    project_name: str = Field(default="API Rosaline Bakery", env="PROJECT_NAME")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    frontend_url: str | None = Field(default=None, env="FRONTEND_URL")

    @property
    def cors_origins(self) -> List[str]:
        """Return the list of CORS origins based on configuration."""
        if not self.cors_origins_raw or self.cors_origins_raw.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins_raw.split(",") if origin.strip()]

    @field_validator("database_url", "secret_key")
    @classmethod
    def _validate_required(cls, value: str, info: FieldValidationInfo) -> str:  # noqa: D401
        if not value:
            env_name = info.field_name.upper()
            raise ValueError(f"Environment variable '{env_name}' debe estar configurada")
        return value


@lru_cache()
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
