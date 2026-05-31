"""Unit tests for core/hybrid/action_logger.py.

Covers the full persistence lifecycle — including the restart-survival
regression for issue #268 (undone actions reappearing after restart).

All tests that interact with SQLite use a temporary file path provided
by the ``db_path`` fixture so that tests are fully isolated from each
other and from any production database.
"""

import aiosqlite
import pytest

from core.hybrid.action_logger import ActionLogger, ActionRecord

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def db_path(tmp_path):
    """Return a per-test temporary SQLite database path."""
    return str(tmp_path / "test_actions.db")


# ---------------------------------------------------------------------------
# record_action
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_record_action_adds_action_to_history(db_path):
    logger = ActionLogger(db_path=db_path)
    action = ActionRecord(type="click", description="Clicked run button")

    await logger.record_action(action)

    assert logger.total_actions() == 1
    assert logger.list_actions() == [action]


@pytest.mark.asyncio
async def test_record_action_persists_to_database(db_path):
    logger = ActionLogger(db_path=db_path)
    action = ActionRecord(type="click", description="DB persistence check")

    await logger.record_action(action)

    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM action_log WHERE id = ?", (action.id,))
        row = await cursor.fetchone()

    assert row is not None
    assert row["description"] == "DB persistence check"
    assert bool(row["undone"]) is False


# ---------------------------------------------------------------------------
# undo_last
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_undo_last_marks_latest_undoable_action(db_path):
    logger = ActionLogger(db_path=db_path)
    first_action = ActionRecord(
        type="edit",
        description="Changed a field",
        is_undoable=True,
        undo_instruction="Restore previous value",
    )
    second_action = ActionRecord(type="view", description="Opened settings")

    await logger.record_action(first_action)
    await logger.record_action(second_action)

    undone = await logger.undo_last()

    assert undone == first_action
    assert first_action.undone is True


@pytest.mark.asyncio
async def test_undo_last_skips_non_undoable_actions(db_path):
    logger = ActionLogger(db_path=db_path)
    non_undoable = ActionRecord(type="view", description="Just a view")
    undoable = ActionRecord(type="edit", description="An edit", is_undoable=True)

    await logger.record_action(non_undoable)
    await logger.record_action(undoable)

    result = await logger.undo_last()
    assert result == undoable


@pytest.mark.asyncio
async def test_double_undo_returns_none_when_no_undoable_action_remains(db_path):
    logger = ActionLogger(db_path=db_path)
    action = ActionRecord(
        type="edit",
        description="Changed a field",
        is_undoable=True,
        undo_instruction="Restore previous value",
    )

    await logger.record_action(action)

    assert await logger.undo_last() == action
    assert await logger.undo_last() is None


@pytest.mark.asyncio
async def test_undo_last_updates_undone_column_in_database(db_path):
    """undo_last() must write undone=1 to the database, not just in memory."""
    logger = ActionLogger(db_path=db_path)
    action = ActionRecord(
        type="edit",
        description="Something undoable",
        is_undoable=True,
    )
    await logger.record_action(action)
    await logger.undo_last()

    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT undone FROM action_log WHERE id = ?", (action.id,)
        )
        row = await cursor.fetchone()

    assert row is not None
    assert bool(row["undone"]) is True


# ---------------------------------------------------------------------------
# Restart survival — regression tests for issue #268
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_undo_state_survives_restart(db_path):
    """Undone actions must not reappear as undoable after a process restart.

    Regression test for issue #268: previously, undo_last() only updated
    the in-memory object.  On restart the in-memory state was lost and the
    action became undoable again.
    """
    # --- First process lifetime ---
    logger_first = ActionLogger(db_path=db_path)
    action = ActionRecord(
        type="edit",
        description="Changed a critical setting",
        is_undoable=True,
        undo_instruction="Restore original value",
    )
    await logger_first.record_action(action)
    undone = await logger_first.undo_last()
    assert undone is not None
    assert undone.undone is True

    # --- Simulate restart: brand-new ActionLogger against the same DB ---
    logger_second = ActionLogger(db_path=db_path)
    await logger_second.load()

    assert logger_second.total_actions() == 1
    restored = logger_second.list_actions()[0]
    assert restored.id == action.id
    assert (
        restored.undone is True
    ), "Undo state was lost after restart — undone action reappeared as undoable"

    second_undo = await logger_second.undo_last()
    assert (
        second_undo is None
    ), "Previously undone action became undoable again after restart"


@pytest.mark.asyncio
async def test_multiple_undos_survive_restart(db_path):
    """All undo operations performed before a restart must remain in effect."""
    logger_a = ActionLogger(db_path=db_path)

    actions = [
        ActionRecord(type="edit", description=f"Action {i}", is_undoable=True)
        for i in range(3)
    ]
    for a in actions:
        await logger_a.record_action(a)

    # Undo the two most recent actions.
    await logger_a.undo_last()
    await logger_a.undo_last()

    undone_before = sum(1 for a in logger_a.list_actions() if a.undone)
    assert undone_before == 2

    # Restart.
    logger_b = ActionLogger(db_path=db_path)
    await logger_b.load()

    undone_after = sum(1 for a in logger_b.list_actions() if a.undone)
    assert (
        undone_after == 2
    ), f"Expected 2 undone actions after restart, got {undone_after}"

    # Only one undoable action should remain.
    assert await logger_b.undo_last() is not None
    assert await logger_b.undo_last() is None


