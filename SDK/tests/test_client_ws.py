import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock
from execra_sdk import ExecraClient, GuidanceInstruction, ExecraConnectionError, ExecraError

@pytest.mark.asyncio
async def test_stream_guidance_success(client):
    mock_ws = AsyncMock()
    
    async def mock_async_iter():
        yield json.dumps({
            "event": "guidance",
            "payload": {
                "instruction": "Step 1",
                "confidence": 0.9,
                "source": [],
                "reasoning": "R1",
                "mode": "manual",
                "step": 1,
                "total_steps": 2,
                "generated_at": "2024-05-14T00:00:00Z"
            }
        })

    mock_ws.__aiter__.side_effect = mock_async_iter

    with patch("websockets.connect", return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_ws))):
        instructions = []
        async for instr in client.stream_guidance():
            instructions.append(instr)
            break
        
        assert len(instructions) == 1
        assert instructions[0].instruction == "Step 1"

@pytest.mark.asyncio
async def test_stream_guidance_frame_too_large(client):
    mock_ws = AsyncMock()
    async def mock_async_iter():
        yield "X" * (11 * 1024 * 1024)  # 11MB > 10MB limit

    mock_ws.__aiter__.side_effect = mock_async_iter
    with patch("websockets.connect", return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_ws))):
        with pytest.raises(ExecraError, match="exceeds size limit"):
            async for _ in client.stream_guidance():
                pass

@pytest.mark.asyncio
async def test_stream_guidance_malformed_json(client):
    mock_ws = AsyncMock()
    async def mock_async_iter():
        yield "not-json"

    mock_ws.__aiter__.side_effect = mock_async_iter
    with patch("websockets.connect", return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_ws))):
        with pytest.raises(ExecraError, match="Malformed guidance message"):
            async for _ in client.stream_guidance():
                pass

@pytest.mark.asyncio
async def test_stream_guidance_missing_payload(client):
    mock_ws = AsyncMock()
    async def mock_async_iter():
        yield json.dumps({"event": "guidance"})  # No payload

    mock_ws.__aiter__.side_effect = mock_async_iter
    with patch("websockets.connect", return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_ws))):
        with pytest.raises(ExecraError, match="missing 'payload' key"):
            async for _ in client.stream_guidance():
                pass

@pytest.mark.asyncio
async def test_stream_guidance_connection_closed(client):
    mock_ws = AsyncMock()
    async def mock_async_iter():
        if False:
            yield "never"
        # Using a name that matches the check in client.py
        class ConnectionClosed(Exception): pass
        raise ConnectionClosed("closed")

    mock_ws.__aiter__.side_effect = mock_async_iter
    with patch("websockets.connect", return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_ws))):
        with pytest.raises(ExecraConnectionError):
            async for _ in client.stream_guidance():
                pass
