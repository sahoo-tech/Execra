import asyncio
import inspect
import time
import logging
from functools import wraps

from openai import APIError, RateLimitError

logger = logging.getLogger(__name__)

# Configure a clean file logging mechanism without side effects
if not logger.handlers:
    handler = logging.FileHandler("retry.log")
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.WARNING)


def retry(max_retries: int = 3, base_delay: float = 1.0):
    """
    Decorator to automatically retry both sync and async functions 
    upon hitting OpenAI API or Rate Limit errors with exponential backoff.
    """
    def decorator(func):
        # Handle Asynchronous Functions
        if inspect.iscoroutinefunction(func):

            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                for attempt in range(max_retries):
                    try:
                        return await func(*args, **kwargs)
                    except (RateLimitError, APIError) as e:
                        if attempt == max_retries - 1:
                            func_name = getattr(func, "__name__", "unknown_function")
                            logger.error(f"Max retries exceeded for {func_name}: {e}")
                            raise

                        delay = base_delay * (2**attempt)
                        logger.warning(
                            f"Retry {attempt + 1}/{max_retries} "
                            f"after {delay:.1f}s due to: {e}"
                        )
                        await asyncio.sleep(delay)

            return async_wrapper

        # Handle Synchronous Functions
        else:

            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                for attempt in range(max_retries):
                    try:
                        return func(*args, **kwargs)
                    except (RateLimitError, APIError) as e:
                        if attempt == max_retries - 1:
                            func_name = getattr(func, "__name__", "unknown_function")
                            logger.error(f"Max retries exceeded for {func_name}: {e}")
                            raise

                        delay = base_delay * (2**attempt)
                        logger.warning(
                            f"Retry {attempt + 1}/{max_retries} "
                            f"after {delay:.1f}s due to: {e}"
                        )
                        time.sleep(delay)

            return sync_wrapper

    return decorator