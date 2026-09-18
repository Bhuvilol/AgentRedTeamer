from agentredteamer.retry import _suggested_wait


def test_parses_minutes_and_seconds():
    message = "Please try again in 1m32.015999999s"
    assert _suggested_wait(message) == 92.015999999


def test_parses_seconds_only():
    message = "Please try again in 3m10.08s"
    assert abs(_suggested_wait(message) - 190.08) < 1e-9


def test_parses_short_seconds_only():
    message = "Please try again in 2.392s"
    assert _suggested_wait(message) == 2.392


def test_returns_none_when_no_wait_present():
    assert _suggested_wait("Some unrelated error message") is None
