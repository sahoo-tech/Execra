import secrets

import numpy as np
import pytest

from core.config import Settings


@pytest.fixture
def api_base_url():
    """Returns the base URL for the API in tests."""
    return "http://localhost:8000"


@pytest.fixture
def sample_frame() -> np.ndarray:
    """Return a small dummy screen frame for tests."""
    return np.zeros((10, 10, 3), dtype=np.uint8)


@pytest.fixture
def mock_settings() -> Settings:
    """Return a Settings object configured for tests."""
    s = Settings()
    s.LLM_BACKEND = "openai"
    s.OPENAI_API_KEY = "test-openai-key"
    s.GEMINI_API_KEY = "test-gemini-key"
    s.ENCRYPTION_KEY = secrets.token_hex(32)
    s.SCREEN_CAPTURE_FPS = 1
    s.DETECTION_THRESHOLD = 0.1
    s.DELTA_THRESHOLD = 0.01
    s.API_HOST = "127.0.0.1"
    s.API_PORT = 9001
    s.LOG_LEVEL = "DEBUG"
    s.REDIS_URL = "redis://localhost:6379"
    s.TRUST_SCORE_W1 = 0.4
    s.TRUST_SCORE_W2 = 0.35
    s.TRUST_SCORE_W3 = 0.25
    return s


@pytest.fixture(autouse=True)
def isolate_env(monkeypatch):
    """
    Prevent local .env values from leaking into tests.

    Clears keys that have strong defaults in Settings but may be overridden
    by a developer's .env file (e.g. LLM_BACKEND=local). Each test starts
    with a clean slate; tests that need specific values set them explicitly.
    """
    keys_to_clear = [
        "LLM_BACKEND",
        "OPENAI_API_KEY",
        "GEMINI_API_KEY",
        "ENCRYPTION_KEY",
        "REDIS_URL",
        "CAPTURE_FPS",
        "LOG_FORMAT",
        "SANDBOX_MODE",
        "WS_API_TOKEN",
    ]
    for key in keys_to_clear:
        monkeypatch.delenv(key, raising=False)


@pytest.fixture(autouse=True)
def encryption_key(monkeypatch):
    """Set a valid ENCRYPTION_KEY in the environment for crypto tests."""
    key = secrets.token_hex(32)
    monkeypatch.setenv("ENCRYPTION_KEY", key)
    # Also patch the module-level settings so crypto.py picks it up
    import core.security.crypto as crypto_mod
    import core.config as config_mod

    monkeypatch.setattr(config_mod.settings, "ENCRYPTION_KEY", key)
    monkeypatch.setattr(crypto_mod, "_fernet_instance", None, raising=False)
    return key


@pytest.fixture(autouse=True, scope="module")
def cleanup_module_patches():
    """Automatically stops all active mocks after each module finishes execution."""
    yield
    from unittest.mock import patch

    patch.stopall()
