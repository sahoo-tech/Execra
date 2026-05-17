"""
Exponential-backoff retry decorator for async coroutines and async generators.

Usage::

    from core.utils.retry import retry

    @retry(max_retries=3, base_delay=2)
    async def call_api(prompt: str) -> str:
        ...

    @retry(max_retries=3, base_delay=2)
    async def stream_api(prompt: str) -> AsyncIterator[str]:
        ...
        yield token
"""
from __future__ import annotations

import asyncio
import functools
import inspect
import logging
from typing import Any, Callable, TypeVar

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


def retry(max_retries: int = 3, base_delay: float = 1.0) -> Callable[[F], F]:
    """Return a decorator that retries the wrapped async callable on exception.

    For async generator functions the entire generator is restarted from
    scratch on each retry attempt.  For regular async coroutines the call is
    simply re-awaited.

    Args:
        max_retries: Maximum number of additional attempts after the first
            failure.  Total attempts = ``max_retries + 1``.
        base_delay: Initial delay in seconds between attempts.  Doubles on
            each successive retry (exponential back-off).

    Returns:
        A decorator that wraps the target async callable with retry logic.

    Raises:
        ValueError: If *max_retries* is negative or *base_delay* is not
            positive.
    """
    if max_retries < 0:
        raise ValueError(f"max_retries must be >= 0, got {max_retries}")
    if base_delay <= 0:
        raise ValueError(f"base_delay must be > 0, got {base_delay}")

    def decorator(func: F) -> F:
        if inspect.isasyncgenfunction(func):
            @functools.wraps(func)
            async def async_gen_wrapper(*args: Any, **kwargs: Any):
                last_exc: BaseException | None = None
                for attempt in range(max_retries + 1):
                    try:
                        async for item in func(*args, **kwargs):
                            yield item
                        return
                    except Exception as exc:
                        last_exc = exc
                        if attempt < max_retries:
                            delay = base_delay * (2 ** attempt)
                            logger.warning(
                                "%s attempt %d/%d failed: %s — retrying in %.1fs",
                                func.__qualname__,
                                attempt + 1,
                                max_retries + 1,
                                exc,
                                delay,
                            )
                            await asyncio.sleep(delay)
                        else:
                            logger.error(
                                "%s failed after %d attempts: %s",
                                func.__qualname__,
                                max_retries + 1,
                                exc,
                            )
                raise last_exc  # type: ignore[misc]

            return async_gen_wrapper  # type: ignore[return-value]

        @functools.wraps(func)
        async def coroutine_wrapper(*args: Any, **kwargs: Any):
            last_exc: BaseException | None = None
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as exc:
                    last_exc = exc
                    if attempt < max_retries:
                        delay = base_delay * (2 ** attempt)
                        logger.warning(
                            "%s attempt %d/%d failed: %s — retrying in %.1fs",
                            func.__qualname__,
                            attempt + 1,
                            max_retries + 1,
                            exc,
                            delay,
                        )
                        await asyncio.sleep(delay)
                    else:
                        logger.error(
                            "%s failed after %d attempts: %s",
                            func.__qualname__,
                            max_retries + 1,
                            exc,
                        )
            raise last_exc  # type: ignore[misc]

        return coroutine_wrapper  # type: ignore[return-value]

    return decorator  # type: ignore[return-value]
