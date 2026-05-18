import os
import json
import base64
import sqlite3
import pytest
from pathlib import Path
from datetime import datetime, timezone
from core.security.session_signer import SessionSigner
from core.hybrid.action_logger import ActionRecord

@pytest.fixture
def temp_key_path(tmp_path):
    """Generates a temporary key path for isolated testing."""
    return tmp_path / "test_session.key"

def test_sign_and_verify_valid_record(temp_key_path):
    """Verifies that a valid signed record correctly passes verification."""
    signer = SessionSigner(key_path=str(temp_key_path))
    record = ActionRecord(
        id="act_test_123",
        session_id="sess_abc_456",
        timestamp=datetime.now(timezone.utc),
        type="digital_interaction",
        description="User triggered a test macro execution",
        domain="digital",
        was_guided=False,
        guidance_confidence=0.85
    )
    
    record_dict = json.loads(record.model_dump_json())
    signature = signer.sign(record_dict)
    assert signer.verify(record_dict, signature) is True

def test_tamper_detection(temp_key_path):
    """Verifies that changing any data inside the record causes verification to fail."""
    signer = SessionSigner(key_path=str(temp_key_path))
    record = ActionRecord(
        id="act_test_123",
        session_id="sess_abc_456",
        timestamp=datetime.now(timezone.utc),
        type="digital_interaction",
        description="Original safe instruction",
        domain="digital",
        was_guided=False,
        guidance_confidence=1.0
    )
    
    record_dict = json.loads(record.model_dump_json())
    signature = signer.sign(record_dict)
    
    record_dict["description"] = "Malicious override payload injected"
    
    assert signer.verify(record_dict, signature) is False

def test_session_export_signing(temp_key_path):
    """Verifies that whole session exports get timestamps and valid top-level signatures."""
    signer = SessionSigner(key_path=str(temp_key_path))
    export_payload = {
        "context": {"session_id": "sess_123", "total_steps": 4},
        "history": [{"id": "act_1", "type": "click"}, {"id": "act_2", "type": "type"}]
    }
    
    signed_export = signer.sign_session_export(export_payload)
    
    assert "signature" in signed_export
    assert "signed_at" in signed_export
    assert signer.verify_session_export(signed_export) is True

def test_key_rotation_updates_historical_db(temp_key_path):
    """Verifies that key rotation updates the physical key and successfully re-signs old records."""
    db_path = temp_key_path.parent / "test_execra.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE action_log (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            action TEXT,
            timestamp TEXT,
            signature TEXT
        )
    """)
    
    signer = SessionSigner(key_path=str(temp_key_path))
    initial_key = signer._private_key
    
    record_data = {"user_id": "user_01", "action": "initialize", "timestamp": "2026-05-18T12:00:00"}
    json_str = json.dumps(record_data, sort_keys=True, separators=(',', ':'))
    initial_sig = base64.b64encode(initial_key.sign(json_str.encode('utf-8'))).decode('utf-8')
    
    cursor.execute(
        "INSERT INTO action_log VALUES (?, ?, ?, ?, ?)", 
        ("1", "user_01", "initialize", "2026-05-18T12:00:00", initial_sig)
    )
    conn.commit()
    
    signer.rotate_key(db_connection=conn)
    
    cursor.execute("SELECT signature FROM action_log WHERE id = '1'")
    rotated_sig = cursor.fetchone()[0]
    
    assert rotated_sig != initial_sig
    assert signer.verify(record_data, rotated_sig) is True
    
    conn.close()