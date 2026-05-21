import pytest
import respx
from httpx import Response
from execra_sdk import ExecraClient, ExecraAuthError, ExecraConnectionError, ExecraError
from execra_sdk.models import AskResponse, StatusResponse, ModeResponse, ActionRecord

@pytest.mark.asyncio
async def test_ask_success(client, mock_router):
    payload = {
        "answer": "Fix the syntax error",
        "confidence": 0.95,
        "source": ["file.py"],
        "reasoning": "Missing colon",
        "follow_up_suggestion": "Check other lines"
    }
    mock_router.post("/api/v1/guidance/ask").mock(return_value=Response(200, json=payload))
    
    result = await client.ask("How to fix this?")
    assert isinstance(result, AskResponse)
    assert result.answer == "Fix the syntax error"
    assert result.confidence == 0.95

@pytest.mark.asyncio
async def test_ask_invalid_length(client):
    with pytest.raises(ValueError, match="exceeds maximum length"):
        await client.ask("a" * 10001)

@pytest.mark.asyncio
async def test_ask_auth_error_truncation(client, mock_router):
    # Long error message should be truncated
    long_error = "X" * 1000
    mock_router.post("/api/v1/guidance/ask").mock(return_value=Response(401, text=long_error))
    with pytest.raises(ExecraAuthError) as exc:
        await client.ask("Where am I?")
    assert "XXXX" in str(exc.value)
    assert len(str(exc.value)) < 600

@pytest.mark.asyncio
async def test_get_status_success(client, mock_router):
    payload = {
        "status": "ok",
        "version": "0.1.0",
        "uptime_seconds": 3600,
        "active_domain": "general",
        "active_mode": "idle",
        "perception_fps": 30,
        "llm_backend": "gpt-4"
    }
    mock_router.get("/api/v1/status").mock(return_value=Response(200, json=payload))
    
    status = await client.get_status()
    assert isinstance(status, StatusResponse)
    assert status.status == "ok"

@pytest.mark.asyncio
async def test_switch_mode_success(client, mock_router):
    payload = {
        "mode": "autonomous",
        "description": "Running in autonomous mode",
        "message": "Mode switched successfully"
    }
    mock_router.put("/api/v1/mode").mock(return_value=Response(200, json=payload))
    
    result = await client.switch_mode("autonomous")
    assert isinstance(result, ModeResponse)
    assert result.mode == "autonomous"

@pytest.mark.asyncio
async def test_switch_mode_invalid(client):
    with pytest.raises(ValueError, match="Invalid mode"):
        await client.switch_mode("invalid-mode")

@pytest.mark.asyncio
async def test_double_connect(client):
    with pytest.raises(ExecraError, match="Already connected"):
        client.connect()

@pytest.mark.asyncio
async def test_repr(client):
    r = repr(client)
    assert "ExecraClient" in r
    assert "connected=True" in r
    assert "test-key" not in r  # Ensure API key is not in repr

@pytest.mark.asyncio
async def test_ensure_connected():
    client = ExecraClient()
    with pytest.raises(ExecraConnectionError, match="Call connect"):
        await client.get_status()
