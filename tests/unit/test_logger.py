"""Unit tests for the logging module."""

import logging
import os
import tempfile
from logging.handlers import RotatingFileHandler
from unittest.mock import patch

import pytest

from core.logger import get_logger, setup


class TestLoggerConfiguration:
    """Test suite for logging configuration."""

    def test_get_logger_returns_correct_name(self) -> None:
        """Test that get_logger returns a logger with the correct name."""
        module_name = "test.module.name"
        logger = get_logger(module_name)

        assert logger.name == module_name
        assert isinstance(logger, logging.Logger)

    def test_get_logger_returns_same_instance(self) -> None:
        """Test that get_logger returns the same instance for the same name."""
        module_name = "test.module.same"
        logger1 = get_logger(module_name)
        logger2 = get_logger(module_name)

        assert logger1 is logger2

    def test_setup_creates_console_handler(self) -> None:
        """Test that setup creates a StreamHandler for console output."""
        root_logger = logging.getLogger()
        # Clear existing handlers for this test
        root_logger.handlers.clear()

        setup(log_level="INFO")

        # Check that at least one StreamHandler exists
        stream_handlers = [
            h for h in root_logger.handlers if isinstance(h, logging.StreamHandler)
        ]
        assert len(stream_handlers) > 0

    def test_setup_creates_file_handler(self) -> None:
        """Test that setup creates a RotatingFileHandler for file logging."""
        root_logger = logging.getLogger()
        # Clear existing handlers for this test
        root_logger.handlers.clear()

        setup(log_level="INFO")

        # Check that at least one RotatingFileHandler exists
        file_handlers = [
            h for h in root_logger.handlers if isinstance(h, RotatingFileHandler)
        ]
        assert len(file_handlers) > 0

    def test_setup_creates_logs_directory(self) -> None:
        """Test that setup creates the logs/ directory if it doesn't exist."""
        root_logger = logging.getLogger()
        root_logger.handlers.clear()

        # Temporarily change to a temp directory
        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                setup(log_level="INFO")
                assert os.path.exists("logs")
            finally:
                os.chdir(original_cwd)
                root_logger.handlers.clear()

    def test_setup_log_level_from_parameter(self) -> None:
        """Test that setup respects the log_level parameter."""
        root_logger = logging.getLogger()
        root_logger.handlers.clear()

        setup(log_level="DEBUG")
        assert root_logger.level == logging.DEBUG

        root_logger.handlers.clear()
        setup(log_level="WARNING")
        assert root_logger.level == logging.WARNING

    @patch("core.logger.settings")
    def test_setup_log_level_from_settings(self, mock_settings) -> None:
        """Test that setup uses settings.LOG_LEVEL when no parameter is provided."""
        root_logger = logging.getLogger()
        root_logger.handlers.clear()

        mock_settings.LOG_LEVEL = "ERROR"
        setup()

        assert root_logger.level == logging.ERROR

    def test_setup_log_format(self) -> None:
        """Test that setup uses the correct log format."""
        root_logger = logging.getLogger()
        root_logger.handlers.clear()

        setup(log_level="INFO")

        # Get the first handler and check its formatter
        handler = root_logger.handlers[0]
        formatter = handler.formatter
        assert formatter is not None

        # Test the format string is correct
        expected_format = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        assert formatter._fmt == expected_format

    def test_log_level_defaults_to_info(self) -> None:
        """Test that invalid log levels default to INFO."""
        root_logger = logging.getLogger()
        root_logger.handlers.clear()

        setup(log_level="INVALID_LEVEL")
        assert root_logger.level == logging.INFO

    @patch("core.logger.settings")
    def test_setup_with_settings_log_level(self, mock_settings) -> None:
        """Test that setup correctly reads LOG_LEVEL from settings."""
        root_logger = logging.getLogger()
        root_logger.handlers.clear()

        # Test with different levels
        for level_str, level_int in [
            ("DEBUG", logging.DEBUG),
            ("INFO", logging.INFO),
            ("WARNING", logging.WARNING),
            ("ERROR", logging.ERROR),
            ("CRITICAL", logging.CRITICAL),
        ]:
            root_logger.handlers.clear()
            mock_settings.LOG_LEVEL = level_str
            setup()
            assert root_logger.level == level_int
