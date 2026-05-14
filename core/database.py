"""
core/database.py

Async SQLite database initializer for Execra.

Sets up all required tables on startup and provides a reusable async
connection context manager used by the context engine and action logger.

Usage:
    # In api/main.py startup event:
    from core.database import init_db
    await init_db()

    # In any module that needs a DB connection:
    from core.database import get_db_connection
    async with get_db_connection() as db:
        await db.execute("SELECT ...")
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

import aiosqlite

logger = logging.getLogger(__name__)

# Default path for the SQLite database file.
# Override by passing db_path to init_db() or get_db_connection().
DEFAULT_DB_PATH = "execra.db"


# ---------------------------------------------------------------------------
# Table creation SQL
# ---------------------------------------------------------------------------

_CREATE_SESSION_CONTEXT = """
CREATE TABLE IF NOT EXISTS session_context (
    session_id      TEXT PRIMARY KEY,
    task_type       TEXT NOT NULL,
    current_step    INTEGER NOT NULL DEFAULT 0,
    total_steps     INTEGER NOT NULL DEFAULT 1,
    step_description TEXT NOT NULL DEFAULT '',
    domain          TEXT NOT NULL,
    started_at      TEXT NOT NULL
);
"""

_CREATE_ERROR_HISTORY = """
CREATE TABLE IF NOT EXISTS error_history (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id  TEXT NOT NULL,
    step        INTEGER NOT NULL,
    error       TEXT NOT NULL,
    resolved    INTEGER NOT NULL DEFAULT 0,
    logged_at   TEXT NOT NULL,
    FOREIGN KEY (session_id) REFERENCES session_context(session_id)
);
"""

_CREATE_ACTION_LOG = """
CREATE TABLE IF NOT EXISTS action_log (
    id                  TEXT PRIMARY KEY,
    session_id          TEXT NOT NULL,
    timestamp           TEXT NOT NULL,
    type                TEXT NOT NULL,
    description         TEXT NOT NULL,
    domain              TEXT NOT NULL,
    was_guided          INTEGER NOT NULL DEFAULT 0,
    guidance_confidence REAL,
    FOREIGN KEY (session_id) REFERENCES session_context(session_id)
);
"""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def init_db(db_path: str = DEFAULT_DB_PATH) -> None:
    """
    Create all required Execra tables in the SQLite database if they do
    not already exist.

    This function is safe to call multiple times — it uses
    ``CREATE TABLE IF NOT EXISTS`` for all tables.

    Args:
        db_path: Path to the SQLite database file.
                 Defaults to ``execra.db`` in the working directory.
                 Pass ``":memory:"`` for an in-memory database (useful in tests).
    """
    logger.info("Initializing database at: %s", db_path)

    async with aiosqlite.connect(db_path) as db:
        # Enable WAL mode for better concurrent read performance
        await db.execute("PRAGMA journal_mode=WAL;")

        await db.execute(_CREATE_SESSION_CONTEXT)
        logger.debug("Table 'session_context' ready.")

        await db.execute(_CREATE_ERROR_HISTORY)
        logger.debug("Table 'error_history' ready.")

        await db.execute(_CREATE_ACTION_LOG)
        logger.debug("Table 'action_log' ready.")

        await db.commit()

    logger.info("Database initialization complete.")


@asynccontextmanager
async def get_db_connection(
    db_path: str = DEFAULT_DB_PATH,
) -> AsyncIterator[aiosqlite.Connection]:
    """
    Async context manager that yields an open ``aiosqlite.Connection``.

    Automatically closes the connection when the context exits.

    Args:
        db_path: Path to the SQLite database file.
                 Defaults to ``execra.db`` in the working directory.

    Yields:
        aiosqlite.Connection: An open, ready-to-use database connection.

    Example::

        async with get_db_connection() as db:
            cursor = await db.execute("SELECT * FROM session_context")
            rows = await cursor.fetchall()
    """
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row  # return dict-like rows
        yield db
