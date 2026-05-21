from typing import Optional, Dict, Any
from core.errors.error_codes import ErrorCode


class ExecraError(Exception):
    def __init__(
        self,
        error_code: ErrorCode,
        message: str,
        context: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.error_code = error_code
        self.message = message
        self.context = context or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": "error",
            "code": self.error_code.value,
            "message": self.message,
            "context": self.context,
        }

    def __str__(self) -> str:
        return f"[{self.error_code.value}] {self.message}"