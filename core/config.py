"""
Central configuration module for Execra.
All modules should import settings from here instead of using os.getenv() directly.
"""

from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Typed settings for Execra with automatic environment variable loading.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    # LLM Configuration
    LLM_BACKEND: str = "gpt-4o"
    OPENAI_API_KEY: str = ""
    GEMINI_API_KEY: str = ""

    # Screen Capture & Detection
    SCREEN_CAPTURE_FPS: int = 2
    DETECTION_THRESHOLD: float = 0.5
    DELTA_THRESHOLD: float = 0.05

    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    LOG_LEVEL: str = "INFO"

    # Redis Configuration
    REDIS_URL: str = "redis://localhost:6379"

    # Trust Score Weights
    TRUST_SCORE_W1: float = 0.5
    TRUST_SCORE_W2: float = 0.3
    TRUST_SCORE_W3: float = 0.2

    def validate_required(self) -> None:
        """
        Validate that required fields are set (not empty).
        Raises ValueError if required keys are missing.
        """
        missing = []
        if not self.OPENAI_API_KEY:
            missing.append("OPENAI_API_KEY")
        if not self.GEMINI_API_KEY:
            missing.append("GEMINI_API_KEY")

        if missing:
            raise ValueError(f"Missing required configuration: {', '.join(missing)}")


# Global settings instance - import this everywhere
settings = Settings()
