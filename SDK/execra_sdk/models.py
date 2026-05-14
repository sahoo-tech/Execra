from datetime import datetime
from typing import List, Optional, Literal
from pydantic import BaseModel, Field

class GuidanceInstruction(BaseModel):
    """Model for a guidance instruction from Execra."""
    instruction: str
    confidence: float = Field(ge=0.0, le=1.0)
    source: List[str]
    reasoning: str
    mode: Literal["autonomous", "manual", "coding", "idle"]
    step: int
    total_steps: int
    generated_at: datetime

class AskResponse(BaseModel):
    """Model for the response to an 'ask' request."""
    answer: str
    confidence: float = Field(ge=0.0, le=1.0)
    source: List[str]
    reasoning: str
    follow_up_suggestion: Optional[str] = None

class ErrorRecord(BaseModel):
    """Model for an error record in a session."""
    step: int
    error: str
    resolved: bool

class SessionContext(BaseModel):
    """Model for the current session context."""
    session_id: str
    task_type: str
    current_step: int
    total_steps: int
    step_description: str
    error_history: List[ErrorRecord]
    domain: str
    started_at: datetime

class ActionRecord(BaseModel):
    """Model for a recorded action."""
    id: str
    timestamp: datetime
    type: str  # Can be Literal if known actions are defined
    description: str
    domain: str
    was_guided: bool
    guidance_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)

class StatusResponse(BaseModel):
    """Model for the system status response."""
    status: str
    version: str
    uptime_seconds: int
    active_domain: str
    active_mode: str
    perception_fps: int
    llm_backend: str

class ModeResponse(BaseModel):
    """Model for the mode switch response."""
    mode: str
    description: Optional[str] = None
    message: Optional[str] = None
