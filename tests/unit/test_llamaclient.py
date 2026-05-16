import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

patch("core.utils.retry.retry", lambda *args, **kwargs: lambda f: f).start()

from core.intelligence.llm_client import LlamaClient

@pytest.mark.asyncio
async def test_complete_success():
    mock_response = MagicMock()

    mock_response.json.return_value = {
        "response": "Hello from Llama"
    }
    mock_response.raise_for_status.return_value = None

    with patch("core.intelligence.llm_client.httpx.AsyncClient") as mock_httpx:
        mock_client = MagicMock()
        mock_client.post = AsyncMock(
            return_value=mock_response
        )
        mock_httpx.return_value = mock_client

        client = LlamaClient()
        response = await client.complete("Hello")

        assert response == "Hello from Llama"
        mock_client.post.assert_awaited_once_with(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3",
                "prompt": "Hello",
                "stream": False
            }
        )

@pytest.mark.asyncio
async def test_complete_http_error():

    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = Exception(
        "HTTP Error"
    )

    with patch("core.intelligence.llm_client.httpx.AsyncClient") as mock_httpx:
        mock_client = MagicMock()
        mock_client.post = AsyncMock(
            return_value=mock_response
        )
        mock_httpx.return_value = mock_client

        client = LlamaClient()
        with pytest.raises(Exception, match="HTTP Error"):

            await client.complete("Hello")

@pytest.mark.asyncio
async def test_stream_success():
    lines = [
        json.dumps({
            "response": "Hello ",
            "done": False
        }),
        json.dumps({
            "response": "World",
            "done": False
        }),
        json.dumps({
            "response": "!",
            "done": True
        })
    ]

    async def mock_aiter_lines():
        for line in lines:
            yield line

    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.aiter_lines = mock_aiter_lines

    mock_stream_context = AsyncMock()
    mock_stream_context.__aenter__.return_value = mock_response
    mock_stream_context.__aexit__.return_value = None

    with patch("core.intelligence.llm_client.httpx.AsyncClient") as mock_httpx:
        mock_client = MagicMock()
        mock_client.stream.return_value = mock_stream_context
        mock_httpx.return_value = mock_client
        client = LlamaClient()

        results = []
        async for token in client.stream("Hello"):
            results.append(token)

        assert results == ["Hello ", "World", "!"]
        mock_client.stream.assert_called_once_with(
            "POST",
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3",
                "prompt": "Hello",
                "stream": True
            }
        )

@pytest.mark.asyncio
async def test_stream_skips_empty_lines():
    lines = [
        "",
        json.dumps({
            "response": "Valid",
            "done": False
        }),
        ""
    ]

    async def mock_aiter_lines():
        for line in lines:
            yield line

    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.aiter_lines = mock_aiter_lines

    mock_stream_context = AsyncMock()
    mock_stream_context.__aenter__.return_value = mock_response
    mock_stream_context.__aexit__.return_value = None

    with patch("core.intelligence.llm_client.httpx.AsyncClient") as mock_httpx:
        mock_client = MagicMock()
        mock_client.stream.return_value = mock_stream_context
        mock_httpx.return_value = mock_client

        client = LlamaClient()
        results = []

        async for token in client.stream("Hello"):
            results.append(token)

        assert results == ["Valid"]

@pytest.mark.asyncio
async def test_stream_stops_on_done_true():
    lines = [
        json.dumps({
            "response": "First",
            "done": True
        }),

        json.dumps({
            "response": "Should not appear",
            "done": False
        })
    ]

    async def mock_aiter_lines():
        for line in lines:
            yield line

    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.aiter_lines = mock_aiter_lines

    mock_stream_context = AsyncMock()
    mock_stream_context.__aenter__.return_value = mock_response
    mock_stream_context.__aexit__.return_value = None

    with patch("core.intelligence.llm_client.httpx.AsyncClient") as mock_httpx:
        mock_client = MagicMock()
        mock_client.stream.return_value = mock_stream_context
        mock_httpx.return_value = mock_client

        client = LlamaClient()
        results = []

        async for token in client.stream("Hello"):
            results.append(token)

        assert results == ["First"]

def test_extract_confidence():

    client = LlamaClient()
    confidence = client.extract_confidence("sample response")

    assert isinstance(confidence, float)
    assert confidence == 0.5