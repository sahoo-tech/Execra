from unittest.mock import AsyncMock, Mock, patch

import pytest
from openai import RateLimitError

from core.config import Settings
from core.intelligence.llm_client import MockApiError, OpenAIClient


@pytest.fixture
def settings():
    s = Settings()
    s.OPENAI_API_KEY = "test_key"
    return s


@pytest.mark.asyncio
async def test_complete_success(settings):
    """Test Successful completion"""
    mock_response = Mock()

    mock_response.choices = [Mock(message=Mock(content="Hello"))]

    with patch("core.intelligence.llm_client.AsyncOpenAI") as mock_openai:

        mock_openai.return_value.chat.completions.create = AsyncMock(return_value=mock_response)

        client = OpenAIClient(settings)

        result = await client.complete("Test prompt")

        assert result == "Hello"


@pytest.mark.asyncio
async def test_complete_retries_on_rate_limit(settings):
    """Test retries on RateLimitError"""
    mock_response = Mock()
    mock_response.choices = [Mock(message=Mock(content="Recovered Response"))]
    mock_request = Mock()
    mock_response_obj = Mock()
    mock_response_obj.request = mock_request

    mock_create = AsyncMock(
        side_effect=[
            RateLimitError("Rate limit exceeded", response=mock_response_obj, body=None),
            mock_response,
        ]
    )

    with patch("core.intelligence.llm_client.AsyncOpenAI") as mock_openai:
        mock_openai.return_value.chat.completions.create = mock_create

        client = OpenAIClient(settings)

        result = await client.complete("Test prompt")

        assert result == "Recovered Response"

        assert mock_create.call_count == 2


@pytest.mark.asyncio
async def test_complete_fails_after_max_retries(settings):
    """Test failure after max retries"""
    mock_create = AsyncMock(side_effect=MockApiError("Api Error"))
    mock_completions = Mock()
    mock_completions.create = mock_create

    mock_chat = Mock()
    mock_chat.completions = mock_completions

    mock_client = Mock()
    mock_client.chat = mock_chat

    with patch("core.intelligence.llm_client.AsyncOpenAI") as mock_openai:
        mock_openai.return_value = mock_client

        client = OpenAIClient(settings)

        with pytest.raises(MockApiError):
            print(mock_create.call_count)
            await client.complete("Failure Test")

        assert mock_create.call_count == 3


@pytest.mark.asyncio
async def test_stream_sucess(settings):
    """Test successful streaming response"""

    async def mock_stream():
        choice1 = Mock()
        choice1.delta = Mock()
        choice1.delta.content = "Hello"
        chunk1 = Mock()
        chunk1.choices = [choice1]

        choice2 = Mock()
        choice2.delta = Mock()
        choice2.delta.content = "World"
        chunk2 = Mock()
        chunk2.choices = [choice2]

        yield chunk1
        yield chunk2

    mock_create = AsyncMock(return_value=mock_stream())
    mock_completions = Mock()
    mock_completions.create = mock_create

    mock_chat = Mock()
    mock_chat.completions = mock_completions

    mock_client = Mock()
    mock_client.chat = mock_chat
    with patch("core.intelligence.llm_client.AsyncOpenAI") as mock_openai:

        mock_openai.return_value = mock_client

        client = OpenAIClient(settings)

        chunks = []
        async for chunk in client.stream("Stream test"):
            chunks.append(chunk)

        assert chunks == ["Hello", "World"]


def test_extract_confidence_default(settings):
    """Test default confidence extraction"""
    client = OpenAIClient(settings)

    confidence = client.extract_confidence({})

    assert confidence == 0.5
