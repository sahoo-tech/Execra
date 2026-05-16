"""
Central configuration module for Execra.
Modules should import settings from here instead of os.getenv().
"""

import os
from dataclasses import dataclass, field

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

    # Privacy Configuration
    PRIVACY_MASKING_ENABLED: bool = True
    MASKED_REGIONS: list = field(
        default_factory=list
    )  # List of [x1, y1, x2, y2]
    SENSITIVE_PATTERNS: list = field(
        default_factory=lambda: [
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",  # Emails
            r"\b\d{4}-\d{4}-\d{4}-\d{4}\b",  # Credit Cards
            r"\b\d{3}-\d{2}-\d{4}\b",  # SSN
            r"(?i)api_key[:=]\s*[A-Za-z0-9_\-]+",  # Generic API Keys
        ]
    )

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

        # Privacy Configuration
        if env_val := os.getenv("PRIVACY_MASKING_ENABLED"):
            self.PRIVACY_MASKING_ENABLED = env_val.lower() == "true"
        # MASKED_REGIONS and SENSITIVE_PATTERNS are complex types,
        # usually handled via JSON strings in .env if needed.
        # For now, we use defaults or manual override.

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
            msg = f"Missing required configuration: {', '.join(missing)}"
            raise ValueError(msg)


# Global settings instance - import this everywhere
settings = Settings()
