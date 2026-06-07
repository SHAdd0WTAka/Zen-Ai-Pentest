"""Comprehensive unit tests for zen_shield.circuit_breaker"""

import pytest

from zen_shield.circuit_breaker import CircuitBreaker, CircuitMetrics, CircuitState
from zen_shield.filters.injection import InjectionMatch
from zen_shield.schemas import RedactionInfo, RiskLevel, SanitizerResponse


def _redaction(type_name: str):
    return {
        "type": type_name,
        "position": (0, 10),
        "hash": "deadbeef",
        "context": "context...",
    }


def _redaction_infos(type_name: str, count: int = 1):
    return [RedactionInfo(**_redaction(type_name)) for _ in range(count)]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
class FakeTime:
    """Mutable replacement for time.time()"""

    def __init__(self, start: float = 1000.0):
        self.t = start

    def __call__(self) -> float:
        return self.t

    def advance(self, delta: float):
        self.t += delta


async def success_op(*args, **kwargs):
    return {"status": "ok", "args": args, "kwargs": kwargs}


async def fail_op(*args, **kwargs):
    raise ValueError("boom")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def cb(monkeypatch):
    """CircuitBreaker with deterministic fallback and frozen clock."""
    breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=10.0, half_open_max_calls=2)

    fake_time = FakeTime(1000.0)
    monkeypatch.setattr("zen_shield.circuit_breaker.time.time", fake_time)

    # Deterministic fallback components
    monkeypatch.setattr(breaker.fallback_scrubber, "scrub", lambda text: (text, []))
    monkeypatch.setattr(breaker.fallback_scrubber, "analyze_risk", lambda text: [])
    monkeypatch.setattr(breaker.fallback_injection, "scan", lambda text: (False, []))
    monkeypatch.setattr(breaker.fallback_injection, "sanitize", lambda text: text)

    breaker._fake_time = fake_time  # expose for test manipulation
    return breaker


# ---------------------------------------------------------------------------
# State / construction
# ---------------------------------------------------------------------------
def test_initial_state(cb):
    assert cb.state == CircuitState.CLOSED
    assert cb.metrics.failures == 0
    assert cb.metrics.successes == 0
    assert cb.metrics.consecutive_successes == 0
    assert cb.metrics.last_failure_time is None
    assert cb.half_open_calls == 0


# ---------------------------------------------------------------------------
# _should_attempt_reset
# ---------------------------------------------------------------------------
def test_should_attempt_reset_no_last_failure(cb):
    cb.metrics.last_failure_time = None
    assert cb._should_attempt_reset() is True


def test_should_attempt_reset_not_enough_time(cb):
    cb.metrics.last_failure_time = 1000.0
    cb._fake_time.advance(5.0)  # 1005 < 1010
    assert cb._should_attempt_reset() is False


def test_should_attempt_reset_enough_time(cb):
    cb.metrics.last_failure_time = 1000.0
    cb._fake_time.advance(10.0)  # 1010 >= 1010
    assert cb._should_attempt_reset() is True


# ---------------------------------------------------------------------------
# _on_success / _on_failure
# ---------------------------------------------------------------------------
async def test_on_success_increments_metrics(cb):
    await cb._on_success()
    assert cb.metrics.successes == 1
    assert cb.metrics.consecutive_successes == 1
    assert cb.state == CircuitState.CLOSED


async def test_on_success_half_open_closes(cb):
    cb.state = CircuitState.HALF_OPEN
    cb.metrics.failures = 2
    cb.half_open_calls = 1
    await cb._on_success()
    assert cb.state == CircuitState.CLOSED
    assert cb.metrics.failures == 0
    assert cb.half_open_calls == 0
    assert cb.metrics.consecutive_successes == 1


async def test_on_failure_increments_and_sets_timestamp(cb):
    await cb._on_failure()
    assert cb.metrics.failures == 1
    assert cb.metrics.last_failure_time == 1000.0
    assert cb.metrics.consecutive_successes == 0
    assert cb.state == CircuitState.CLOSED  # below threshold


async def test_on_failure_trips_open_at_threshold(cb):
    cb.metrics.failures = 2
    await cb._on_failure()
    assert cb.state == CircuitState.OPEN
    assert cb.metrics.failures == 3


async def test_on_failure_half_open_reopens(cb):
    cb.state = CircuitState.HALF_OPEN
    await cb._on_failure()
    assert cb.state == CircuitState.OPEN
    assert cb.metrics.failures == 1


