"""
tests/unit/test_models.py

Unit tests for core/models.py.

Covers:
- Correct instantiation of every model with valid data.
- ValidationError raised when required fields are missing.
- Type and constraint enforcement (field validators, Literal values, ranges).
"""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from core.models import (
    ActionRecord,
    Detection,
    ErrorRecord,
    GuidanceInstruction,
    Outcome,
    SessionContext,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

NOW = datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Detection
# ---------------------------------------------------------------------------

class TestDetection:
    def test_valid_instantiation(self):
        d = Detection(label="screwdriver", confidence=0.91, bounding_box=[10, 20, 100, 200])
        assert d.label == "screwdriver"
        assert d.confidence == 0.91
        assert d.bounding_box == [10, 20, 100, 200]

    def test_missing_label_raises(self):
        with pytest.raises(ValidationError):
            Detection(confidence=0.5, bounding_box=[0, 0, 50, 50])

    def test_missing_confidence_raises(self):
        with pytest.raises(ValidationError):
            Detection(label="bowl", bounding_box=[0, 0, 50, 50])

    def test_missing_bounding_box_raises(self):
        with pytest.raises(ValidationError):
            Detection(label="bowl", confidence=0.7)

    def test_confidence_above_one_raises(self):
        with pytest.raises(ValidationError):
            Detection(label="bowl", confidence=1.5, bounding_box=[0, 0, 50, 50])

    def test_confidence_below_zero_raises(self):
        with pytest.raises(ValidationError):
            Detection(label="bowl", confidence=-0.1, bounding_box=[0, 0, 50, 50])


# ---------------------------------------------------------------------------
# ErrorRecord
# ---------------------------------------------------------------------------

class TestErrorRecord:
    def test_valid_instantiation(self):
        e = ErrorRecord(step=2, error="NullPointerException on line 42", resolved=False)
        assert e.step == 2
        assert e.resolved is False

    def test_resolved_defaults_to_false(self):
        e = ErrorRecord(step=0, error="some error")
        assert e.resolved is False

    def test_missing_step_raises(self):
        with pytest.raises(ValidationError):
            ErrorRecord(error="missing step")

    def test_missing_error_raises(self):
        with pytest.raises(ValidationError):
            ErrorRecord(step=1)

    def test_negative_step_raises(self):
        with pytest.raises(ValidationError):
            ErrorRecord(step=-1, error="bad step")


# ---------------------------------------------------------------------------
# ActionRecord
# ---------------------------------------------------------------------------

class TestActionRecord:
    def _valid(self, **kwargs):
        defaults = dict(
            id="act_001",
            timestamp=NOW,
            type="code_edit",
            description="Modified line 42",
            domain="digital",
            was_guided=True,
            guidance_confidence=0.87,
        )
        defaults.update(kwargs)
        return ActionRecord(**defaults)

    def test_valid_instantiation(self):
        a = self._valid()
        assert a.id == "act_001"
        assert a.domain == "digital"

    def test_guidance_confidence_nullable(self):
        a = self._valid(guidance_confidence=None)
        assert a.guidance_confidence is None

    def test_invalid_domain_raises(self):
        with pytest.raises(ValidationError):
            self._valid(domain="cloud")

    def test_missing_id_raises(self):
        with pytest.raises(ValidationError):
            ActionRecord(
                timestamp=NOW, type="code_edit",
                description="x", domain="digital", was_guided=False,
            )

    def test_guidance_confidence_out_of_range_raises(self):
        with pytest.raises(ValidationError):
            self._valid(guidance_confidence=1.5)


# ---------------------------------------------------------------------------
# Outcome
# ---------------------------------------------------------------------------

class TestOutcome:
    def test_valid_critical(self):
        o = Outcome(description="Infinite loop", probability=0.95, severity="critical")
        assert o.severity == "critical"

    def test_valid_warning(self):
        o = Outcome(description="Off-by-one", probability=0.6, severity="warning")
        assert o.severity == "warning"

    def test_valid_info(self):
        o = Outcome(description="File opened without context manager", probability=0.3, severity="info")
        assert o.severity == "info"

    def test_invalid_severity_raises(self):
        with pytest.raises(ValidationError):
            Outcome(description="x", probability=0.5, severity="low")

    def test_missing_description_raises(self):
        with pytest.raises(ValidationError):
            Outcome(probability=0.5, severity="info")

    def test_probability_out_of_range_raises(self):
        with pytest.raises(ValidationError):
            Outcome(description="x", probability=2.0, severity="info")


# ---------------------------------------------------------------------------
# GuidanceInstruction
# ---------------------------------------------------------------------------

class TestGuidanceInstruction:
    def _valid(self, **kwargs):
        defaults = dict(
            instruction="Add a null check before line 42.",
            confidence=0.87,
            source=["llm", "rule_engine"],
            reasoning="config is None in 3 paths.",
            mode="safe",
            step=4,
            total_steps=9,
            generated_at=NOW,
        )
        defaults.update(kwargs)
        return GuidanceInstruction(**defaults)

    def test_valid_instantiation(self):
        g = self._valid()
        assert g.mode == "safe"
        assert g.step == 4

    def test_expert_mode_valid(self):
        g = self._valid(mode="expert")
        assert g.mode == "expert"

    def test_invalid_mode_raises(self):
        with pytest.raises(ValidationError):
            self._valid(mode="debug")

    def test_confidence_out_of_range_raises(self):
        with pytest.raises(ValidationError):
            self._valid(confidence=1.1)

    def test_missing_instruction_raises(self):
        with pytest.raises(ValidationError):
            GuidanceInstruction(
                confidence=0.9, source=["llm"], reasoning="x",
                mode="safe", step=1, total_steps=5, generated_at=NOW,
            )

    def test_total_steps_zero_raises(self):
        with pytest.raises(ValidationError):
            self._valid(total_steps=0)


# ---------------------------------------------------------------------------
# SessionContext
# ---------------------------------------------------------------------------

class TestSessionContext:
    def _valid(self, **kwargs):
        defaults = dict(
            session_id="sess-uuid-1234",
            task_type="code_debugging",
            current_step=2,
            total_steps=7,
            step_description="Add null check to config loader",
            error_history=[],
            domain="digital",
            started_at=NOW,
        )
        defaults.update(kwargs)
        return SessionContext(**defaults)

    def test_valid_instantiation(self):
        s = self._valid()
        assert s.session_id == "sess-uuid-1234"
        assert s.domain == "digital"

    def test_error_history_defaults_empty(self):
        s = self._valid()
        assert s.error_history == []

    def test_error_history_with_records(self):
        err = ErrorRecord(step=1, error="TypeError", resolved=False)
        s = self._valid(error_history=[err])
        assert len(s.error_history) == 1

    def test_invalid_domain_raises(self):
        with pytest.raises(ValidationError):
            self._valid(domain="remote")

    def test_physical_domain_valid(self):
        s = self._valid(domain="physical")
        assert s.domain == "physical"

    def test_hybrid_domain_valid(self):
        s = self._valid(domain="hybrid")
        assert s.domain == "hybrid"

    def test_missing_session_id_raises(self):
        with pytest.raises(ValidationError):
            SessionContext(
                task_type="cooking", current_step=0, total_steps=5,
                step_description="start", domain="physical", started_at=NOW,
            )

    def test_total_steps_zero_raises(self):
        with pytest.raises(ValidationError):
            self._valid(total_steps=0)
