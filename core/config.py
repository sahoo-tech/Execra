"""
Central configuration module for Execra.
All modules should import settings from here instead of using os.getenv() directly.
"""

import os
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv


# Load .env file at module import time
load_dotenv()


@dataclass
class Settings:
    """
    Typed settings for Execra with defaults and environment variable overrides.
    """

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

    def __post_init__(self):
        """Load environment variables and override defaults."""
        # LLM Configuration
        if env_val := os.getenv("LLM_BACKEND"):
            self.LLM_BACKEND = env_val
        if env_val := os.getenv("OPENAI_API_KEY"):
            self.OPENAI_API_KEY = env_val
        if env_val := os.getenv("GEMINI_API_KEY"):
            self.GEMINI_API_KEY = env_val

        # Screen Capture & Detection
        if env_val := os.getenv("SCREEN_CAPTURE_FPS"):
            self.SCREEN_CAPTURE_FPS = int(env_val)
        if env_val := os.getenv("DETECTION_THRESHOLD"):
            self.DETECTION_THRESHOLD = float(env_val)
        if env_val := os.getenv("DELTA_THRESHOLD"):
            self.DELTA_THRESHOLD = float(env_val)

        # API Configuration
        if env_val := os.getenv("API_HOST"):
            self.API_HOST = env_val
        if env_val := os.getenv("API_PORT"):
            self.API_PORT = int(env_val)
        if env_val := os.getenv("LOG_LEVEL"):
            self.LOG_LEVEL = env_val

        # Redis Configuration
        if env_val := os.getenv("REDIS_URL"):
            self.REDIS_URL = env_val

        # Trust Score Weights
        if env_val := os.getenv("TRUST_SCORE_W1"):
            self.TRUST_SCORE_W1 = float(env_val)
        if env_val := os.getenv("TRUST_SCORE_W2"):
            self.TRUST_SCORE_W2 = float(env_val)
        if env_val := os.getenv("TRUST_SCORE_W3"):
            self.TRUST_SCORE_W3 = float(env_val)

    def validate_required(self) -> None:
        """
        Validate that required fields are set (not empty).
        Raises ValueError if required keys are missing.
        """
        required_fields = {
            "OPENAI_API_KEY": self.OPENAI_API_KEY,
            "GEMINI_API_KEY": self.GEMINI_API_KEY,
        }
        
        missing = [key for key, value in required_fields.items() if not value]
        if missing:
            raise ValueError(f"Missing required configuration: {', '.join(missing)}")


# Global settings instance - import this everywhere
settings = Settings()
