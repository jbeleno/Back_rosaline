"""Application configuration settings.

This module centralizes environment-driven settings so they can be injected
throughout the app without re-reading environment variables in every module.
"""

from functools import lru_cache
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment configuration for the FastAPI backend."""

    # Pydantic-settings will automatically search for a .env file and load it.
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,  # Allow matching uppercase env vars to lowercase fields
        extra="ignore",
    )

    APP_ENV: str = "development"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False

    DATABASE_URL: str
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Pydantic will automatically read CORS_ORIGINS and assign it here
    CORS_ORIGINS: str = "*"

    PROJECT_NAME: str = "API Rosaline Bakery"
    LOG_LEVEL: str = "INFO"
    FRONTEND_URL: Optional[str] = None

    # SMTP Configuration for sending emails
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM_EMAIL: Optional[str] = None
    SMTP_FROM_NAME: Optional[str] = None

    @property
    def cors_origins_list(self) -> List[str]:
        """Return the list of CORS origins based on configuration."""
        if not self.CORS_ORIGINS or self.CORS_ORIGINS.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


@lru_cache()
def get_settings() -> Settings:
    """Return cached settings instance.
    
    This function is decorated with @lru_cache to ensure the Settings object
    is created only once, improving performance.
    """
    return Settings()
