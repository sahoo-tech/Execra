import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# Temporarily mock the retry decorator during import to avoid real delays/retries
_retry_patcher = patch("core.utils.retry.retry", lambda *args, **kwargs: lambda f: f)
_retry_patcher.start()
from core.intelligence.llm_client import GeminiClient
_retry_patcher.stop()

@pytest.fixture
def valid_api_key():
    return "AI-test-key"

@pytest.fixture
def mock_settings(valid_api_key):
    with patch("core.intelligence.llm_client.settings") as mock:
        mock.GEMINI_API_KEY = valid_api_key
        yield mock

def test_valid_api_key_format(mock_settings):
    client = GeminiClient()

    assert client._isValidateFormat("AI-test123") is True

def test_invalid_api_key_format(mock_settings):
    client = GeminiClient()

    assert client._isValidateFormat("") is False
    assert client._isValidateFormat(None) is False
    assert client._isValidateFormat(123) is False
    assert client._isValidateFormat("sk-test") is False

def test_init_invalid_api_key():

    with patch("core.intelligence.llm_client.settings") as mock_settings:
        mock_settings.GEMINI_API_KEY = "invalid"

        with pytest.raises(ValueError, match="invalid"):
            GeminiClient()

@pytest.mark.asyncio
async def test_complete_success(mock_settings):
    mock_response = MagicMock()
    mock_response.text = "Gemini response"

    with patch("core.intelligence.llm_client.genai.Client") as mock_genai:
        mock_client = MagicMock()
        mock_client.aio.models.generate_content = AsyncMock(
            return_value=mock_response
        )
        mock_genai.return_value = mock_client
        client = GeminiClient()
        response = await client.complete("Hello")

        assert response == mock_response
        assert response.text == "Gemini response"
        mock_client.aio.models.generate_content.assert_awaited_once_with(
            model="gemini-1.5-pro",
            contents=[
                {
                    "role": "user",
                    "parts": [{"text": "Hello"}]
                }
            ]
        )

@pytest.mark.asyncio
async def test_complete_exception(mock_settings):

    with patch("core.intelligence.llm_client.genai.Client") as mock_genai:
        mock_client = MagicMock()
        mock_client.aio.models.generate_content = AsyncMock(
            side_effect=Exception("Gemini API Failure")
        )
        mock_genai.return_value = mock_client
        client = GeminiClient()

        with pytest.raises(Exception, match="Gemini API Failure"):
            await client.complete("Hello")

@pytest.mark.asyncio
async def test_stream_success(mock_settings):

    chunk1 = MagicMock()
    chunk1.text = "Hello "
    chunk2 = MagicMock()
    chunk2.text = "World"

    async def mock_stream():
        yield chunk1
        yield chunk2

    with patch("core.intelligence.llm_client.genai.Client") as mock_genai:
        mock_client = MagicMock()
        mock_client.aio.models.generate_content_stream = AsyncMock(
            return_value=mock_stream()
        )
        mock_genai.return_value = mock_client
        client = GeminiClient()
        results = []

        async for chunk in client.stream("Hello"):
            results.append(chunk.text)

        assert results == ["Hello ", "World"]
        mock_client.aio.models.generate_content_stream.assert_awaited_once_with(
            model="gemini-1.5-pro",
            contents=[
                {
                    "role": "user",
                    "parts": [{"text": "Hello"}]
                }
            ]
        )

@pytest.mark.asyncio
async def test_stream_skips_empty_chunks(mock_settings):

    chunk1 = None
    chunk2 = MagicMock()
    chunk2.text = "Valid chunk"

    async def mock_stream():
        yield chunk1
        yield chunk2

    with patch("core.intelligence.llm_client.genai.Client") as mock_genai:
        mock_client = MagicMock()
        mock_client.aio.models.generate_content_stream = AsyncMock(
            return_value=mock_stream()
        )
        mock_genai.return_value = mock_client
        client = GeminiClient()
        results = []

        async for chunk in client.stream("Hello"):
            if chunk:
                results.append(chunk.text)

        assert results == ["Valid chunk"]


def test_extract_confidence_high_risk(mock_settings):
    mock_rating = MagicMock()
    mock_rating.probability = "HIGH"

    mock_candidate = MagicMock()
    mock_candidate.safety_ratings = [mock_rating]

    mock_response = MagicMock()
    mock_response.candidates = [mock_candidate]

    client = GeminiClient()
    confidence = client.extract_confidence(mock_response)

    assert confidence == 0.1


def test_extract_confidence_multiple_ratings(mock_settings):
    rating1 = MagicMock()
    rating1.probability = "LOW"

    rating2 = MagicMock()
    rating2.probability = "MEDIUM"

    rating3 = MagicMock()
    rating3.probability = "NEGLIGIBLE"

    mock_candidate = MagicMock()
    mock_candidate.safety_ratings = [
        rating1,
        rating2,
        rating3
    ]

    mock_response = MagicMock()
    mock_response.candidates = [mock_candidate]

    client = GeminiClient()
    confidence = client.extract_confidence(mock_response)

    assert confidence == 0.4


def test_extract_confidence_no_ratings(mock_settings):
    mock_candidate = MagicMock()
    mock_candidate.safety_ratings = []

    mock_response = MagicMock()
    mock_response.candidates = [mock_candidate]

    client = GeminiClient()
    confidence = client.extract_confidence(mock_response)

    assert confidence == 0.5


def test_extract_confidence_unknown_probability(mock_settings):
    mock_rating = MagicMock()
    mock_rating.probability = "VERY_HIGH"

    mock_candidate = MagicMock()
    mock_candidate.safety_ratings = [mock_rating]

    mock_response = MagicMock()
    mock_response.candidates = [mock_candidate]

    client = GeminiClient()
    confidence = client.extract_confidence(mock_response)

    # fallback value
    assert confidence == 0.5