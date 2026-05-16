import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch
from core.hybrid.action_logger import ActionLogger, ActionRecord


@pytest.fixture
def logger():
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
        is_undoable=True,
        undo_instruction="Revert the edit",
    )


@pytest.fixture
def non_undoable_action():
    return ActionRecord(
        id="act_002",
        session_id="sess_001",
        timestamp=datetime.now(),
        type="screen_read",
        description="Non-undoable observation",
        domain="digital",
        was_guided=False,
        guidance_confidence=None,
        is_undoable=False,
    )


# ---------------------------------------------------------------------------
# undo_last — basic behaviour
# ---------------------------------------------------------------------------

def test_undo_last_returns_none_when_empty(logger):
    result = logger.undo_last()
    assert result is None


def test_undo_last_returns_last_action(logger, sample_action):
    logger._stack.append(sample_action)

    result = logger.undo_last()
    assert result is not None
    assert result.id == sample_action.id
    assert result.description == sample_action.description


def test_undo_last_marks_action_id_as_undone(logger, sample_action):
    logger._stack.append(sample_action)

    result = logger.undo_last()

    assert result is not None
    assert result.id in logger._undone_ids


def test_undo_last_returns_none_for_non_undoable_action(logger, non_undoable_action):
    logger._stack.append(non_undoable_action)

    result = logger.undo_last()
    assert result is None


# ---------------------------------------------------------------------------
# undo_last — double-undo safety
# ---------------------------------------------------------------------------

def test_double_undo_returns_none_after_first_undo(logger, sample_action):
    logger._stack.append(sample_action)

    first = logger.undo_last()
    second = logger.undo_last()

    assert first is not None
    assert second is None


def test_double_undo_does_not_corrupt_stack(logger, sample_action):
    logger._stack.append(sample_action)

    logger.undo_last()
    logger.undo_last()

    # Stack still holds the original action; idempotent, no corruption.
    assert len(logger._stack) == 1


def test_undo_picks_last_undoable_skipping_non_undoable(logger, sample_action, non_undoable_action):
    """Non-undoable actions on top of the stack are skipped."""
    logger._stack.append(sample_action)
    logger._stack.append(non_undoable_action)

    result = logger.undo_last()

    assert result is not None
    assert result.id == sample_action.id


# ---------------------------------------------------------------------------
# deque size limit
# ---------------------------------------------------------------------------

def test_deque_max_size_is_50(logger, sample_action):
    for _ in range(60):
        logger._stack.append(sample_action)

    assert len(logger._stack) == 50


# ---------------------------------------------------------------------------
# log_action — async with SQLite mock
# ---------------------------------------------------------------------------

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

        # execute is called at least once (INSERT; _init_db may also call it)
        assert mock_db.execute.call_count >= 1
        assert mock_db.commit.call_count >= 1


# ---------------------------------------------------------------------------
# clear_session
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_clear_session_clears_deque(logger, sample_action):
    with patch("aiosqlite.connect") as mock_connect:
        mock_db = AsyncMock()
        mock_connect.return_value.__aenter__.return_value = mock_db

        logger._stack.append(sample_action)
        logger._stack.append(sample_action)

        await logger.clear_session("sess_001")

        assert len(logger._stack) == 0


@pytest.mark.asyncio
async def test_clear_session_clears_undone_ids(logger, sample_action):
    with patch("aiosqlite.connect") as mock_connect:
        mock_db = AsyncMock()
        mock_connect.return_value.__aenter__.return_value = mock_db

        logger._stack.append(sample_action)
        logger.undo_last()
        assert sample_action.id in logger._undone_ids

        await logger.clear_session("sess_001")

        assert len(logger._undone_ids) == 0


@pytest.mark.asyncio
async def test_clear_session_calls_sqlite_delete(logger):
    with patch("aiosqlite.connect") as mock_connect:
        mock_db = AsyncMock()
        mock_connect.return_value.__aenter__.return_value = mock_db

        await logger.clear_session("sess_001")

        mock_db.execute.assert_called()
        mock_db.commit.assert_called()


