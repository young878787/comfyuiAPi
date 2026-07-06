"""Retry utilities with exponential backoff for API calls."""

import asyncio
import logging
import time
from functools import wraps
from typing import Callable, Optional, Tuple, Type

logger = logging.getLogger(__name__)


def retry_sync(
    func: Callable,
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    retryable_exceptions: Optional[Tuple[Type[Exception], ...]] = None,
    *args,
    **kwargs,
):
    """
    Execute a synchronous function with retry logic.

    Args:
        func: The function to execute
        max_retries: Maximum number of retry attempts (default 3)
        delay: Initial delay between retries in seconds (default 1.0)
        backoff: Multiplier for delay after each retry (default 2.0)
        retryable_exceptions: Tuple of exception types that trigger retry.
                              If None, all exceptions are retried.

    Returns:
        The result of the function call

    Raises:
        The last exception if all retries are exhausted
    """
    current_delay = delay
    last_exception = None

    for attempt in range(1, max_retries + 1):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            last_exception = e

            if retryable_exceptions and not isinstance(e, retryable_exceptions):
                raise

            if attempt < max_retries:
                logger.warning(
                    "Retry attempt %d/%d after error: %s",
                    attempt,
                    max_retries,
                    str(e),
                )
                time.sleep(current_delay)
                current_delay *= backoff
            else:
                logger.error(
                    "All %d retry attempts exhausted. Last error: %s",
                    max_retries,
                    str(e),
                )

    raise last_exception


async def retry_async(
    func: Callable,
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    retryable_exceptions: Optional[Tuple[Type[Exception], ...]] = None,
    *args,
    **kwargs,
):
    """
    Execute an async function with retry logic.

    Args:
        func: The async function to execute
        max_retries: Maximum number of retry attempts (default 3)
        delay: Initial delay between retries in seconds (default 1.0)
        backoff: Multiplier for delay after each retry (default 2.0)
        retryable_exceptions: Tuple of exception types that trigger retry.
                              If None, all exceptions are retried.

    Returns:
        The result of the function call

    Raises:
        The last exception if all retries are exhausted
    """
    current_delay = delay
    last_exception = None

    for attempt in range(1, max_retries + 1):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            last_exception = e

            if retryable_exceptions and not isinstance(e, retryable_exceptions):
                raise

            if attempt < max_retries:
                logger.warning(
                    "Retry attempt %d/%d after error: %s",
                    attempt,
                    max_retries,
                    str(e),
                )
                await asyncio.sleep(current_delay)
                current_delay *= backoff
            else:
                logger.error(
                    "All %d retry attempts exhausted. Last error: %s",
                    max_retries,
                    str(e),
                )

    raise last_exception
