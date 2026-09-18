import time
from collections.abc import Callable
from typing import TypeVar

from groq import APIStatusError

T = TypeVar("T")

MAX_DELAY = 70.0


def with_retry(fn: Callable[[], T], max_attempts: int = 9, base_delay: float = 2.0) -> T:
    """Retry transient API failures.

    Only 429s and 5xx are retried. A 400 (malformed request, context overflow)
    fails the same way every time, so retrying it just burns minutes before
    failing anyway.
    """
    for attempt in range(max_attempts):
        try:
            return fn()
        except APIStatusError as e:
            retryable = e.status_code == 429 or e.status_code >= 500
            if not retryable or attempt == max_attempts - 1:
                raise
            delay = min(base_delay * (2**attempt), MAX_DELAY)
            print(f"  (retrying in {delay:.0f}s — {e.status_code})")
            time.sleep(delay)
    raise RuntimeError("unreachable")
