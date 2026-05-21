import pytest
import time
from datetime import datetime
from core.hybrid.alert_suppressor import AlertSuppressor
from core.models import GuidanceInstruction


@pytest.fixture
def suppressor():
    """Fresh suppressor with short cooldowns for testing."""
    return AlertSuppressor(cooldown_map={
        "info": 1,        
        "warning": 1,
        "critical": 0
    })


@pytest.fixture
def sample_instruction():
    """Sample GuidanceInstruction for testing."""
    return GuidanceInstruction(
        instruction="Add null check on line 42",
        confidence=0.9,
        source=["llm"],
        reasoning="test",
        mode="safe",
        step=1,
        total_steps=5,
        generated_at=datetime.now()
    )



# Cooldown behavior
def test_same_instruction_within_cooldown_is_suppressed(suppressor, sample_instruction):
    """Same instruction repeated within cooldown should be suppressed."""
    assert suppressor.should_suppress(sample_instruction, "info") is False
    assert suppressor.should_suppress(sample_instruction, "info") is True


def test_same_instruction_after_cooldown_is_not_suppressed(suppressor, sample_instruction):
    """Same instruction after the cooldown expires should NOT be suppressed."""
    suppressor.should_suppress(sample_instruction, "info")  # records it

    # Wait longer than the cooldown 
    time.sleep(1.1)

    assert suppressor.should_suppress(sample_instruction, "info") is False


def test_different_instructions_not_suppressed(suppressor, sample_instruction):
    """Different instructions should be tracked independently."""
    other_instruction = GuidanceInstruction(
        instruction="Different instruction text",
        confidence=0.9,
        source=["llm"],
        reasoning="test",
        mode="safe",
        step=1,
        total_steps=5,
        generated_at=datetime.now()
    )

    suppressor.should_suppress(sample_instruction, "info")
    assert suppressor.should_suppress(other_instruction, "info") is False


def test_same_text_different_mode_not_suppressed(suppressor, sample_instruction):
    """Same text but different mode should NOT collide."""
    other_mode = GuidanceInstruction(
        instruction="Add null check on line 42",
        confidence=0.9,
        source=["llm"],
        reasoning="test",
        mode="expert",   # different mode
        step=1,
        total_steps=5,
        generated_at=datetime.now()
    )

    suppressor.should_suppress(sample_instruction, "info")   # mode="safe"
    assert suppressor.should_suppress(other_mode, "info") is False



# Critical severity bypasses suppression

def test_critical_severity_never_suppressed(suppressor, sample_instruction):
    """Critical severity should never be suppressed, even when repeated."""
    assert suppressor.should_suppress(sample_instruction, "critical") is False
    assert suppressor.should_suppress(sample_instruction, "critical") is False
    assert suppressor.should_suppress(sample_instruction, "critical") is False


def test_critical_passes_even_after_info_suppression(suppressor, sample_instruction):
    """Critical alerts pass through even if same text was previously suppressed at info level."""
    suppressor.should_suppress(sample_instruction, "info")
    assert suppressor.should_suppress(sample_instruction, "info") is True
    assert suppressor.should_suppress(sample_instruction, "critical") is False


# LRU eviction
def test_lru_eviction_when_max_size_exceeded(suppressor):
    """When map exceeds MAX_SIZE, oldest entry should be evicted."""
    # Override MAX_SIZE for faster testing
    suppressor.MAX_SIZE = 3

    instructions = []
    for i in range(5):
        instructions.append(GuidanceInstruction(
            instruction=f"Instruction number {i}",
            confidence=0.9,
            source=["llm"],
            reasoning="test",
            mode="safe",
            step=1,
            total_steps=5,
            generated_at=datetime.now()
        ))

    # Record 5 unique instructions (max size = 3)
    for inst in instructions:
        suppressor.should_suppress(inst, "info")

    # Map should never exceed MAX_SIZE
    assert len(suppressor._suppression_map) == 3


# Reset functionality

def test_reset_clears_specific_instruction(suppressor, sample_instruction):
    """reset() should clear a specific instruction's suppression record."""
    suppressor.should_suppress(sample_instruction, "info")
    assert suppressor.should_suppress(sample_instruction, "info") is True

    # Reset and try again
    suppressor.reset(sample_instruction.instruction)
    assert suppressor.should_suppress(sample_instruction, "info") is False


# Stats tracking

def test_stats_count_suppressed_correctly(suppressor, sample_instruction):
    """Stats should accurately count suppressed instructions."""
    # First call — not suppressed
    suppressor.should_suppress(sample_instruction, "info")

    # 3 more calls — all suppressed
    suppressor.should_suppress(sample_instruction, "info")
    suppressor.should_suppress(sample_instruction, "info")
    suppressor.should_suppress(sample_instruction, "info")

    stats = suppressor.get_suppression_stats()
    assert stats["total_suppressed"] == 3
    assert stats["by_severity"]["info"] == 3


def test_stats_track_severity_breakdown(suppressor, sample_instruction):
    """Stats should track suppression counts by severity."""
    # info suppressions
    suppressor.should_suppress(sample_instruction, "info")
    suppressor.should_suppress(sample_instruction, "info")  # suppressed

    # warning suppressions (different instruction so it gets recorded)
    other = GuidanceInstruction(
        instruction="Different warning",
        confidence=0.9,
        source=["llm"],
        reasoning="test",
        mode="safe",
        step=1,
        total_steps=5,
        generated_at=datetime.now()
    )
    suppressor.should_suppress(other, "warning")
    suppressor.should_suppress(other, "warning")  # suppressed

    stats = suppressor.get_suppression_stats()
    assert stats["by_severity"]["info"] == 1
    assert stats["by_severity"]["warning"] == 1