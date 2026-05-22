import pytest
import aiosqlite
from core.intelligence.context_engine import ContextEngine


@pytest.mark.asyncio
async def test_create_session_returns_uuid(tmp_path):
    """create_session should return a valid UUID string."""
    db_file = tmp_path / "test.db"
    engine = ContextEngine(db_path=str(db_file))

    session_id = await engine.create_session("digital")

    assert isinstance(session_id, str)
    assert len(session_id) == 36   # UUID length with dashes


@pytest.mark.asyncio
async def test_step_description_is_encrypted_in_sqlite(tmp_path):
    """The step_description column should not contain plaintext."""
    db_file = tmp_path / "test.db"
    engine = ContextEngine(db_path=str(db_file))

    session_id = await engine.create_session("digital")
    await engine.update_step(session_id, 4, "Fix the null check on line 42")

    # Read raw value from SQLite 
    async with aiosqlite.connect(str(db_file)) as db:
        cursor = await db.execute(
            "SELECT step_description FROM session_context WHERE session_id = ?",
            (session_id,)
        )
        row = await cursor.fetchone()

    raw = row[0]
    assert "null check" not in raw
    assert "line 42" not in raw


@pytest.mark.asyncio
async def test_get_context_decrypts_description(tmp_path):
    """get_context should transparently decrypt the description."""
    db_file = tmp_path / "test.db"
    engine = ContextEngine(db_path=str(db_file))

    session_id = await engine.create_session("digital")
    await engine.update_step(session_id, 4, "Fix the null check on line 42")

    ctx = await engine.get_context(session_id)

    assert ctx["session_id"] == session_id
    assert ctx["current_step"] == 4
    assert ctx["step_description"] == "Fix the null check on line 42"
    assert ctx["domain"] == "digital"


@pytest.mark.asyncio
async def test_get_context_returns_none_for_unknown_session(tmp_path):
    """get_context should return None when session does not exist."""
    db_file = tmp_path / "test.db"
    engine = ContextEngine(db_path=str(db_file))

    await engine.create_session("digital")

    result = await engine.get_context("nonexistent-session-id")
    assert result is None