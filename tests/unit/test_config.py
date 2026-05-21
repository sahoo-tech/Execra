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
        "http://localhost:5173",
        "http://127.0.0.1:5173",
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
