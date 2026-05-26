import pytest
import aiosqlite
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from core.intelligence.session_summarizer import SessionSummarizer, SessionSummary
from core.hybrid.action_logger import ActionRecord
from api.main import app
from core.security.crypto import encrypt

client = TestClient(app)

import tempfile

@pytest.fixture
async def setup_db():
    db_path = tempfile.mktemp(suffix=".db")
    # Initialize the tables and some synthetic data
    async with aiosqlite.connect(db_path) as db:
        await db.execute("""
            CREATE TABLE action_log (
                id TEXT PRIMARY KEY,
                session_id TEXT,
                timestamp TEXT,
                type TEXT,
                description TEXT,
                domain TEXT,
                was_guided INTEGER,
                guidance_confidence REAL
            )
        """)
        await db.execute("""
            CREATE TABLE error_history (
                id TEXT PRIMARY KEY,
                session_id TEXT,
                step INTEGER,
                error TEXT
            )
        """)
        
        # Insert actions
        actions = [
            ("act_1", "test_sess_1", "2026-05-26T10:00:00+00:00", "click", "Clicked button", "digital", 0, None),
            ("act_2", "test_sess_1", "2026-05-26T10:00:05+00:00", "type", "Typed text", "digital", 1, 0.8),
            ("act_3", "test_sess_1", "2026-05-26T10:00:10+00:00", "scroll", "Scrolled page", "digital", 1, 0.9)
        ]
        await db.executemany("INSERT INTO action_log VALUES (?, ?, ?, ?, ?, ?, ?, ?)", actions)
        
        # Insert errors
        errors = [
            ("err_1", "test_sess_1", 1, "enc_NetworkError: connection timeout"),
            ("err_2", "test_sess_1", 2, "enc_NetworkError: connection refused"),
            ("err_3", "test_sess_1", 3, "enc_ValueError: invalid literal")
        ]
        await db.executemany("INSERT INTO error_history VALUES (?, ?, ?, ?)", errors)
        
        await db.commit()
        
    return db_path

@pytest.mark.asyncio
async def test_session_summarizer_logic(setup_db, monkeypatch):
    monkeypatch.setattr("core.intelligence.session_summarizer.decrypt", lambda x: x.replace("enc_", ""))
    db_path = setup_db
    summarizer = SessionSummarizer(db_path=db_path)
    summary = await summarizer.summarize("test_sess_1")
    
    assert summary.session_id == "test_sess_1"
    assert summary.total_steps == 3
    assert summary.steps_completed == 3
    assert summary.duration_seconds == 10.0  # 10:00:00 to 10:00:10
    assert summary.total_guidance_delivered == 2
    assert summary.avg_confidence == 0.85  # (0.8 + 0.9) / 2
    assert summary.errors_detected == 3
    assert summary.most_common_error_type == "NetworkError"

def test_api_summary_json():
    from unittest.mock import AsyncMock
    import api.routes.session
    
    mock_summary = SessionSummary(
        session_id="mock_sess",
        duration_seconds=42.0,
        total_steps=10,
        steps_completed=10,
        errors_detected=2,
        errors_resolved=0,
        total_guidance_delivered=5,
        avg_confidence=0.9,
        most_common_error_type="SyntaxError",
        task_type="unknown",
        generated_at="2026-05-26T10:00:00+00:00"
    )
    api.routes.session.summarizer.summarize = AsyncMock(return_value=mock_summary)
    
    response = client.get("/api/v1/session/mock_sess/summary")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["session_id"] == "mock_sess"
    assert data["avg_confidence"] == 0.9
    assert data["total_steps"] == 10

def test_api_summary_markdown():
    from unittest.mock import AsyncMock
    import api.routes.session
    
    mock_summary = SessionSummary(
        session_id="mock_sess",
        duration_seconds=42.0,
        total_steps=10,
        steps_completed=10,
        errors_detected=2,
        errors_resolved=0,
        total_guidance_delivered=5,
        avg_confidence=0.9,
        most_common_error_type="SyntaxError",
        task_type="unknown",
        generated_at="2026-05-26T10:00:00+00:00"
    )
    api.routes.session.summarizer.summarize = AsyncMock(return_value=mock_summary)
    
    response = client.get("/api/v1/session/mock_sess/summary.md")
    assert response.status_code == 200
    assert "Session Summary Report: mock_sess" in response.text
    assert "**Average Guidance Confidence:** 0.9" in response.text
