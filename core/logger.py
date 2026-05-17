import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Optional

from core.config import settings


def setup(log_level: Optional[str] = None) -> None:
    """Configure root logging for the application with structured formatting.

    Configures:
    - StreamHandler for console output
    - RotatingFileHandler for logs/execra.log
    - Format: %(asctime)s | %(levelname)s | %(name)s | %(message)s
    - Log level from settings.LOG_LEVEL (or parameter override)

    This is intentionally simple: modules should call `get_logger(name)`.
    """
    # Use provided log_level or fall back to settings
    level_str = log_level or settings.LOG_LEVEL
    level = getattr(logging, level_str.upper(), logging.INFO)

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    root = logging.getLogger()
    # Avoid adding duplicate handlers when called multiple times
    if root.handlers:
        root.handlers.clear()

    # StreamHandler for console output
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    root.addHandler(stream_handler)

    # Create logs directory if it doesn't exist
    logs_dir = "logs"
    os.makedirs(logs_dir, exist_ok=True)

    # RotatingFileHandler for logs/execra.log
    log_file = os.path.join(logs_dir, "execra.log")
    file_handler = RotatingFileHandler(
        log_file, maxBytes=10 * 1024 * 1024, backupCount=5  # 10MB per file, keep 5 backups
    )
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)

    root.setLevel(level)

    # Make sure common uvicorn loggers follow the same level
    logging.getLogger("uvicorn.access").setLevel(level)
    logging.getLogger("uvicorn.error").setLevel(level)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for the given module name.

    All modules should use this instead of logging.getLogger() directly.

    Args:
        name: The module name, typically __name__

    Returns:
        A configured logging.Logger instance
    """
    return logging.getLogger(name)
