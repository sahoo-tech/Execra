"""Unit tests for core/hybrid/action_logger.py.

Covers the full persistence lifecycle — including the restart-survival
regression for issue #268 (undone actions reappearing after restart).

Upstream tests (``_stack``-based, mocked aiosqlite) are preserved
alongside the new persistence tests.  All tests that interact with a real
SQLite database use the ``db_path`` fixture (backed by ``tmp_path``) so
that each test gets an isolated, temporary database file.
"""

from datetime import datetime
from unittest.mock import AsyncMock, patch

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


@pytest.fixture
def logger():
    """In-memory ActionLogger for upstream-style tests."""
    return ActionLogger(db_path=":memory:")


@pytest.fixture
def sample_action():
    return ActionRecord(
        id="act_001",
        session_id="sess_001",
        timestamp=datetime.now(),
        type="code_edit",
        description="Test action",
        domain="digital",
        was_guided=True,
        guidance_confidence=0.9,
    )


# ---------------------------------------------------------------------------
# Upstream-style tests (deque / mocked SQLite)
# ---------------------------------------------------------------------------


def test_deque_max_size_is_50(logger, sample_action):
    for _ in range(60):
        logger._stack.append(sample_action)
    assert len(logger._stack) == 50


@pytest.mark.asyncio
async def test_log_action_appends_to_deque(logger, sample_action):
    with patch("aiosqlite.connect") as mock_connect:
        mock_db = AsyncMock()
        mock_connect.return_value.__aenter__.return_value = mock_db
        await logger.log_action(sample_action)
        assert len(logger._stack) == 1
        assert logger._stack[0] == sample_action


@pytest.mark.asyncio
async def test_log_action_calls_sqlite_insert(logger, sample_action):
    with patch("aiosqlite.connect") as mock_connect:
        mock_db = AsyncMock()
        mock_connect.return_value.__aenter__.return_value = mock_db
        await logger.log_action(sample_action)
        insert_calls = [
            c
            for c in mock_db.execute.call_args_list
            if "INSERT INTO" in (c[0][0] if c[0] else "")
        ]
        assert len(insert_calls) == 1
        assert mock_db.commit.called


@pytest.mark.asyncio
async def test_clear_session_clears_deque(logger, sample_action):
    with patch("aiosqlite.connect") as mock_connect:
        mock_db = AsyncMock()
        mock_connect.return_value.__aenter__.return_value = mock_db
        logger._stack.append(sample_action)
        logger._stack.append(sample_action)
        logger._actions = [sample_action, sample_action]
        await logger.clear_session("sess_001")
        assert len(logger._stack) == 0


@pytest.mark.asyncio
async def test_clear_session_calls_sqlite_delete(logger, sample_action):
    with patch("aiosqlite.connect") as mock_connect:
        mock_db = AsyncMock()
        mock_connect.return_value.__aenter__.return_value = mock_db
        await logger.clear_session("sess_001")
        delete_calls = [
            c
            for c in mock_db.execute.call_args_list
            if "DELETE FROM" in (c[0][0] if c[0] else "")
        ]
        assert len(delete_calls) == 1
        assert mock_db.commit.called


@pytest.mark.asyncio
async def test_get_history_passes_pagination(logger):
    with patch("aiosqlite.connect") as mock_connect:
        mock_db = AsyncMock()
        mock_cursor = AsyncMock()
        mock_cursor.fetchall.return_value = []
        mock_db.execute.return_value = mock_cursor
        mock_connect.return_value.__aenter__.return_value = mock_db

        await logger.get_history(limit=5, offset=10)

        pagination_calls = [
            c
            for c in mock_db.execute.call_args_list
            if c[0] and "LIMIT" in c[0][0] and c[0][1] == (5, 10)
        ]
        assert len(pagination_calls) == 1


# ---------------------------------------------------------------------------
# Persistence tests (real SQLite via tmp_path)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_log_action_adds_action_to_history(db_path):
    lg = ActionLogger(db_path=db_path)
    action = ActionRecord(type="click", description="Clicked run button")

    await lg.log_action(action)

    assert lg.total_actions() == 1
    assert lg.list_actions() == [action]


@pytest.mark.asyncio
async def test_log_action_persists_to_database(db_path):
    lg = ActionLogger(db_path=db_path)
    action = ActionRecord(type="click", description="DB persistence check")

    await lg.log_action(action)

    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM action_log WHERE id = ?", (action.id,)
        )
        row = await cursor.fetchone()

    assert row is not None
    assert row["description"] == "DB persistence check"
    assert bool(row["undone"]) is False


@pytest.mark.asyncio
async def test_undo_last_marks_latest_undoable_action(db_path):
    lg = ActionLogger(db_path=db_path)
    first_action = ActionRecord(
        type="edit",
        description="Changed a field",
        is_undoable=True,
        undo_instruction="Restore previous value",
    )
    second_action = ActionRecord(type="view", description="Opened settings")

    await lg.log_action(first_action)
    await lg.log_action(second_action)

    undone = await lg.undo_last()

    assert undone == first_action
    assert first_action.undone is True


@pytest.mark.asyncio
async def test_double_undo_returns_none_when_no_undoable_action_remains(db_path):
    lg = ActionLogger(db_path=db_path)
    action = ActionRecord(
        type="edit",
        description="Changed a field",
        is_undoable=True,
    )
    await lg.log_action(action)
    assert await lg.undo_last() == action
    assert await lg.undo_last() is None