@pytest.mark.asyncio
async def test_load_restores_all_actions_with_correct_fields(db_path):
    """load() must reconstruct every field of every ActionRecord from the DB."""
    logger_a = ActionLogger(db_path=db_path)
    original = ActionRecord(
        type="code_edit",
        description="Fixed null check",
        domain="digital",
        session_id="s1",
        was_guided=True,
        guidance_confidence=0.95,
        is_undoable=True,
        undo_instruction="Revert null check",
    )
    await logger_a.record_action(original)

    logger_b = ActionLogger(db_path=db_path)
    await logger_b.load()

    assert logger_b.total_actions() == 1
    restored = logger_b.list_actions()[0]
    assert restored.id == original.id
    assert restored.type == original.type
    assert restored.description == original.description
    assert restored.session_id == original.session_id
    assert restored.was_guided is True
    assert restored.guidance_confidence == pytest.approx(0.95)
    assert restored.is_undoable is True
    assert restored.undo_instruction == original.undo_instruction
    assert restored.undone is False


@pytest.mark.asyncio
async def test_non_undone_actions_remain_undoable_after_restart(db_path):
    """Actions that were NOT undone must still be undoable after restart."""
    logger_a = ActionLogger(db_path=db_path)
    action = ActionRecord(type="edit", description="Pending undo", is_undoable=True)
    await logger_a.record_action(action)
    # Do NOT undo — action should survive restart as undoable.

    logger_b = ActionLogger(db_path=db_path)
    await logger_b.load()

    result = await logger_b.undo_last()
    assert result is not None
    assert result.id == action.id


# ---------------------------------------------------------------------------
# In-memory / database synchronisation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_memory_and_database_stay_in_sync_after_undo(db_path):
    """After undo_last(), in-memory object and database row must both show undone=True."""
    logger = ActionLogger(db_path=db_path)
    action = ActionRecord(type="edit", description="Sync check", is_undoable=True)
    await logger.record_action(action)
    await logger.undo_last()

    # In-memory
    assert logger.list_actions()[0].undone is True

    # Database
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT undone FROM action_log WHERE id = ?", (action.id,)
        )
        row = await cursor.fetchone()
    assert bool(row["undone"]) is True


# ---------------------------------------------------------------------------
# replay_session
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_replay_session_excludes_undone_actions(db_path):
    """Replay must not include actions that have been undone."""
    logger = ActionLogger(db_path=db_path)
    kept = ActionRecord(type="step", description="Keep this", session_id="s1")
    reverted = ActionRecord(
        type="edit",
        description="Revert this",
        session_id="s1",
        is_undoable=True,
    )
    await logger.record_action(kept)
    await logger.record_action(reverted)
    await logger.undo_last()

    replayed = [a async for a in logger.replay_session(session_id="s1")]

    assert replayed == [kept]
    assert reverted not in replayed


@pytest.mark.asyncio
async def test_replay_session_yields_matching_session_actions_in_order(db_path):
    logger = ActionLogger(db_path=db_path)
    first_action = ActionRecord(
        type="step", description="First", session_id="session-1"
    )
    second_action = ActionRecord(
        type="step", description="Second", session_id="session-2"
    )
    third_action = ActionRecord(
        type="step", description="Third", session_id="session-1"
    )

    await logger.record_action(first_action)
    await logger.record_action(second_action)
    await logger.record_action(third_action)

    replayed_actions = [
        action async for action in logger.replay_session(session_id="session-1")
    ]

    assert replayed_actions == [first_action, third_action]


@pytest.mark.asyncio
async def test_replay_session_rejects_invalid_speed(db_path):
    logger = ActionLogger(db_path=db_path)

    with pytest.raises(ValueError, match="Replay speed"):
        async for _ in logger.replay_session(speed=0):
            pass


@pytest.mark.asyncio
async def test_replay_session_respects_undone_state_after_restart(db_path):
    """Replay must exclude undone actions even after load() reconstructs state."""
    logger_a = ActionLogger(db_path=db_path)
    kept = ActionRecord(type="step", description="Kept", session_id="s1")
    reverted = ActionRecord(
        type="edit", description="Reverted", session_id="s1", is_undoable=True
    )
    await logger_a.record_action(kept)
    await logger_a.record_action(reverted)
    await logger_a.undo_last()

    logger_b = ActionLogger(db_path=db_path)
    await logger_b.load()

    replayed = [a async for a in logger_b.replay_session(session_id="s1")]
    assert len(replayed) == 1
    assert replayed[0].description == "Kept"


# ---------------------------------------------------------------------------
# clear_session
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_clear_session_removes_actions_from_memory_and_db(db_path):
    logger = ActionLogger(db_path=db_path)
    await logger.record_action(
        ActionRecord(type="click", description="A", session_id="s1")
    )
    await logger.record_action(
        ActionRecord(type="click", description="B", session_id="s2")
    )

    await logger.clear_session("s1")

    assert all(a.session_id != "s1" for a in logger.list_actions())
    assert any(a.session_id == "s2" for a in logger.list_actions())

    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute(
            "SELECT COUNT(*) FROM action_log WHERE session_id = ?", ("s1",)
        )
        count = (await cursor.fetchone())[0]
    assert count == 0