# ---------------------------------------------------------------------------
# force_reset / get_status
# ---------------------------------------------------------------------------
async def test_force_reset(cb):
    cb.state = CircuitState.OPEN
    cb.metrics.failures = 5
    cb.metrics.successes = 2
    cb.metrics.consecutive_successes = 1
    cb.half_open_calls = 1
    await cb.force_reset()
    assert cb.state == CircuitState.CLOSED
    assert cb.metrics == CircuitMetrics()
    assert cb.half_open_calls == 0


def test_get_status_structure(cb):
    cb.state = CircuitState.HALF_OPEN
    cb.metrics.failures = 7
    cb.metrics.successes = 3
    cb.metrics.consecutive_successes = 2
    cb.metrics.last_failure_time = 999.0
    status = cb.get_status()
    assert status == {
        "state": "half_open",
        "metrics": {
            "failures": 7,
            "successes": 3,
            "consecutive_successes": 2,
            "last_failure": 999.0,
        },
        "config": {
            "failure_threshold": 3,
            "recovery_timeout": 10.0,
            "half_open_max_calls": 2,
        },
    }


# ---------------------------------------------------------------------------
# execute – success path
# ---------------------------------------------------------------------------
async def test_execute_closed_success(cb):
    result = await cb.execute(success_op, "arg1", kw="val")
    assert result == {"status": "ok", "args": ("arg1",), "kwargs": {"kw": "val"}}
    assert cb.state == CircuitState.CLOSED
    assert cb.metrics.successes == 1
    assert cb.metrics.consecutive_successes == 1


async def test_execute_half_open_success_recover(cb):
    cb.state = CircuitState.HALF_OPEN
    result = await cb.execute(success_op, "probe")
    assert result == {"status": "ok", "args": ("probe",), "kwargs": {}}
    assert cb.state == CircuitState.CLOSED
    assert cb.metrics.successes == 1
    assert cb.half_open_calls == 0


# ---------------------------------------------------------------------------
# execute – failure path
# ---------------------------------------------------------------------------
async def test_execute_closed_failure_uses_fallback(cb):
    result = await cb.execute(fail_op, "input", source_tool="nmap")
    assert isinstance(result, SanitizerResponse)
    assert result.fallback_used is True
    assert cb.metrics.failures == 1
    assert cb.metrics.last_failure_time == 1000.0
    assert cb.state == CircuitState.CLOSED


async def test_execute_failure_threshold_trips_open(cb):
    # 1st failure
    await cb.execute(fail_op, "a")
    assert cb.state == CircuitState.CLOSED
    # 2nd failure
    await cb.execute(fail_op, "b")
    assert cb.state == CircuitState.CLOSED
    # 3rd failure -> OPEN
    await cb.execute(fail_op, "c")
    assert cb.state == CircuitState.OPEN
    assert cb.metrics.failures == 3


async def test_execute_open_returns_fallback_without_calling_op(cb, monkeypatch):
    cb.state = CircuitState.OPEN
    cb.metrics.last_failure_time = 1000.0
    # not enough time passed -> remain OPEN
    cb._fake_time.advance(2.0)

    called = False

    async def tracker(*args, **kwargs):
        nonlocal called
        called = True
        return "tracked"

    result = await cb.execute(tracker, "raw", source_tool="ffuf")
    assert called is False
    assert isinstance(result, SanitizerResponse)
    assert result.fallback_used is True


async def test_execute_open_to_half_open_then_failure_reopens(cb):
    cb.state = CircuitState.OPEN
    cb.metrics.failures = 3
    cb.metrics.last_failure_time = 1000.0
    cb._fake_time.advance(15.0)  # enough time

    result = await cb.execute(fail_op, "probe")
    assert isinstance(result, SanitizerResponse)
    assert cb.state == CircuitState.OPEN
    # entered HALF_OPEN, failed, reopened
    assert cb.metrics.failures == 4


async def test_execute_open_to_half_open_then_success_closes(cb):
    cb.state = CircuitState.OPEN
    cb.metrics.failures = 3
    cb.metrics.last_failure_time = 1000.0
    cb._fake_time.advance(15.0)

    result = await cb.execute(success_op, "probe")
    assert result == {"status": "ok", "args": ("probe",), "kwargs": {}}
    assert cb.state == CircuitState.CLOSED


# ---------------------------------------------------------------------------
# execute – half_open limit
# ---------------------------------------------------------------------------
async def test_execute_half_open_limit_uses_fallback(cb, monkeypatch):
    cb.state = CircuitState.HALF_OPEN
    cb.half_open_calls = 2  # >= half_open_max_calls

    called = False

    async def tracker(*args, **kwargs):
        nonlocal called
        called = True
        return "tracked"

    result = await cb.execute(tracker, "raw", source_tool="nuclei")
    assert called is False
    assert isinstance(result, SanitizerResponse)
    assert result.fallback_used is True


