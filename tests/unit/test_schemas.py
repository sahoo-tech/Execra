"""
tests/unit/test_schemas.py

Unit tests for core/schemas.py.

Covers:
- Correct instantiation of every request/response schema with valid data.
- ValidationError raised when required fields are missing.
- Field constraints are enforced (Literal values, ranges, lengths).
- Edge cases like empty strings, boundary values, and optional fields.
"""

import pytest
from pydantic import ValidationError

from core.schemas import (
    ActionsQueryParams,
    ContextDeleteResponse,
    GuidanceAskRequest,
    GuidanceAskResponse,
    ModeResponse,
    ModeUpdateRequest,
    StatusResponse,
    SystemRestartRequest,
    SystemRestartResponse,
    UndoActionResponse,
)


# ---------------------------------------------------------------------------
# SystemRestartRequest
# ---------------------------------------------------------------------------

class TestSystemRestartRequest:
    def test_defaults_to_true(self):
        r = SystemRestartRequest()
        assert r.clear_session is True

    def test_explicit_false(self):
        r = SystemRestartRequest(clear_session=False)
        assert r.clear_session is False


# ---------------------------------------------------------------------------
# ModeUpdateRequest
# ---------------------------------------------------------------------------

class TestModeUpdateRequest:
    def test_passive_valid(self):
        r = ModeUpdateRequest(mode="passive")
        assert r.mode == "passive"

    def test_active_valid(self):
        r = ModeUpdateRequest(mode="active")
        assert r.mode == "active"

    def test_mixed_valid(self):
        r = ModeUpdateRequest(mode="mixed")
        assert r.mode == "mixed"

    def test_invalid_mode_raises(self):
        with pytest.raises(ValidationError):
            ModeUpdateRequest(mode="turbo")

    def test_missing_mode_raises(self):
        with pytest.raises(ValidationError):
            ModeUpdateRequest()

    def test_empty_string_raises(self):
        with pytest.raises(ValidationError):
            ModeUpdateRequest(mode="")

    def test_numeric_mode_raises(self):
        with pytest.raises(ValidationError):
            ModeUpdateRequest(mode=123)


# ---------------------------------------------------------------------------
# GuidanceAskRequest
# ---------------------------------------------------------------------------

class TestGuidanceAskRequest:
    def test_valid_question(self):
        r = GuidanceAskRequest(question="What is wrong with line 42?")
        assert r.question == "What is wrong with line 42?"

    def test_missing_question_raises(self):
        with pytest.raises(ValidationError):
            GuidanceAskRequest()

    def test_empty_question_raises(self):
        with pytest.raises(ValidationError):
            GuidanceAskRequest(question="")

    def test_whitespace_only_valid(self):
        # Single space is technically 1 character, so it passes min_length
        r = GuidanceAskRequest(question=" ")
        assert r.question == " "

    def test_max_length_boundary(self):
        # Exactly 2000 characters should be valid
        r = GuidanceAskRequest(question="a" * 2000)
        assert len(r.question) == 2000

    def test_exceeds_max_length_raises(self):
        with pytest.raises(ValidationError):
            GuidanceAskRequest(question="a" * 2001)


# ---------------------------------------------------------------------------
# ActionsQueryParams
# ---------------------------------------------------------------------------

class TestActionsQueryParams:
    def test_defaults(self):
        p = ActionsQueryParams()
        assert p.limit == 20
        assert p.offset == 0

    def test_custom_values(self):
        p = ActionsQueryParams(limit=50, offset=10)
        assert p.limit == 50
        assert p.offset == 10

    def test_limit_min_boundary(self):
        p = ActionsQueryParams(limit=1)
        assert p.limit == 1

    def test_limit_max_boundary(self):
        p = ActionsQueryParams(limit=100)
        assert p.limit == 100

    def test_limit_zero_raises(self):
        with pytest.raises(ValidationError):
            ActionsQueryParams(limit=0)

    def test_limit_exceeds_max_raises(self):
        with pytest.raises(ValidationError):
            ActionsQueryParams(limit=101)

    def test_negative_limit_raises(self):
        with pytest.raises(ValidationError):
            ActionsQueryParams(limit=-5)

    def test_negative_offset_raises(self):
        with pytest.raises(ValidationError):
            ActionsQueryParams(offset=-1)


