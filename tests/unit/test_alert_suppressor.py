import time
import pytest
from core.hybrid.alert_suppressor import AlertSuppressor, MAX_SUPPRESSION_ENTRIES


class MockInstruction:
    def __init__(self, instruction: str, mode: str = "passive", severity: str = "info"):
        self.instruction = instruction
        self.mode = mode
        self.severity = severity


@pytest.fixture
def suppressor():
    return AlertSuppressor(cooldown_map={"info": 60, "warning": 30, "critical": 0})


@pytest.fixture
def short_cooldown_suppressor():
    """Suppressor with very short cooldown for expiry tests."""
    return AlertSuppressor(cooldown_map={"info": 1, "warning": 1, "critical": 0})


# ─── Basic suppression ───────────────────────────────────────────────────────

def test_first_instruction_is_not_suppressed(suppressor):
    instruction = MockInstruction("Add null check before line 42")
    assert suppressor.should_suppress(instruction) is False


def test_same_instruction_within_cooldown_is_suppressed(suppressor):
    instruction = MockInstruction("Add null check before line 42")
    suppressor.should_suppress(instruction)  # first delivery — not suppressed
    assert suppressor.should_suppress(instruction) is True


def test_different_instruction_is_not_suppressed(suppressor):
    first = MockInstruction("Add null check before line 42")
    second = MockInstruction("Save your file before running")
    suppressor.should_suppress(first)
    assert suppressor.should_suppress(second) is False


def test_same_text_different_mode_is_not_suppressed(suppressor):
    passive = MockInstruction("Add null check", mode="passive")
    active = MockInstruction("Add null check", mode="active")
    suppressor.should_suppress(passive)
    assert suppressor.should_suppress(active) is False


# ─── Cooldown expiry ─────────────────────────────────────────────────────────

def test_same_instruction_after_cooldown_is_not_suppressed(short_cooldown_suppressor):
    instruction = MockInstruction("Check your loop condition")
    short_cooldown_suppressor.should_suppress(instruction)
    time.sleep(1.1)  # wait for cooldown to expire
    assert short_cooldown_suppressor.should_suppress(instruction) is False


# ─── Critical severity ───────────────────────────────────────────────────────

def test_critical_instruction_is_never_suppressed(suppressor):
    instruction = MockInstruction("STOP — critical error detected", severity="critical")
    suppressor.should_suppress(instruction)  # first
    assert suppressor.should_suppress(instruction) is False  # second — still not suppressed


def test_critical_always_passes_regardless_of_cooldown():
    suppressor = AlertSuppressor(cooldown_map={"critical": 0})
    instruction = MockInstruction("Critical failure", severity="critical")
    for _ in range(5):
        assert suppressor.should_suppress(instruction) is False


# ─── Reset ───────────────────────────────────────────────────────────────────

def test_reset_clears_suppression_record(suppressor):
    instruction = MockInstruction("Add null check before line 42", mode="passive")
    suppressor.should_suppress(instruction)  # record it
    assert suppressor.should_suppress(instruction) is True  # suppressed

    suppressor.reset("Add null check before line 42")
    assert suppressor.should_suppress(instruction) is False  # cleared


# ─── Stats ───────────────────────────────────────────────────────────────────

def test_suppression_stats_initial_state(suppressor):
    stats = suppressor.get_suppression_stats()
    assert stats["total_suppressed"] == 0
    assert stats["by_severity"] == {}


def test_suppression_stats_increment_on_suppress(suppressor):
    instruction = MockInstruction("Add null check", severity="info")
    suppressor.should_suppress(instruction)  # not suppressed
    suppressor.should_suppress(instruction)  # suppressed
    suppressor.should_suppress(instruction)  # suppressed

    stats = suppressor.get_suppression_stats()
    assert stats["total_suppressed"] == 2
    assert stats["by_severity"]["info"] == 2


def test_suppression_stats_track_by_severity(suppressor):
    info_inst = MockInstruction("Info message", severity="info")
    warn_inst = MockInstruction("Warning message", severity="warning")

    suppressor.should_suppress(info_inst)
    suppressor.should_suppress(info_inst)  # suppressed
    suppressor.should_suppress(warn_inst)
    suppressor.should_suppress(warn_inst)  # suppressed

    stats = suppressor.get_suppression_stats()
    assert stats["by_severity"]["info"] == 1
    assert stats["by_severity"]["warning"] == 1


# ─── LRU eviction ────────────────────────────────────────────────────────────

def test_lru_eviction_on_overflow():
    suppressor = AlertSuppressor(cooldown_map={"info": 60})

    # Fill up to max + 1
    for i in range(MAX_SUPPRESSION_ENTRIES + 1):
        inst = MockInstruction(f"Instruction number {i}", mode="passive")
        suppressor.should_suppress(inst)

    assert len(suppressor._suppression_map) == MAX_SUPPRESSION_ENTRIES


def test_oldest_entry_evicted_first():
    suppressor = AlertSuppressor(cooldown_map={"info": 60})

    first = MockInstruction("First instruction ever", mode="passive")
    suppressor.should_suppress(first)
    first_key = suppressor._make_key(first)

    # Fill up beyond max
    for i in range(MAX_SUPPRESSION_ENTRIES):
        inst = MockInstruction(f"Filler instruction {i}", mode="passive")
        suppressor.should_suppress(inst)

    # First entry should have been evicted
    assert first_key not in suppressor._suppression_map