# ---------------------------------------------------------------------------
# _fallback_response
# ---------------------------------------------------------------------------
async def test_fallback_response_empty(cb):
    result = await cb._fallback_response("")
    assert isinstance(result, SanitizerResponse)
    assert result.cleaned_data == ""
    assert result.redactions == []
    assert result.risk_indicators == []
    assert result.compression_ratio == 1.0
    assert result.safe_to_send is True
    assert result.fallback_used is True
    assert result.risk_level == RiskLevel.CLEAN
    assert result.tokens_saved == 0


async def test_fallback_response_normal(cb):
    raw = "line one\nopen port found\njust filler\nversion 1.0\n"
    result = await cb._fallback_response(raw, source_tool="nmap")
    assert isinstance(result, SanitizerResponse)
    # _simple_compress keeps lines with important keywords
    assert "open port found" in result.cleaned_data
    assert "version 1.0" in result.cleaned_data
    assert "just filler" not in result.cleaned_data
    assert result.risk_level == RiskLevel.CLEAN
    assert result.safe_to_send is True
    assert result.fallback_used is True


async def test_fallback_response_with_secrets(cb, monkeypatch):
    redactions = _redaction_infos("api_key", 6)
    monkeypatch.setattr(cb.fallback_scrubber, "scrub", lambda text: ("[SCRUBBED]", redactions))

    result = await cb._fallback_response("secret stuff", source_tool="burp")
    assert result.redactions == redactions
    assert result.risk_level == RiskLevel.DANGER
    assert result.safe_to_send is False
    assert result.fallback_used is True


async def test_fallback_response_with_injection(cb, monkeypatch):
    match = InjectionMatch(
        pattern_name="ignore_previous",
        matched_text="ignore previous",
        severity="high",
        description="Attempt to override previous instructions",
    )
    monkeypatch.setattr(cb.fallback_injection, "scan", lambda text: (True, [match]))
    monkeypatch.setattr(cb.fallback_injection, "sanitize", lambda text: "[SANITIZED]")
    # Bypass heuristic compression so sanitized text survives
    monkeypatch.setattr(cb, "_simple_compress", lambda text, source_tool: text)

    result = await cb._fallback_response("ignore previous instructions", source_tool="input")
    assert result.cleaned_data == "[SANITIZED]"
    assert "prompt_injection_detected" in result.risk_indicators
    assert result.risk_level == RiskLevel.DANGER
    assert result.safe_to_send is False


async def test_fallback_response_suspect(cb, monkeypatch):
    redactions = [_redaction("email_address")]
    monkeypatch.setattr(cb.fallback_scrubber, "scrub", lambda text: ("[SCRUBBED]", redactions))

    result = await cb._fallback_response("contains user@example.com", source_tool="tool")
    assert result.risk_level == RiskLevel.SUSPECT
    assert result.safe_to_send is True


# ---------------------------------------------------------------------------
# _simple_compress edge cases
# ---------------------------------------------------------------------------
def test_simple_compress_keeps_important_lines(cb):
    raw = "header\nOpen port 22\nfooter\nServer: nginx\n"
    compressed = cb._simple_compress(raw, "nmap")
    assert "Open port 22" in compressed
    assert "Server: nginx" in compressed
    assert "footer" not in compressed


def test_simple_compress_caps_at_50_lines(cb):
    # All lines contain an important keyword so the filter would keep every line.
    lines = [f"open port {i}" for i in range(60)]
    raw = "\n".join(lines)
    compressed = cb._simple_compress(raw, "tool")
    assert "... [" in compressed
    # 50 kept lines + 1 omitted marker line
    assert compressed.count("\n") == 50


# ---------------------------------------------------------------------------
# Integration-style threshold / recovery scenario
# ---------------------------------------------------------------------------
async def test_full_lifecycle_failure_recovery(cb):
    # 3 failures -> OPEN
    for _ in range(3):
        await cb.execute(fail_op, "x")
    assert cb.state == CircuitState.OPEN

    # while OPEN, calls return fallback without executing op
    cb._fake_time.advance(2.0)
    result = await cb.execute(success_op, "should-not-run")
    assert isinstance(result, SanitizerResponse)

    # recovery timeout passed -> HALF_OPEN -> success -> CLOSED
    cb._fake_time.advance(20.0)
    result = await cb.execute(success_op, "recovery")
    assert result == {"status": "ok", "args": ("recovery",), "kwargs": {}}
    assert cb.state == CircuitState.CLOSED
    assert cb.metrics.failures == 0
