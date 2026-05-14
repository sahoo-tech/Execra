class ExecraError(Exception):
    """Base class for all Execra SDK errors."""
    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code

class ExecraConnectionError(ExecraError):
    """Raised when the Execra instance is unreachable."""
    pass

class ExecraAuthError(ExecraError):
    """Raised when the API returns 401 Unauthorized or 403 Forbidden."""
    pass
