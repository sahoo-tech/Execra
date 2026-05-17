"""
Unit tests for core/config.py
Tests: defaults, environment variable overrides, and validation.
"""

import os
from unittest.mock import patch

import pytest
from dotenv import load_dotenv


def test_settings_correct_defaults():
    """Test that Settings uses correct default values."""
    # Import here to get a fresh instance with defaults
    from core.config import Settings

    settings = Settings()

    # LLM Configuration
    assert settings.LLM_BACKEND == "gpt-4o"
    assert settings.OPENAI_API_KEY == ""
    assert settings.GEMINI_API_KEY == ""

    # Screen Capture & Detection
    assert settings.SCREEN_CAPTURE_FPS == 2
    assert settings.DETECTION_THRESHOLD == 0.5
    assert settings.DELTA_THRESHOLD == 0.05

    # API Configuration
    assert settings.API_HOST == "0.0.0.0"
    assert settings.API_PORT == 8000
    assert settings.LOG_LEVEL == "INFO"
    assert settings.CORS_ORIGINS == [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]

    # Redis Configuration
    assert settings.REDIS_URL == "redis://localhost:6379"

    # Trust Score Weights
    assert settings.TRUST_SCORE_W1 == 0.5
    assert settings.TRUST_SCORE_W2 == 0.3
    assert settings.TRUST_SCORE_W3 == 0.2


def test_settings_override_via_env_vars():
    """Test that environment variables correctly override defaults."""
    # Set up environment variables
    env_vars = {
        "LLM_BACKEND": "claude-3",
        "OPENAI_API_KEY": "sk-test-key-123",
        "GEMINI_API_KEY": "gemini-test-key",
        "SCREEN_CAPTURE_FPS": "5",
        "DETECTION_THRESHOLD": "0.75",
        "DELTA_THRESHOLD": "0.1",
        "API_HOST": "127.0.0.1",
        "API_PORT": "9000",
        "LOG_LEVEL": "DEBUG",
        "CORS_ORIGINS": "https://app.example.com, https://admin.example.com",
        "REDIS_URL": "redis://localhost:6380",
        "TRUST_SCORE_W1": "0.6",
        "TRUST_SCORE_W2": "0.25",
        "TRUST_SCORE_W3": "0.15",
    }

    with patch.dict(os.environ, env_vars, clear=False):
        from core.config import Settings

        settings = Settings()

        # LLM Configuration
        assert settings.LLM_BACKEND == "claude-3"
        assert settings.OPENAI_API_KEY == "sk-test-key-123"
        assert settings.GEMINI_API_KEY == "gemini-test-key"

        # Screen Capture & Detection
        assert settings.SCREEN_CAPTURE_FPS == 5
        assert settings.DETECTION_THRESHOLD == 0.75
        assert settings.DELTA_THRESHOLD == 0.1

        # API Configuration
        assert settings.API_HOST == "127.0.0.1"
        assert settings.API_PORT == 9000
        assert settings.LOG_LEVEL == "DEBUG"
        assert settings.CORS_ORIGINS == [
            "https://app.example.com",
            "https://admin.example.com",
        ]

        # Redis Configuration
        assert settings.REDIS_URL == "redis://localhost:6380"

        # Trust Score Weights
        assert settings.TRUST_SCORE_W1 == 0.6
        assert settings.TRUST_SCORE_W2 == 0.25
        assert settings.TRUST_SCORE_W3 == 0.15


def test_settings_missing_required_key_raises_error():
    """Test that missing required API keys raise ValueError."""
    from core.config import Settings

    # Create settings without API keys
    settings = Settings()

    # Should raise ValueError when validating
    with pytest.raises(ValueError, match="Missing required configuration"):
        settings.validate_required()

    # Now set the keys and validation should pass
    settings.OPENAI_API_KEY = "sk-test"
    settings.GEMINI_API_KEY = "gemini-test"
    settings.validate_required()  # Should not raise


def test_settings_partial_required_keys_raises_error():
    """Test that partial required keys also raise ValueError."""
    from core.config import Settings

    settings = Settings()
    settings.OPENAI_API_KEY = "sk-test"
    # Missing GEMINI_API_KEY

    with pytest.raises(ValueError, match="Missing required configuration"):
        settings.validate_required()


def test_parse_cors_origins_ignores_empty_entries():
    """Test that empty entries and extra whitespace are ignored."""
    from core.config import parse_cors_origins

    raw_origins = " http://localhost:3000, ,https://app.example.com, "

    assert parse_cors_origins(raw_origins) == [
        "http://localhost:3000",
        "https://app.example.com",
    ]


# ---------------------------------------------------------------------------
# Trust-score weight validation tests (Issue #166)
# ---------------------------------------------------------------------------


def test_trust_score_weights_valid_exact_sum():
    """Weights that sum to exactly 1.0 must not raise."""
    env_vars = {"TRUST_SCORE_W1": "0.5", "TRUST_SCORE_W2": "0.3", "TRUST_SCORE_W3": "0.2"}
    with patch.dict(os.environ, env_vars, clear=False):
        from core.config import Settings

        settings = Settings()  # must not raise
        assert settings.TRUST_SCORE_W1 == 0.5
        assert settings.TRUST_SCORE_W2 == 0.3
        assert settings.TRUST_SCORE_W3 == 0.2


def test_trust_score_weights_valid_within_tolerance():
    """Weights whose sum is within ±0.001 of 1.0 must not raise."""
    # 0.5005 + 0.3 + 0.2 = 1.0005 → |1.0005 - 1.0| = 0.0005 ≤ 0.001
    env_vars = {"TRUST_SCORE_W1": "0.5005", "TRUST_SCORE_W2": "0.3", "TRUST_SCORE_W3": "0.2"}
    with patch.dict(os.environ, env_vars, clear=False):
        from core.config import Settings

        Settings()  # must not raise


def test_trust_score_weights_invalid_sum_above_tolerance():
    """Weights summing more than 0.001 above 1.0 must raise ValueError."""
    # 0.6 + 0.3 + 0.2 = 1.1 → clearly outside tolerance
    env_vars = {"TRUST_SCORE_W1": "0.6", "TRUST_SCORE_W2": "0.3", "TRUST_SCORE_W3": "0.2"}
    with patch.dict(os.environ, env_vars, clear=False):
        from core.config import Settings

        with pytest.raises(ValueError, match="TRUST_SCORE_W1 \\+ TRUST_SCORE_W2 \\+ TRUST_SCORE_W3"):
            Settings()


def test_trust_score_weights_invalid_sum_below_tolerance():
    """Weights summing more than 0.001 below 1.0 must raise ValueError."""
    # 0.3 + 0.3 + 0.2 = 0.8 → clearly outside tolerance
    env_vars = {"TRUST_SCORE_W1": "0.3", "TRUST_SCORE_W2": "0.3", "TRUST_SCORE_W3": "0.2"}
    with patch.dict(os.environ, env_vars, clear=False):
        from core.config import Settings

        with pytest.raises(ValueError, match="TRUST_SCORE_W1 \\+ TRUST_SCORE_W2 \\+ TRUST_SCORE_W3"):
            Settings()
