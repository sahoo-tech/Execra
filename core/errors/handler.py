from typing import Any, Dict
from core.errors.exceptions import ExecraError
from core.errors.error_codes import ErrorCode
from core.logger import logger


def handle_exception(e: Exception) -> Dict[str, Any]:
    # If it's our custom error
    if isinstance(e, ExecraError):
        logger.error(f"[{e.error_code.value}] {e.message} | Context: {e.context}")
        return e.to_dict()

    # Unknown/unhandled error
    logger.exception(f"[{ErrorCode.UNKNOWN_ERROR.value}] {str(e)}")

    return {
        "status": "error",
        "code": ErrorCode.UNKNOWN_ERROR.value,
        "message": "An unexpected error occurred",
    }