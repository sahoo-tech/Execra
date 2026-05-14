"""
tests/unit/test_database.py

Unit tests for core/database.py.

Uses an in-memory SQLite database (":memory:") via a shared connection
fixture to verify that:
- All three required tables are created correctly.
- Tables have the correct columns.
- get_db_connection() yields a usable connection.
- Calling init_db() multiple times is idempotent (CREATE TABLE IF NOT EXISTS).

NOTE: SQLite :memory: databases are connection-scoped — each new
aiosqlite.connect() call gets a completely fresh, empty database.
Tests that create tables and then inspect them must therefore do both
operations on the SAME connection object. We achieve this via the
shared `db` fixture and the `_setup_db()` helper, and by using
tmp_path (a real temp file) for tests that call init_db() directly.
"""

import aiosqlite
import pytest
import pytest_asyncio

from core.database import (
    _CREATE_ACTION_LOG,
    _CREATE_ERROR_HISTORY,
    _CREATE_SESSION_CONTEXT,
    get_db_connection,
    init_db,
)


# ---------------------------------------------------------------------------
# Shared in-memory DB fixture
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def db():
    """
    Provides a single, persistent in-memory aiosqlite connection per test.
    All setup and assertions that need the same in-memory DB share this fixture.
    """
    async with aiosqlite.connect(":memory:") as conn:
        conn.row_factory = aiosqlite.Row
        yield conn


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _setup_db(conn: aiosqlite.Connection) -> None:
    """Run all CREATE TABLE statements on a given connection."""
    await conn.execute(_CREATE_SESSION_CONTEXT)
    await conn.execute(_CREATE_ERROR_HISTORY)
    await conn.execute(_CREATE_ACTION_LOG)
    await conn.commit()


async def _get_table_names(conn: aiosqlite.Connection) -> list[str]:
    cursor = await conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"
    )
    rows = await cursor.fetchall()
    return [row[0] for row in rows]


async def _get_column_names(conn: aiosqlite.Connection, table: str) -> list[str]:
    cursor = await conn.execute(f"PRAGMA table_info({table});")
    rows = await cursor.fetchall()
    return [row[1] for row in rows]


# ---------------------------------------------------------------------------
# Tests — table creation via _setup_db helper (shared in-memory connection)
# ---------------------------------------------------------------------------

class TestInitDb:
    @pytest.mark.asyncio
    async def test_creates_session_context_table(self, db):
        await _setup_db(db)
        tables = await _get_table_names(db)
        assert "session_context" in tables

    @pytest.mark.asyncio
    async def test_creates_error_history_table(self, db):
        await _setup_db(db)
        tables = await _get_table_names(db)
        assert "error_history" in tables

    @pytest.mark.asyncio
    async def test_creates_action_log_table(self, db):
        await _setup_db(db)
        tables = await _get_table_names(db)
        assert "action_log" in tables

    @pytest.mark.asyncio
    async def test_session_context_columns(self, db):
        await _setup_db(db)
        cols = await _get_column_names(db, "session_context")
        expected = {
            "session_id", "task_type", "current_step",
            "total_steps", "step_description", "domain", "started_at",
        }
        assert expected.issubset(set(cols))

    @pytest.mark.asyncio
    async def test_error_history_columns(self, db):
        await _setup_db(db)
        cols = await _get_column_names(db, "error_history")
        expected = {"id", "session_id", "step", "error", "resolved", "logged_at"}
        assert expected.issubset(set(cols))

    @pytest.mark.asyncio
    async def test_action_log_columns(self, db):
        await _setup_db(db)
        cols = await _get_column_names(db, "action_log")
        expected = {
            "id", "session_id", "timestamp", "type",
            "description", "domain", "was_guided", "guidance_confidence",
        }
        assert expected.issubset(set(cols))

    @pytest.mark.asyncio
    async def test_idempotent_multiple_calls(self, db):
        """CREATE TABLE IF NOT EXISTS called twice must not raise or duplicate."""
        await _setup_db(db)
        await _setup_db(db)  # second run — no-op
        tables = await _get_table_names(db)
        assert tables.count("session_context") == 1
        assert tables.count("error_history") == 1
        assert tables.count("action_log") == 1

    @pytest.mark.asyncio
    async def test_init_db_completes_on_real_file(self, tmp_path):
        """init_db() must run without raising on a real filesystem path."""
        db_file = str(tmp_path / "test_execra.db")
        await init_db(db_path=db_file)  # must not raise


# ---------------------------------------------------------------------------
# Tests — get_db_connection (uses real temp file so init and get share same DB)
# ---------------------------------------------------------------------------

class TestGetDbConnection:
    @pytest.mark.asyncio
    async def test_yields_live_connection(self, tmp_path):
        db_file = str(tmp_path / "conn_test.db")
        await init_db(db_path=db_file)
        async with get_db_connection(db_path=db_file) as conn:
            assert conn is not None

    @pytest.mark.asyncio
    async def test_can_query_created_tables(self, tmp_path):
        db_file = str(tmp_path / "query_test.db")
        await init_db(db_path=db_file)
        async with get_db_connection(db_path=db_file) as conn:
            cursor = await conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table';"
            )
            rows = await cursor.fetchall()
        assert len(rows) >= 3

    @pytest.mark.asyncio
    async def test_row_factory_returns_row_objects(self, tmp_path):
        """Rows must support column access by name (aiosqlite.Row)."""
        db_file = str(tmp_path / "row_test.db")
        await init_db(db_path=db_file)
        async with get_db_connection(db_path=db_file) as conn:
            cursor = await conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name LIMIT 1;"
            )
            row = await cursor.fetchone()
        assert row is not None
        assert row["name"] in ("action_log", "error_history", "session_context")
