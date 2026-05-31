"""
core/exceptions.py

Standardized error handling for the Execra API.

Defines a custom exception class and a FastAPI exception handler that
transforms all errors into the project's documented error format::

    {
        "error": {
            "code": "INVALID_MODE",
            "message": "Unknown mode value provided",
            "status": 400
        }
    }

This format is specified in ``docs/api_reference.md`` under Error Handling.

Usage:
    # In any route, raise an ExecraAPIError:
    raise ExecraAPIError(
        code="INVALID_MODE",
        message="Unknown mode value provided.",
        status_code=400,
    )

    # In api/main.py, register the handler:
    from core.exceptions import ExecraAPIError, execra_error_handler
    app.add_exception_handler(ExecraAPIError, execra_error_handler)
"""

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Standardized error response model (for Swagger docs)
# ---------------------------------------------------------------------------

class ErrorDetail(BaseModel):
    """Inner error object matching the Execra API error specification."""

    code: str = Field(..., description="Machine-readable error code.")
    message: str = Field(..., description="Human-readable error message.")
    status: int = Field(..., description="HTTP status code.")


class ErrorResponse(BaseModel):
    """
    Top-level error envelope used by all Execra API error responses.

    Example::

        {
            "error": {
                "code": "CONTEXT_NOT_FOUND",
                "message": "No active session context found.",
                "status": 404
            }
        }
    """

    error: ErrorDetail


# ---------------------------------------------------------------------------
# Custom exception class
# ---------------------------------------------------------------------------

class ExecraAPIError(Exception):
    """
    Raise this in any route to return a standardized Execra error response.

    Args:
        code: Machine-readable error code (e.g. ``"INVALID_MODE"``).
        message: Human-readable error description.
        status_code: HTTP status code to return (default 400).
    """

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
    ) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


# ---------------------------------------------------------------------------
# Exception handlers (register in api/main.py)
# ---------------------------------------------------------------------------

async def execra_error_handler(
    request: Request, exc: ExecraAPIError
) -> JSONResponse:
    """
    Catches ``ExecraAPIError`` and returns the project's standard
    error JSON envelope.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "status": exc.status_code,
            }
        },
    )


async def validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """
    Catches FastAPI's ``RequestValidationError`` (the default 422) and
    transforms it into Execra's standard error format with a 400 status.

    This ensures that Pydantic validation failures are returned in the
    same format as all other API errors, making life easier for frontend
    consumers who only need to handle one error shape.
    """
    # Build a human-readable summary from all validation errors
    errors = exc.errors()
    details = []
    for err in errors:
        loc = " → ".join(str(part) for part in err["loc"])
        details.append(f"{loc}: {err['msg']}")
    message = "; ".join(details)

    return JSONResponse(
        status_code=400,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": message,
                "status": 400,
            }
        },
    )
