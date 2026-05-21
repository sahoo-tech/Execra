"""
Tests for core/utils/retry.py

Sync tests live in TestRetry(unittest.TestCase) to preserve the original
test structure.  Async tests are collected as plain pytest coroutines so
that pytest-asyncio actually awaits them — unittest.TestCase cannot await
async methods and those tests previously ran as silent false-positives.
"""
import asyncio
import time
import unittest

import pytest
from unittest.mock import AsyncMock, Mock, patch

from openai import APIError, RateLimitError

from core.utils.retry import retry


# ---------------------------------------------------------------------------
# Sync tests (unittest.TestCase — unchanged from original structure)
# ---------------------------------------------------------------------------

class TestRetry(unittest.TestCase):

    def test_non_retryable_exception(self):
        mock_func = Mock(side_effect=ValueError("invalid input"))
        decorated = retry()(mock_func)

        with pytest.raises(ValueError):
            decorated()

        assert mock_func.call_count == 1

    def test_sync_success_without_retry(self):
        mock_func = Mock(return_value="success")
        decorated = retry()(mock_func)
        result = decorated()

        assert result == "success"
        assert mock_func.call_count == 1

    def test_sync_retries_then_success(self):
        mock_func = Mock(
            side_effect=[
                APIError("temporary error", request=None, body=None),
                "success",
            ]
        )
        decorated = retry(max_retries=3, base_delay=0)(mock_func)

        with patch("time.sleep") as mock_sleep:
            result = decorated()

            assert result == "success"
            assert mock_func.call_count == 2
            mock_sleep.assert_called_once_with(0)

    def test_sync_max_retries_exceeded(self):
        mock_func = Mock(
            side_effect=APIError("temporary error", request=None, body=None)
        )
        decorated = retry(max_retries=3, base_delay=0)(mock_func)

        with patch("time.sleep") as mock_sleep:
            with pytest.raises(APIError):
                decorated()

            assert mock_func.call_count == 3
            assert mock_sleep.call_count == 2

    def test_exponential_backoff_sync(self):
        mock_response = Mock()
        mock_response.request = Mock()

        mock_func = Mock(
            side_effect=[
                APIError("error1", request=None, body=None),
                RateLimitError("error2", response=mock_response, body=None),
                "success",
            ]
        )
        decorated = retry(max_retries=3, base_delay=1)(mock_func)

        with patch("time.sleep") as mock_sleep:
            decorated()
            assert mock_sleep.call_args_list == [((1,),), ((2,),)]


# ---------------------------------------------------------------------------
# Async tests — plain pytest coroutines so pytest-asyncio awaits them
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_async_decorator_returns_callable():
    """
    Regression test for the 'return async_wapper' typo.

    When @retry is applied to an async function the decorator must return
    the wrapper, not raise NameError.  Verify the result is callable and
    that calling it produces the correct return value.
    """
    async def target():
        return "ok"

    decorated = retry()(target)

    assert callable(decorated), (
        "retry() applied to an async function must return a callable wrapper"
    )
    assert await decorated() == "ok"


@pytest.mark.asyncio
async def test_async_success_without_retry():
    mock_func = AsyncMock(return_value="success")
    decorated = retry()(mock_func)
    result = await decorated()

    assert result == "success"
    assert mock_func.call_count == 1


@pytest.mark.asyncio
async def test_async_retries_then_success():
    mock_response = Mock()
    mock_response.request = Mock()

    mock_func = AsyncMock(
        side_effect=[
            RateLimitError("temporary error", response=mock_response, body=None),
            "success",
        ]
    )
    decorated = retry(max_retries=3, base_delay=0)(mock_func)

    with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        result = await decorated()

        assert result == "success"
        assert mock_func.call_count == 2
        mock_sleep.assert_awaited_once_with(0)


@pytest.mark.asyncio
async def test_async_max_retries_exceeded():
    mock_response = Mock()
    mock_response.request = Mock()

    mock_func = AsyncMock(
        side_effect=RateLimitError("temporary error", response=mock_response, body=None)
    )
    decorated = retry(max_retries=3, base_delay=0)(mock_func)

    with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        with pytest.raises(RateLimitError):
            await decorated()

        assert mock_func.call_count == 3
        assert mock_sleep.call_count == 2


@pytest.mark.asyncio
async def test_exponential_backoff_async():
    mock_response = Mock()
    mock_response.request = Mock()

    mock_func = AsyncMock(
        side_effect=[
            APIError("error1", request=None, body=None),
            RateLimitError("error2", response=mock_response, body=None),
            "success",
        ]
    )
    decorated = retry(max_retries=3, base_delay=1)(mock_func)

    with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        await decorated()
        assert mock_sleep.call_args_list == [((1,),), ((2,),)]


@pytest.mark.asyncio
async def test_async_non_retryable_exception():
    """Exceptions outside (RateLimitError, APIError) must propagate immediately."""
    call_count = 0

    async def target():
        nonlocal call_count
        call_count += 1
        raise ValueError("not a retryable error")

    decorated = retry(max_retries=3, base_delay=0)(target)

    with pytest.raises(ValueError, match="not a retryable error"):
        await decorated()

    assert call_count == 1, "non-retryable exception must not trigger retries"


@pytest.mark.asyncio
async def test_async_preserves_return_value_across_retries():
    """Ensure the actual return value from the successful attempt is returned."""
    mock_response = Mock()
    mock_response.request = Mock()

    expected = {"key": "value", "n": 42}
    mock_func = AsyncMock(
        side_effect=[
            APIError("transient", request=None, body=None),
            expected,
        ]
    )
    decorated = retry(max_retries=2, base_delay=0)(mock_func)

    with patch("asyncio.sleep", new_callable=AsyncMock):
        result = await decorated()

    assert result is expected


@pytest.mark.asyncio
async def test_async_functools_wraps_preserves_metadata():
    """@retry must preserve __name__ and __doc__ of the original function."""
    async def my_function():
        """My docstring."""
        return "result"

    decorated = retry()(my_function)

    assert decorated.__name__ == "my_function"
    assert decorated.__doc__ == "My docstring."
