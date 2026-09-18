import time
from collections.abc import Callable
from typing import TypeVar

from groq import APIStatusError

T = TypeVar("T")


def with_retry(fn: Callable[[], T], max_attempts: int = 6, base_delay: float = 2.0) -> T:
    for attempt in range(max_attempts):
        try:
            return fn()
        except APIStatusError as e:
            if attempt == max_attempts - 1:
                raise
            delay = base_delay * (2**attempt)
            print(f"  (rate limited or API error: {e}; retrying in {delay:.0f}s)")
            time.sleep(delay)
    raise RuntimeError("unreachable")
