import logging
from typing import Optional


def setup(log_level: str = "INFO") -> None:
    """Configure root logging for the application.

    This is intentionally small: modules should call `get_logger(name)`.
    """
    level = getattr(logging, log_level.upper(), logging.INFO)
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(asctime)s] %(levelname)s %(name)s: %(message)s")
    handler.setFormatter(formatter)

    root = logging.getLogger()
    # Avoid adding duplicate handlers when called multiple times
    if not root.handlers:
        root.addHandler(handler)
    root.setLevel(level)

    # Make sure common uvicorn loggers follow the same level
    logging.getLogger("uvicorn.access").setLevel(level)
    logging.getLogger("uvicorn.error").setLevel(level)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
