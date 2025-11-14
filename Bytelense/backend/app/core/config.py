"""Core configuration for Bytelense backend."""

from typing import Literal
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Application
    app_name: str = "Bytelense"
    debug: bool = False
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    # Ollama Configuration
    ollama_api_base: str = "http://localhost:11434"
    ollama_model: str = "qwen3:30b"  # or deepseek-r1:8b, qwen3:8b

    # SearXNG Configuration
    searxng_url: str = "http://192.168.1.4"
    searxng_api_base: str = "http://192.168.1.4"

    # Storage
    profiles_dir: str = "./data/profiles"

    # API Settings
    max_image_size_mb: int = 10
    api_timeout_seconds: int = 30

    # OpenFoodFacts
    openfoodfacts_api_base: str = "https://world.openfoodfacts.org"
    openfoodfacts_timeout: int = 3

    # Performance
    max_react_iterations: int = 5


# Global settings instance
settings = Settings()
