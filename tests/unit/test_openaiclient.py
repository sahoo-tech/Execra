import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# Temporarily mock the retry decorator during import to avoid real delays/retries
_retry_patcher = patch("core.utils.retry.retry", lambda *args, **kwargs: lambda f: f)
_retry_patcher.start()
from core.intelligence.llm_client import OpenAIClient
_retry_patcher.stop()

@pytest.fixture
def valid_api_key():
    return "sk-test123"


@pytest.fixture
def mock_settings(valid_api_key):
    with patch("core.intelligence.llm_client.settings") as mock:
        mock.OPENAI_API_KEY = "sk-abcdef1234567890abcdef1234567890abcdef12"
        yield mock

def test_valid_api_key_format(mock_settings):
    client = OpenAIClient()
    assert client._isValidateFormat("sk-abc123") is True


def test_invalid_api_key_format(mock_settings):
    client = OpenAIClient()

    assert client._isValidateFormat("") is False
    assert client._isValidateFormat(None) is False
    assert client._isValidateFormat("abc123") is False
    assert client._isValidateFormat(12345) is False


def test_init_invalid_api_key():
    with patch("core.intelligence.llm_client.settings") as mock_settings:
        mock_settings.OPENAI_API_KEY = "invalid-key"

        with pytest.raises(ValueError, match="invalid"):
            OpenAIClient()

@pytest.mark.asyncio
async def test_complete_success(mock_settings):
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="4"))]

    with patch("core.intelligence.llm_client.AsyncOpenAI") as mock_openai_class:
        mock_instance = MagicMock()
        mock_instance.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_openai_class.return_value = mock_instance

        client = OpenAIClient()
        response = await client.complete("what is 2+2")
        
        assert response == "4"

@pytest.mark.asyncio
async def test_complete_raises_exception(mock_settings):

    with patch("core.intelligence.llm_client.AsyncOpenAI") as mock_openai:
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(
            side_effect=Exception("API Failure")
        )
        
        mock_openai.return_value = mock_client
        client = OpenAIClient()

        with pytest.raises(Exception, match="API Failure"):
            await client.complete("Hello")

@pytest.mark.asyncio
async def test_stream_success(mock_settings):
    chunk1 = MagicMock()
    chunk1.choices = [
        MagicMock(
            delta=MagicMock(content="Hello ")
        )
    ]

    chunk2 = MagicMock()
    chunk2.choices = [
        MagicMock(
            delta=MagicMock(content="World")
        )
    ]

    async def mock_stream():
        yield chunk1
        yield chunk2

    with patch("core.intelligence.llm_client.AsyncOpenAI") as mock_openai:
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(
            return_value=mock_stream()
        )
        mock_openai.return_value = mock_client
        
        client = OpenAIClient()
        results = []

        async for token in client.stream("Hello"):
            results.append(token)

        assert results == ["Hello ", "World"]
        mock_client.chat.completions.create.assert_awaited_once_with(
            model="gpt-4o",
            messages=[{"role": "user", "content": "Hello"}],
            stream=True
        )


@pytest.mark.asyncio
async def test_stream_skips_none_content(mock_settings):
    chunk1 = MagicMock()
    chunk1.choices = [
        MagicMock(
            delta=MagicMock(content=None)
        )
    ]

    chunk2 = MagicMock()
    chunk2.choices = [
        MagicMock(
            delta=MagicMock(content="Valid")
        )
    ]

    async def mock_stream():
        yield chunk1
        yield chunk2

    with patch("core.intelligence.llm_client.AsyncOpenAI") as mock_openai:
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(
            return_value=mock_stream()
        )
        mock_openai.return_value = mock_client
        
        client = OpenAIClient()
        results = []

        async for token in client.stream("test"):
            results.append(token)

        assert results == ["Valid"]

def test_extract_confidence(mock_settings):
    client = OpenAIClient()
    confidence = client.extract_confidence("sample response")

    assert isinstance(confidence, float)
    assert confidence == 0.5
