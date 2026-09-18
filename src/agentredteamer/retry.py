import re
import time
from collections.abc import Callable
from typing import TypeVar

from groq import APIStatusError

T = TypeVar("T")

MAX_DELAY = 70.0
DAILY_QUOTA_MARKERS = ("per day", "TPD", "RPD")
MAX_QUOTA_WAIT = 15 * 60.0  # give up rather than sleep longer than this in one shot

RETRY_AFTER_PATTERN = re.compile(r"try again in (?:(\d+)m)?([\d.]+)s")


class DailyQuotaExceeded(Exception):
    """The daily cap is gone and Groq's own suggested wait exceeds MAX_QUOTA_WAIT."""


def _suggested_wait(message: str) -> float | None:
    match = RETRY_AFTER_PATTERN.search(message)
    if not match:
        return None
    minutes = int(match.group(1)) if match.group(1) else 0
    seconds = float(match.group(2))
    return minutes * 60 + seconds


def with_retry(fn: Callable[[], T], max_attempts: int = 9, base_delay: float = 2.0) -> T:
    for attempt in range(max_attempts):
        try:
            return fn()
        except APIStatusError as e:
            message = str(e)

            if e.status_code == 429 and any(marker in message for marker in DAILY_QUOTA_MARKERS):
                # Groq's own suggested wait is more accurate than blind exponential backoff
                # here — a "per day" limit on this API has behaved like a rolling window
                # that frees up in minutes, not a fixed reset at midnight.
                wait = _suggested_wait(message)
                if wait is None or wait > MAX_QUOTA_WAIT:
                    raise DailyQuotaExceeded(message) from e
                print(f"  (daily quota — waiting Groq's suggested {wait:.0f}s)")
                time.sleep(wait + 1)
                continue

            retryable = e.status_code == 429 or e.status_code >= 500
            if not retryable or attempt == max_attempts - 1:
                raise
            delay = min(base_delay * (2**attempt), MAX_DELAY)
            print(f"  (retrying in {delay:.0f}s — {e.status_code})")
            time.sleep(delay)
    raise RuntimeError("unreachable")
