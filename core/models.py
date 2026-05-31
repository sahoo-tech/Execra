"""
core/models.py

Central Pydantic data models shared across the Execra API, WebSocket layer,
and all core processing modules.

All models use Pydantic v2 for automatic validation and type enforcement.
Refer to docs/api_reference.md for the full field specifications.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Detection — YOLO object detection result
# ---------------------------------------------------------------------------

class Detection(BaseModel):
    """Represents a single object detected by YOLOv8 in a camera frame."""

    label: str = Field(..., description="Class label of the detected object, e.g. 'screwdriver'")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detection confidence score (0.0–1.0)")
    bounding_box: list[int] = Field(
        ...,
        min_length=4,
        max_length=4,
        description="Bounding box as [x_min, y_min, x_max, y_max] in pixel coordinates",
    )


# ---------------------------------------------------------------------------
# ErrorRecord — a single logged error entry in a session
# ---------------------------------------------------------------------------

class ErrorRecord(BaseModel):
    """Represents one error that occurred during a guided session."""

    step: int = Field(..., ge=0, description="Session step number at which the error was logged")
    error: str = Field(..., description="Human-readable error description")
    resolved: bool = Field(False, description="Whether this error has been resolved")


# ---------------------------------------------------------------------------
# ActionRecord — a single user action entry in the action log
# ---------------------------------------------------------------------------

class ActionRecord(BaseModel):
    """Represents one user action recorded in the session action log."""

    id: str = Field(..., description="Unique action identifier, e.g. 'act_001'")
    timestamp: datetime = Field(..., description="UTC timestamp when the action occurred")
    type: str = Field(..., description="Action type, e.g. 'code_edit', 'key_press'")
    description: str = Field(..., description="Human-readable description of the action")
    domain: Literal["digital", "physical"] = Field(
        ..., description="Execution domain in which the action took place"
    )
    was_guided: bool = Field(..., description="Whether this action was performed under Execra guidance")
    guidance_confidence: float | None = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Confidence of the guidance that preceded this action, if any",
    )


# ---------------------------------------------------------------------------
# Outcome — consequence simulation result
# ---------------------------------------------------------------------------

class Outcome(BaseModel):
    """Represents one predicted outcome from the Consequence Simulation Engine."""

    description: str = Field(..., description="Human-readable description of the predicted outcome")
    probability: float = Field(..., ge=0.0, le=1.0, description="Estimated probability (0.0–1.0)")
    severity: Literal["info", "warning", "critical"] = Field(
        ..., description="Severity level of this outcome"
    )


# ---------------------------------------------------------------------------
# GuidanceInstruction — full guidance output delivered to the user
# ---------------------------------------------------------------------------

class GuidanceInstruction(BaseModel):
    """
    The complete guidance payload produced by the Intelligence Core and
    delivered to the user via the WebSocket or REST API.
    """

    instruction: str = Field(..., description="Human-readable guidance text shown to the user")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Overall trust score (0.0–1.0)")
    source: list[str] = Field(
        ...,
        description="Contributing signal sources, e.g. ['llm', 'rule_engine', 'execution_trace']",
    )
    reasoning: str = Field(..., description="Explanation of why this guidance was generated")
    mode: Literal["safe", "expert"] = Field(..., description="Guidance delivery mode")
    step: int = Field(..., ge=0, description="Current task step number")
    total_steps: int = Field(..., ge=1, description="Total number of steps in the task model")
    generated_at: datetime = Field(..., description="UTC timestamp when the instruction was generated")


# ---------------------------------------------------------------------------
# SessionContext — the full state of an active Execra session
# ---------------------------------------------------------------------------

class SessionContext(BaseModel):
    """
    Tracks the complete state of one Execra session — the task, current step,
    error history, and metadata. Persisted to SQLite via the context engine.
    """

    session_id: str = Field(..., description="Unique session identifier (UUID)")
    task_type: str = Field(
        ..., description="Detected task category, e.g. 'code_debugging', 'cooking'"
    )
    current_step: int = Field(..., ge=0, description="Index of the step the user is currently on")
    total_steps: int = Field(..., ge=1, description="Total steps decomposed for this task")
    step_description: str = Field(..., description="Description of the current step")
    error_history: list[ErrorRecord] = Field(
        default_factory=list, description="All errors logged during this session"
    )
    domain: Literal["digital", "physical", "hybrid"] = Field(
        ..., description="Active execution domain"
    )
    started_at: datetime = Field(..., description="UTC timestamp when this session began")