# ---------------------------------------------------------------------------
# StatusResponse
# ---------------------------------------------------------------------------

class TestStatusResponse:
    def _valid(self, **kwargs):
        defaults = dict(
            status="running",
            version="0.1.0",
            uptime_seconds=3421,
            active_domain="digital",
            active_mode="passive",
            perception_fps=2,
            llm_backend="gpt-4o",
        )
        defaults.update(kwargs)
        return StatusResponse(**defaults)

    def test_valid_instantiation(self):
        s = self._valid()
        assert s.status == "running"

    def test_idle_status_valid(self):
        s = self._valid(status="idle")
        assert s.status == "idle"

    def test_error_status_valid(self):
        s = self._valid(status="error")
        assert s.status == "error"

    def test_invalid_status_raises(self):
        with pytest.raises(ValidationError):
            self._valid(status="booting")

    def test_invalid_domain_raises(self):
        with pytest.raises(ValidationError):
            self._valid(active_domain="cloud")

    def test_invalid_mode_raises(self):
        with pytest.raises(ValidationError):
            self._valid(active_mode="turbo")

    def test_negative_uptime_raises(self):
        with pytest.raises(ValidationError):
            self._valid(uptime_seconds=-1)


# ---------------------------------------------------------------------------
# GuidanceAskResponse
# ---------------------------------------------------------------------------

class TestGuidanceAskResponse:
    def _valid(self, **kwargs):
        defaults = dict(
            answer="The error is caused by a null reference.",
            confidence=0.92,
            source=["llm", "execution_trace"],
            reasoning="Traced from 3 function calls.",
            follow_up_suggestion=None,
        )
        defaults.update(kwargs)
        return GuidanceAskResponse(**defaults)

    def test_valid_instantiation(self):
        r = self._valid()
        assert r.answer is not None

    def test_follow_up_optional(self):
        r = self._valid(follow_up_suggestion="Want to see the fix?")
        assert r.follow_up_suggestion == "Want to see the fix?"

    def test_confidence_out_of_range_raises(self):
        with pytest.raises(ValidationError):
            self._valid(confidence=1.5)

    def test_missing_answer_raises(self):
        with pytest.raises(ValidationError):
            GuidanceAskResponse(
                confidence=0.9, source=["llm"], reasoning="test"
            )


# ---------------------------------------------------------------------------
# ModeResponse
# ---------------------------------------------------------------------------

class TestModeResponse:
    def test_valid_with_description(self):
        r = ModeResponse(mode="passive", description="Observing automatically.")
        assert r.mode == "passive"

    def test_valid_with_message(self):
        r = ModeResponse(mode="active", message="Switched to Active Mode.")
        assert r.message == "Switched to Active Mode."

    def test_optional_fields_default_none(self):
        r = ModeResponse(mode="mixed")
        assert r.description is None
        assert r.message is None

    def test_invalid_mode_raises(self):
        with pytest.raises(ValidationError):
            ModeResponse(mode="debug")


# ---------------------------------------------------------------------------
# Simple Response Schemas
# ---------------------------------------------------------------------------

class TestSystemRestartResponse:
    def test_valid(self):
        r = SystemRestartResponse(
            message="System restarted successfully.", session_cleared=True
        )
        assert r.session_cleared is True


class TestUndoActionResponse:
    def test_valid_with_action(self):
        r = UndoActionResponse(
            message="Last action undone.",
            action_undone={"id": "act_042", "description": "Modified line 42"},
        )
        assert r.action_undone["id"] == "act_042"

    def test_valid_without_action(self):
        r = UndoActionResponse(message="Nothing to undo.", action_undone=None)
        assert r.action_undone is None


class TestContextDeleteResponse:
    def test_valid(self):
        r = ContextDeleteResponse(message="Session context cleared.")
        assert r.message == "Session context cleared."