@pytest.mark.asyncio
async def test_undo_last_updates_undone_column_in_database(db_path):
    """undo_last() must write undone=1 to the database, not just in memory."""
    lg = ActionLogger(db_path=db_path)
    action = ActionRecord(
        type="edit", description="Something undoable", is_undoable=True
    )
    await lg.log_action(action)
    await lg.undo_last()

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
    # First process lifetime
    lg_first = ActionLogger(db_path=db_path)
    action = ActionRecord(
        type="edit",
        description="Changed a critical setting",
        is_undoable=True,
        undo_instruction="Restore original value",
    )
    await lg_first.log_action(action)
    undone = await lg_first.undo_last()
    assert undone is not None
    assert undone.undone is True

    # Simulate restart: brand-new ActionLogger against the same DB
    lg_second = ActionLogger(db_path=db_path)
    await lg_second.load()

    assert lg_second.total_actions() == 1
    restored = lg_second.list_actions()[0]
    assert restored.id == action.id
    assert restored.undone is True, (
        "Undo state was lost after restart — undone action reappeared as undoable"
    )

    second_undo = await lg_second.undo_last()
    assert second_undo is None, (
        "Previously undone action became undoable again after restart"
    )


@pytest.mark.asyncio
async def test_multiple_undos_survive_restart(db_path):
    """All undo operations performed before a restart must remain in effect."""
    lg_a = ActionLogger(db_path=db_path)

    actions = [
        ActionRecord(type="edit", description=f"Action {i}", is_undoable=True)
        for i in range(3)
    ]
    for a in actions:
        await lg_a.log_action(a)

    await lg_a.undo_last()
    await lg_a.undo_last()

    undone_before = sum(1 for a in lg_a.list_actions() if a.undone)
    assert undone_before == 2

    lg_b = ActionLogger(db_path=db_path)
    await lg_b.load()

    undone_after = sum(1 for a in lg_b.list_actions() if a.undone)
    assert undone_after == 2, (
        f"Expected 2 undone actions after restart, got {undone_after}"
    )

    assert await lg_b.undo_last() is not None
    assert await lg_b.undo_last() is None


@pytest.mark.asyncio
async def test_load_restores_all_actions_with_correct_fields(db_path):
    """load() must reconstruct every field of every ActionRecord from the DB."""
    lg_a = ActionLogger(db_path=db_path)
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
    await lg_a.log_action(original)

    lg_b = ActionLogger(db_path=db_path)
    await lg_b.load()

    assert lg_b.total_actions() == 1
    restored = lg_b.list_actions()[0]
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
    lg_a = ActionLogger(db_path=db_path)
    action = ActionRecord(type="edit", description="Pending undo", is_undoable=True)
    await lg_a.log_action(action)

    lg_b = ActionLogger(db_path=db_path)
    await lg_b.load()

    result = await lg_b.undo_last()
    assert result is not None
    assert result.id == action.id


# ---------------------------------------------------------------------------
# In-memory / database synchronisation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_memory_and_database_stay_in_sync_after_undo(db_path):
    lg = ActionLogger(db_path=db_path)
    action = ActionRecord(type="edit", description="Sync check", is_undoable=True)
    await lg.log_action(action)
    await lg.undo_last()

    assert lg.list_actions()[0].undone is True

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
    lg = ActionLogger(db_path=db_path)
    kept = ActionRecord(type="step", description="Keep this", session_id="s1")
    reverted = ActionRecord(
        type="edit",
        description="Revert this",
        session_id="s1",
        is_undoable=True,
    )
    await lg.log_action(kept)
    await lg.log_action(reverted)
    await lg.undo_last()

    replayed = [a async for a in lg.replay_session(session_id="s1")]

    assert replayed == [kept]
    assert reverted not in replayed


@pytest.mark.asyncio
async def test_replay_session_yields_matching_session_actions_in_order(db_path):
    lg = ActionLogger(db_path=db_path)
    first_action = ActionRecord(
        type="step", description="First", session_id="session-1"
    )
    second_action = ActionRecord(
        type="step", description="Second", session_id="session-2"
    )
    third_action = ActionRecord(
        type="step", description="Third", session_id="session-1"
    )

    await lg.log_action(first_action)
    await lg.log_action(second_action)
    await lg.log_action(third_action)

    replayed = [a async for a in lg.replay_session(session_id="session-1")]

    assert replayed == [first_action, third_action]


@pytest.mark.asyncio
async def test_replay_session_rejects_invalid_speed(db_path):
    lg = ActionLogger(db_path=db_path)
    with pytest.raises(ValueError, match="Replay speed"):
        async for _ in lg.replay_session(speed=0):
            pass


@pytest.mark.asyncio
async def test_replay_session_respects_undone_state_after_restart(db_path):
    """Replay must exclude undone actions even after load() reconstructs state."""
    lg_a = ActionLogger(db_path=db_path)
    kept = ActionRecord(type="step", description="Kept", session_id="s1")
    reverted = ActionRecord(
        type="edit", description="Reverted", session_id="s1", is_undoable=True
    )
    await lg_a.log_action(kept)
    await lg_a.log_action(reverted)
    await lg_a.undo_last()

    lg_b = ActionLogger(db_path=db_path)
    await lg_b.load()

    replayed = [a async for a in lg_b.replay_session(session_id="s1")]
    assert len(replayed) == 1
    assert replayed[0].description == "Kept"


# ---------------------------------------------------------------------------
# clear_session
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_clear_session_removes_actions_from_memory_and_db(db_path):
    lg = ActionLogger(db_path=db_path)
    await lg.log_action(ActionRecord(type="click", description="A", session_id="s1"))
    await lg.log_action(ActionRecord(type="click", description="B", session_id="s2"))

    await lg.clear_session("s1")

    assert all(a.session_id != "s1" for a in lg.list_actions())
    assert any(a.session_id == "s2" for a in lg.list_actions())

    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute(
            "SELECT COUNT(*) FROM action_log WHERE session_id = ?", ("s1",)
        )
        count = (await cursor.fetchone())[0]
    assert count == 0
