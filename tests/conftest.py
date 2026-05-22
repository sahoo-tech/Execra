import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import pytest
from core.config import Settings

@pytest.fixture
def mock_settings():
    """
    Returns a fresh Settings instance for testing.
    """
    return Settings(
        LLM_BACKEND="test-model",
        OPENAI_API_KEY="test-key",
        GEMINI_API_KEY="test-key",
        API_PORT=9999
    )

@pytest.fixture
def api_base_url():
    """
    Returns the base URL for the API in tests.
    """
    return "http://localhost:8000"
import numpy as np
import pytest

from core.config import Settings


@pytest.fixture
def sample_frame() -> np.ndarray:
    """Return a small dummy screen frame for tests."""
    return np.zeros((10, 10, 3), dtype=np.uint8)


@pytest.fixture
def mock_settings() -> Settings:
    """Return a Settings object configured for tests."""
    settings = Settings()
    settings.OPENAI_API_KEY = "test-openai-key"
    settings.GEMINI_API_KEY = "test-gemini-key"
    settings.SCREEN_CAPTURE_FPS = 1
    settings.DETECTION_THRESHOLD = 0.1
    settings.DELTA_THRESHOLD = 0.01
    settings.API_HOST = "127.0.0.1"
    settings.API_PORT = 9001
    settings.LOG_LEVEL = "DEBUG"
    settings.REDIS_URL = "redis://localhost:6379"
    settings.TRUST_SCORE_W1 = 0.4
    settings.TRUST_SCORE_W2 = 0.35
    settings.TRUST_SCORE_W3 = 0.25
    return settings
