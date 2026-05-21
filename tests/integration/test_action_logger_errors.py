import pytest
import aiosqlite
from core.hybrid.action_logger import ActionLogger


@pytest.mark.asyncio
async def test_log_error_encrypts_in_sqlite(tmp_path):
    """The error field stored in SQLite should not be plaintext."""
    db_file = tmp_path / "test.db"
    logger = ActionLogger(db_path=str(db_file))

    await logger.log_error("sess_001", step=1, error="IndexError: list index out of range")

    # Read the raw value directly from SQLite 
    async with aiosqlite.connect(str(db_file)) as db:
        cursor = await db.execute("SELECT error FROM error_history")
        row = await cursor.fetchone()

    raw = row[0]
    assert "IndexError" not in raw
    assert "list index" not in raw


@pytest.mark.asyncio
async def test_get_errors_returns_decrypted(tmp_path):
    """get_errors should transparently decrypt error messages."""
    db_file = tmp_path / "test.db"
    logger = ActionLogger(db_path=str(db_file))

    await logger.log_error("sess_001", step=1, error="IndexError: list index out of range")
    await logger.log_error("sess_001", step=2, error="NameError: x not defined")

    errors = await logger.get_errors("sess_001")

    assert len(errors) == 2
    assert errors[0]["error"] == "IndexError: list index out of range"
    assert errors[1]["error"] == "NameError: x not defined"


@pytest.mark.asyncio
async def test_get_errors_ordered_by_step(tmp_path):
    """Errors should be returned in step order."""
    db_file = tmp_path / "test.db"
    logger = ActionLogger(db_path=str(db_file))

    # Insert out of order
    await logger.log_error("sess_001", step=5, error="error 5")
    await logger.log_error("sess_001", step=1, error="error 1")
    await logger.log_error("sess_001", step=3, error="error 3")

    errors = await logger.get_errors("sess_001")

    assert [e["step"] for e in errors] == [1, 3, 5]


@pytest.mark.asyncio
async def test_get_errors_empty_when_no_errors(tmp_path):
    """get_errors should return empty list if no errors exist for a session."""
    db_file = tmp_path / "test.db"
    logger = ActionLogger(db_path=str(db_file))

    errors = await logger.get_errors("nonexistent-session")

    assert errors == []


@pytest.mark.asyncio
async def test_get_errors_only_for_specified_session(tmp_path):
    """get_errors should only return errors for the requested session."""
    db_file = tmp_path / "test.db"
    logger = ActionLogger(db_path=str(db_file))

    await logger.log_error("sess_001", step=1, error="error A")
    await logger.log_error("sess_002", step=1, error="error B")
    await logger.log_error("sess_001", step=2, error="error C")

    sess_001_errors = await logger.get_errors("sess_001")
    sess_002_errors = await logger.get_errors("sess_002")

    assert len(sess_001_errors) == 2
    assert len(sess_002_errors) == 1
    assert sess_002_errors[0]["error"] == "error B"