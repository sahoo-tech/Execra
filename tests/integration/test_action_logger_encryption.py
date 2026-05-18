import pytest
import aiosqlite
from datetime import datetime
from core.hybrid.action_logger import ActionLogger, ActionRecord


@pytest.fixture
def sample_action():
    return ActionRecord(
        id="act_enc_001",
        session_id="sess_enc_001",
        timestamp=datetime.now(),
        type="code_edit",
        description="Modified line 42 in main.py",
        domain="digital",
        was_guided=True,
        guidance_confidence=0.9
    )

@pytest.mark.asyncio
async def test_description_is_encrypted_in_sqlite(sample_action, tmp_path):
    """Verify the description stored in SQLite is NOT plaintext."""

    db_file = tmp_path / "test.db"
    logger = ActionLogger(db_path=str(db_file))

    await logger.log_action(sample_action)

    async with aiosqlite.connect(str(db_file)) as db:
        cursor = await db.execute("SELECT description FROM action_log")
        row = await cursor.fetchone()

    raw_description = row[0]

    assert "Modified line 42" not in raw_description
    assert raw_description != sample_action.description

@pytest.mark.asyncio
async def test_get_history_returns_decrypted_description(sample_action, tmp_path):
    """get_history should transparently decrypt descriptions."""
    db_file = tmp_path / "test.db"
    logger = ActionLogger(db_path=str(db_file))

    await logger.log_action(sample_action)
    history = await logger.get_history()

    assert len(history) == 1
    assert history[0].description == "Modified line 42 in main.py"