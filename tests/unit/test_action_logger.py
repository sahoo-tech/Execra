import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch, MagicMock
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
        guidance_confidence=0.9
    )

def test_undo_last_returns_none_when_empty(logger):
    result = logger.undo_last()
    assert result is None

def test_undo_last_returns_last_action(logger, sample_action):
    logger._stack.append(sample_action)

    result = logger.undo_last()
    assert result == sample_action

def test_undo_last_removes_from_stack(logger, sample_action):
    logger._stack.append(sample_action)
    logger.undo_last()

    assert len(logger._stack) == 0

def test_deque_max_size_is_50(logger, sample_action):
    for i in range(60):
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

        # Verify that an INSERT INTO command was executed
        insert_calls = [call for call in mock_db.execute.call_args_list if "INSERT INTO" in call[0][0]]
        assert len(insert_calls) == 1
        assert mock_db.commit.called


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
async def test_clear_session_calls_sqlite_delete(logger, sample_action):
    with patch("aiosqlite.connect") as mock_connect:
        mock_db = AsyncMock()
        mock_connect.return_value.__aenter__.return_value = mock_db

        await logger.clear_session("sess_001")

        # Verify that a DELETE FROM command was executed
        delete_calls = [call for call in mock_db.execute.call_args_list if "DELETE FROM" in call[0][0]]
        assert len(delete_calls) == 1
        assert mock_db.commit.called

@pytest.mark.asyncio
async def test_get_history_returns_list(logger):
    with patch("aiosqlite.connect") as mock_connect:
        mock_db = AsyncMock()
        mock_cursor = AsyncMock()

        mock_cursor.fetchall.return_value = [
            ("act_001", "sess_001", "2026-04-14T10:00:00", "code_edit",
             "Test action", "digital", 1, 0.9)
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