"""Application configuration loaded from environment variables.

Uses pydantic-settings to validate and type-cast all configuration values.
Defaults are provided for local development; production values come from .env.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable overrides."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    app_name: str = "DataViz"
    app_description: str = "Interactive Data Visualization Web App"
    debug: bool = False

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Logging
    log_level: str = "INFO"
    log_dir: str = "logs"

    # Upload limits
    max_upload_size_mb: int = 50
    allowed_extensions: str = ".csv,.tsv,.txt"

    @property
    def max_upload_size_bytes(self) -> int:
        """Maximum upload size in bytes."""
        return self.max_upload_size_mb * 1024 * 1024

    @property
    def allowed_extensions_list(self) -> list[str]:
        """Parsed list of allowed file extensions."""
        return [ext.strip() for ext in self.allowed_extensions.split(",")]


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings singleton."""
    return Settings()
