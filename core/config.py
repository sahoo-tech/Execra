"""
Central configuration module for Execra.
Modules should import settings from here instead of os.getenv().
"""

import os
from typing import List, Optional
from dataclasses import dataclass, field
from typing import Optional
from dotenv import load_dotenv
from core.utils.env_validator import assert_env

# Load .env file
load_dotenv()

# Validate environment at startup
assert_env()


def parse_cors_origins(raw_origins: str) -> List[str]:
    return [origin.strip() for origin in raw_origins.split(",") if origin.strip()]


@dataclass
class Settings:
    # LLM Configuration
    LLM_BACKEND: str = "openai"
    OPENAI_API_KEY: str = ""
    GEMINI_API_KEY: str = ""

    # Security
    ENCRYPTION_KEY: str = ""

    # Screen Capture & Detection
    SCREEN_CAPTURE_FPS: int = 2
    DETECTION_THRESHOLD: float = 0.5
    DELTA_THRESHOLD: float = 0.05

    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    LOG_LEVEL: str = "INFO"
    CORS_ORIGINS: List[str] = field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:8000",
            "http://127.0.0.1:8000",
        ]
    )

    # Alert Suppression
    ALERT_COOLDOWN_INFO: int = 60
    ALERT_COOLDOWN_WARNING: int = 30

    # Redis Configuration
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_AUTH: Optional[str] = None

    # Trace Anomaly Detection (Isolation Forest)
    # Expected fraction of anomalous traces in training data.
    ANOMALY_CONTAMINATION: float = 0.1
    # Number of trees in the Isolation Forest ensemble.
    ANOMALY_N_ESTIMATORS: int = 100
    # Random seed — controls both model training and synthetic baseline generation.
    ANOMALY_RANDOM_STATE: int = 42
    # Path where the fitted model is persisted with joblib.
    ANOMALY_MODEL_PATH: str = "data/trace_anomaly_model.joblib"

    # Privacy Configuration
    PRIVACY_MASKING_ENABLED: bool = True
    MASKED_REGIONS: List = field(default_factory=list)
    SENSITIVE_PATTERNS: List = field(
        default_factory=lambda: [
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            r"\b\d{4}-\d{4}-\d{4}-\d{4}\b",
            r"\b\d{3}-\d{2}-\d{4}\b",
            r"(?i)api_key[:=]\s*[A-Za-z0-9_\-]+",
        ]
    )

    def __post_init__(self):
        """Load environment variables and override defaults."""
        # LLM Configuration
        if val := os.getenv("LLM_BACKEND"):
            self.LLM_BACKEND = val
        if val := os.getenv("OPENAI_API_KEY"):
            self.OPENAI_API_KEY = val
        if val := os.getenv("GEMINI_API_KEY"):
            self.GEMINI_API_KEY = val
        # Security
        if val := os.getenv("ENCRYPTION_KEY"):
            self.ENCRYPTION_KEY = val

        # Screen Capture & Detection
        if val := os.getenv("SCREEN_CAPTURE_FPS"):
            self.SCREEN_CAPTURE_FPS = int(val)
        if val := os.getenv("DETECTION_THRESHOLD"):
            self.DETECTION_THRESHOLD = float(val)
        if val := os.getenv("DELTA_THRESHOLD"):
            self.DELTA_THRESHOLD = float(val)

        # API Configuration
        if val := os.getenv("API_HOST"):
            self.API_HOST = val
        if val := os.getenv("API_PORT"):
            self.API_PORT = int(val)
        if val := os.getenv("LOG_LEVEL"):
            self.LOG_LEVEL = val
        if val := os.getenv("CORS_ORIGINS"):
            self.CORS_ORIGINS = parse_cors_origins(val)

        # Redis
        if val := os.getenv("REDIS_URL"):
            self.REDIS_URL = val
        if val := os.getenv("REDIS_PASSWORD"):
            self.REDIS_AUTH = val

        # Trust Score Weights
        if env_val := os.getenv("TRUST_SCORE_W1"):
            self.TRUST_SCORE_W1 = float(env_val)
        if env_val := os.getenv("TRUST_SCORE_W2"):
            self.TRUST_SCORE_W2 = float(env_val)
        if env_val := os.getenv("TRUST_SCORE_W3"):
            self.TRUST_SCORE_W3 = float(env_val)

        # Trace Anomaly Detection
        if env_val := os.getenv("ANOMALY_CONTAMINATION"):
            self.ANOMALY_CONTAMINATION = float(env_val)
        if env_val := os.getenv("ANOMALY_N_ESTIMATORS"):
            self.ANOMALY_N_ESTIMATORS = int(env_val)
        if env_val := os.getenv("ANOMALY_RANDOM_STATE"):
            self.ANOMALY_RANDOM_STATE = int(env_val)
        if env_val := os.getenv("ANOMALY_MODEL_PATH"):
            self.ANOMALY_MODEL_PATH = env_val

        # Privacy Configuration
        if env_val := os.getenv("PRIVACY_MASKING_ENABLED"):
            self.PRIVACY_MASKING_ENABLED = env_val.lower() == "true"
        # MASKED_REGIONS and SENSITIVE_PATTERNS are complex types,
        # usually handled via JSON strings in .env if needed.
        # For now, we use defaults or manual override.

        # Alert Suppression
        if val := os.getenv("ALERT_COOLDOWN_INFO"):
            self.ALERT_COOLDOWN_INFO = int(val)
        if val := os.getenv("ALERT_COOLDOWN_WARNING"):
            self.ALERT_COOLDOWN_WARNING = int(val)

    def validate_required(self) -> None:
        """
        Validate that required fields are set (not empty).
        Raises ValueError if required keys are missing.
        """
        required_fields = {
            "OPENAI_API_KEY": self.OPENAI_API_KEY,
            "GEMINI_API_KEY": self.GEMINI_API_KEY,
            "ENCRYPTION_KEY": self.ENCRYPTION_KEY,
        }

        missing = [key for key, value in required_fields.items() if not value]
        if missing:
            msg = f"Missing required configuration: {', '.join(missing)}"
            raise ValueError(msg)


# Global settings instance - import this everywhere
settings = Settings()