import json
import logging
import traceback
from logging.handlers import RotatingFileHandler
from typing import Optional


class JSONFormatter(logging.Formatter):
    """Custom formatter that outputs log records as JSON strings."""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_data["exception"] = "".join(traceback.format_exception(*record.exc_info))
        return json.dumps(log_data)


def setup(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 5,
    json_format: bool = False,
) -> None:
    """Configure root logging for the application.

    Supports rotating file logs and structured JSON logging.
    """
    level = getattr(logging, log_level.upper(), logging.INFO)
    root = logging.getLogger()

    # Clear existing handlers to prevent duplicates during reconfiguration
    for h in list(root.handlers):
        root.removeHandler(h)

    # Configure formatter
    if json_format:
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter("[%(asctime)s] %(levelname)s %(name)s: %(message)s")

    # Add Stream Handler
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    root.addHandler(stream_handler)

    # Add Rotating File Handler
    if log_file:
        file_handler = RotatingFileHandler(
            log_file, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
        )
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)

    root.setLevel(level)



setup()
logger = logging.getLogger("execra")