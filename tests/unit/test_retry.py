"""Unit tests for core.utils.retry."""
import pytest

from core.utils.retry import retry


# ---------------------------------------------------------------------------
# Async coroutine tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_coroutine_succeeds_on_first_attempt():
    """Function that succeeds immediately is called exactly once."""
    call_count = 0

    @retry(max_retries=3, base_delay=0.01)
    async def always_ok():
        nonlocal call_count
        call_count += 1
        return "ok"

    result = await always_ok()
    assert result == "ok"
    assert call_count == 1


@pytest.mark.asyncio
async def test_coroutine_retries_on_transient_failure():
    """Function that fails twice then succeeds returns the correct value."""
    call_count = 0

    @retry(max_retries=3, base_delay=0.01)
    async def flaky():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ValueError("transient error")
        return "success"

    result = await flaky()
    assert result == "success"
    assert call_count == 3


@pytest.mark.asyncio
async def test_coroutine_raises_after_max_retries_exhausted():
    """Function that always fails re-raises the last exception."""
    call_count = 0

    @retry(max_retries=2, base_delay=0.01)
    async def always_fails():
        nonlocal call_count
        call_count += 1
        raise RuntimeError("permanent failure")

    with pytest.raises(RuntimeError, match="permanent failure"):
        await always_fails()

    # 1 initial attempt + 2 retries = 3 total
    assert call_count == 3


@pytest.mark.asyncio
async def test_coroutine_total_attempts_is_max_retries_plus_one():
    """Confirms exactly max_retries + 1 attempts are made."""
    call_count = 0

    @retry(max_retries=4, base_delay=0.01)
    async def always_fails():
        nonlocal call_count
        call_count += 1
        raise ValueError("error")

    with pytest.raises(ValueError):
        await always_fails()

    assert call_count == 5


@pytest.mark.asyncio
async def test_coroutine_zero_retries_calls_once():
    """max_retries=0 means a single attempt with no retries."""
    call_count = 0

    @retry(max_retries=0, base_delay=0.01)
    async def always_fails():
        nonlocal call_count
        call_count += 1
        raise ValueError("only once")

    with pytest.raises(ValueError):
        await always_fails()

    assert call_count == 1


@pytest.mark.asyncio
async def test_coroutine_passes_args_and_kwargs():
    """Wrapped coroutine receives positional and keyword arguments."""

    @retry(max_retries=1, base_delay=0.01)
    async def add(a: int, b: int = 0) -> int:
        return a + b

    assert await add(3, b=4) == 7


# ---------------------------------------------------------------------------
# Async generator tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_async_gen_yields_all_items_on_success():
    """Async generator that succeeds streams every item."""

    @retry(max_retries=2, base_delay=0.01)
    async def good_stream():
        for i in range(3):
            yield i

    results = [item async for item in good_stream()]
    assert results == [0, 1, 2]


@pytest.mark.asyncio
async def test_async_gen_retries_when_setup_raises():
    """Async generator that raises before yielding is retried."""
    call_count = 0

    @retry(max_retries=2, base_delay=0.01)
    async def flaky_stream():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise ConnectionError("stream error")
        yield "item"

    results = [item async for item in flaky_stream()]
    assert results == ["item"]
    assert call_count == 2


@pytest.mark.asyncio
async def test_async_gen_raises_after_max_retries_exhausted():
    """Async generator that always fails re-raises after all attempts."""
    call_count = 0

    @retry(max_retries=2, base_delay=0.01)
    async def bad_stream():
        nonlocal call_count
        call_count += 1
        raise RuntimeError("stream failure")
        yield  # pragma: no cover — makes this an async generator function

    with pytest.raises(RuntimeError, match="stream failure"):
        async for _ in bad_stream():
            pass

    assert call_count == 3  # 1 initial + 2 retries


@pytest.mark.asyncio
async def test_async_gen_passes_args_and_kwargs():
    """Wrapped async generator receives positional and keyword arguments."""

    @retry(max_retries=1, base_delay=0.01)
    async def counter(start: int, step: int = 1):
        for i in range(start, start + 3 * step, step):
            yield i

    results = [item async for item in counter(10, step=2)]
    assert results == [10, 12, 14]


# ---------------------------------------------------------------------------
# Metadata preservation tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_retry_preserves_coroutine_metadata():
    """functools.wraps keeps __name__ and __doc__ on wrapped coroutines."""

    @retry(max_retries=1, base_delay=0.01)
    async def my_coroutine():
        """My docstring."""
        return 1

    assert my_coroutine.__name__ == "my_coroutine"
    assert my_coroutine.__doc__ == "My docstring."


@pytest.mark.asyncio
async def test_retry_preserves_generator_metadata():
    """functools.wraps keeps __name__ and __doc__ on wrapped generators."""

    @retry(max_retries=1, base_delay=0.01)
    async def my_generator():
        """My generator docstring."""
        yield 1

    assert my_generator.__name__ == "my_generator"
    assert my_generator.__doc__ == "My generator docstring."


# ---------------------------------------------------------------------------
# Invalid argument tests
# ---------------------------------------------------------------------------


def test_retry_rejects_negative_max_retries():
    """Negative max_retries raises ValueError at decoration time."""
    with pytest.raises(ValueError, match="max_retries"):
        retry(max_retries=-1, base_delay=1.0)


def test_retry_rejects_non_positive_base_delay():
    """Non-positive base_delay raises ValueError at decoration time."""
    with pytest.raises(ValueError, match="base_delay"):
        retry(max_retries=3, base_delay=0)

    with pytest.raises(ValueError, match="base_delay"):
        retry(max_retries=3, base_delay=-1.0)
