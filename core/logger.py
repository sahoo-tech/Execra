import json
import logging
import sys
import traceback
from datetime import datetime
from logging.handlers import RotatingFileHandler
from typing import Optional


class JSONFormatter(logging.Formatter):
    """
    Custom logging formatter that outputs log records as structured JSON strings.
    Extracts dynamic context fields seamlessly.
    """

    def format(self, record: logging.LogRecord) -> str:
        # Standardize timestamp to ISO-8601 format
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "module": record.name,
            "message": record.getMessage(),
        }

        # Dynamically append any extra payload context keys passed by the developer
        # Filtering out python's default internal LogRecord attributes
        DEFAULT_ATTRS = {
            "name", "msg", "args", "levelname", "levelno", "pathname", "filename",
            "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName",
            "created", "msecs", "relativeCreated", "thread", "threadName",
            "processName", "process"
        }
        
        for key, value in record.__dict__.items():
            if key not in DEFAULT_ATTRS:
                log_data[key] = value

        # Format exception tracebacks elegantly if an error runtime event occurs
        if record.exc_info:
            log_data["exception"] = "".join(traceback.format_exception(*record.exc_info))

        return json.dumps(log_data)


def get_logger(
    name: str = "execra",
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 5,
    json_format: bool = True,  # Defaulting to True to meet Feature Request #232 spec
) -> logging.Logger:
    """
    Configures and returns a thread-safe, module-isolated logger instance.
    Prevents duplicate handler bubbling and standardizes output tracking format.
    """
    level = getattr(logging, log_level.upper(), logging.INFO)
    logger = logging.getLogger(name)

    # Prevent re-adding handlers if logger is already configured
    if logger.hasHandlers():
        return logger

    logger.setLevel(level)
    logger.propagate = False  # Isolate stream formats cleanly

    # Resolve Formatter Selection
    if json_format:
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)s %(name)s: %(message)s", 
            datefmt="%Y-%m-%dT%H:%M:%S"
        )

    # 1. Standard System Output (Console Stream)
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    # 2. Add File Persistence (Rotating File Engine)
    if log_file:
        file_handler = RotatingFileHandler(
            log_file, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


# Default initialization hook matching execution environment requirements
logger = get_logger("execra")