"""
core/schemas.py

Pydantic request and response schemas for all Execra API endpoints
that accept user input (POST, PUT, query parameters).

These schemas enforce strict input validation at the API boundary.
FastAPI uses them automatically to:
    - Validate incoming request bodies and query parameters.
    - Return 422 errors with details when validation fails.
    - Generate accurate OpenAPI / Swagger documentation.

All field constraints (allowed values, ranges, lengths) are derived
from docs/api_reference.md.
"""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# System Endpoints
# ---------------------------------------------------------------------------

class SystemRestartRequest(BaseModel):
    """Request body for ``POST /api/v1/system/restart``."""

    clear_session: bool = Field(
        True,
        description="Whether to clear the current session context on restart.",
    )


class SystemRestartResponse(BaseModel):
    """Response body for ``POST /api/v1/system/restart``."""

    message: str = Field(..., description="Human-readable status message.")
    session_cleared: bool = Field(
        ..., description="Whether the session was cleared."
    )


# ---------------------------------------------------------------------------
# Mode Endpoints
# ---------------------------------------------------------------------------

class ModeUpdateRequest(BaseModel):
    """Request body for ``PUT /api/v1/mode``."""

    mode: Literal["passive", "active", "mixed"] = Field(
        ...,
        description=(
            'Target interaction mode. Must be one of: '
            '"passive", "active", or "mixed".'
        ),
    )


class ModeResponse(BaseModel):
    """Response body for ``GET /api/v1/mode`` and ``PUT /api/v1/mode``."""

    mode: Literal["passive", "active", "mixed"] = Field(
        ..., description="The current interaction mode."
    )
    description: Optional[str] = Field(
        None, description="Human-readable description of the current mode."
    )
    message: Optional[str] = Field(
        None, description="Confirmation message after a mode switch."
    )


# ---------------------------------------------------------------------------
# Guidance Endpoints
# ---------------------------------------------------------------------------

class GuidanceAskRequest(BaseModel):
    """Request body for ``POST /api/v1/guidance/ask``."""

    question: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description=(
            "The user's question in Active Mode. "
            "Must be a non-empty string (max 2000 characters)."
        ),
    )


class GuidanceAskResponse(BaseModel):
    """Response body for ``POST /api/v1/guidance/ask``."""

    answer: str = Field(..., description="Execra's answer to the question.")
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence score (0.0–1.0)."
    )
    source: list[str] = Field(
        ..., description='Signal sources, e.g. ["llm", "execution_trace"].'
    )
    reasoning: str = Field(
        ..., description="Explanation of how the answer was derived."
    )
    follow_up_suggestion: Optional[str] = Field(
        None, description="Optional follow-up suggestion for the user."
    )


# ---------------------------------------------------------------------------
# Action Log Endpoints
# ---------------------------------------------------------------------------

class ActionsQueryParams(BaseModel):
    """
    Validated query parameters for ``GET /api/v1/actions``.

    Usage in a route::

        @router.get("/actions")
        async def get_actions(params: ActionsQueryParams = Depends()):
            ...
    """

    limit: int = Field(
        20,
        ge=1,
        le=100,
        description="Maximum number of actions to return (1–100).",
    )
    offset: int = Field(
        0,
        ge=0,
        description="Pagination offset (must be >= 0).",
    )


class UndoActionResponse(BaseModel):
    """Response body for ``POST /api/v1/actions/undo``."""

    message: str = Field(
        ..., description="Human-readable confirmation message."
    )
    action_undone: Optional[dict] = Field(
        None,
        description=(
            "Details of the action that was undone "
            '(contains "id" and "description").'
        ),
    )


# ---------------------------------------------------------------------------
# Context Endpoints
# ---------------------------------------------------------------------------

class ContextDeleteResponse(BaseModel):
    """Response body for ``DELETE /api/v1/context``."""

    message: str = Field(
        ..., description="Confirmation that the session context was cleared."
    )


# ---------------------------------------------------------------------------
# Status Response
# ---------------------------------------------------------------------------

class StatusResponse(BaseModel):
    """Response body for ``GET /api/v1/status``."""

    status: Literal["running", "idle", "error"] = Field(
        ..., description="Current system status."
    )
    version: str = Field(..., description="Execra version string.")
    uptime_seconds: int = Field(
        ..., ge=0, description="Seconds since last startup."
    )
    active_domain: Literal["digital", "physical", "hybrid"] = Field(
        ..., description="Currently active execution domain."
    )
    active_mode: Literal["passive", "active", "mixed"] = Field(
        ..., description="Currently active interaction mode."
    )
    perception_fps: int = Field(
        ..., ge=0, description="Current screen/camera capture rate."
    )
    llm_backend: str = Field(
        ..., description="Active LLM provider name."
    )