# ---------------------------------------------------------------------------
# get_history
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_history_returns_list(logger):
    with patch("aiosqlite.connect") as mock_connect:
        mock_db = AsyncMock()
        mock_cursor = AsyncMock()

        mock_cursor.fetchall.return_value = [
            (
                "act_001", "sess_001", "2026-04-14T10:00:00",
                "code_edit", "Test action", "digital", 1, 0.9,
                0, None, 0,
            )
        ]
        mock_db.execute.return_value = mock_cursor
        mock_connect.return_value.__aenter__.return_value = mock_db

        result = await logger.get_history(limit=10, offset=0)

        assert len(result) == 1
        assert isinstance(result[0], ActionRecord)
        assert result[0].id == "act_001"


@pytest.mark.asyncio
async def test_get_history_passes_pagination(logger):
    with patch("aiosqlite.connect") as mock_connect:
        mock_db = AsyncMock()
        mock_cursor = AsyncMock()
        mock_cursor.fetchall.return_value = []
        mock_db.execute.return_value = mock_cursor
        mock_connect.return_value.__aenter__.return_value = mock_db

        await logger.get_history(limit=5, offset=10)

        call_args = mock_db.execute.call_args
        assert call_args[0][1] == (5, 10)


# ---------------------------------------------------------------------------
# replay_session — async generator
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_replay_session_invalid_speed_raises(logger):
    with pytest.raises(ValueError, match="Replay speed must be > 0"):
        async for _ in logger.replay_session("sess_001", speed=0):
            pass

    with pytest.raises(ValueError):
        async for _ in logger.replay_session("sess_001", speed=-1.5):
            pass


@pytest.mark.asyncio
async def test_replay_session_yields_actions_in_order(logger):
    t0 = datetime(2026, 1, 1, 12, 0, 0)
    rows = [
        ("a1", "sess_001", t0.isoformat(), "click", "First", "digital", 0, None, 0, None, 0),
        ("a2", "sess_001", (t0 + timedelta(seconds=1)).isoformat(), "type", "Second", "digital", 0, None, 0, None, 0),
        ("a3", "sess_001", (t0 + timedelta(seconds=2)).isoformat(), "scroll", "Third", "digital", 0, None, 0, None, 0),
    ]

    with patch("aiosqlite.connect") as mock_connect:
        mock_db = AsyncMock()
        mock_cursor = AsyncMock()
        mock_cursor.fetchall.return_value = rows
        mock_db.execute.return_value = mock_cursor
        mock_connect.return_value.__aenter__.return_value = mock_db

        # Use a very high speed so sleep durations are negligible.
        collected = []
        async for action in logger.replay_session("sess_001", speed=1e9):
            collected.append(action)

    assert len(collected) == 3
    assert collected[0].id == "a1"
    assert collected[1].id == "a2"
    assert collected[2].id == "a3"
    # interval is set for actions after the first
    assert collected[0].interval == 0.0
    assert collected[1].interval == pytest.approx(1.0)
    assert collected[2].interval == pytest.approx(1.0)


@pytest.mark.asyncio
async def test_replay_session_does_not_modify_history(logger, sample_action):
    """Replay must not add, remove, or alter actions in the undo stack."""
    logger._stack.append(sample_action)
    stack_len_before = len(logger._stack)

    rows = [
        (
            sample_action.id, sample_action.session_id,
            sample_action.timestamp.isoformat(), sample_action.type,
            sample_action.description, sample_action.domain,
            int(sample_action.was_guided), sample_action.guidance_confidence,
            int(sample_action.is_undoable), sample_action.undo_instruction, 0,
        )
    ]

    with patch("aiosqlite.connect") as mock_connect:
        mock_db = AsyncMock()
        mock_cursor = AsyncMock()
        mock_cursor.fetchall.return_value = rows
        mock_db.execute.return_value = mock_cursor
        mock_connect.return_value.__aenter__.return_value = mock_db

        async for _ in logger.replay_session(sample_action.session_id, speed=1e9):
            pass

    assert len(logger._stack) == stack_len_before
    assert len(logger._undone_ids) == 0
