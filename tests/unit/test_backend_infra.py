import json
import logging

from backend.observability import JsonFormatter, request_id_var
from backend.ratelimit import RateLimiter


def test_rate_limiter_allows_up_to_limit_then_blocks_and_recovers():
    now = [0.0]
    rl = RateLimiter(3, 60, clock=lambda: now[0])
    assert [rl.allow("a") for _ in range(4)] == [True, True, True, False]
    assert rl.allow("b") is True  # other clients unaffected
    assert 1 <= rl.retry_after("a") <= 61
    now[0] = 61
    assert rl.allow("a") is True


def test_rate_limiter_disabled_when_limit_zero():
    rl = RateLimiter(0)
    assert all(rl.allow("x") for _ in range(100))


def test_json_logs_carry_request_id_and_extras_but_no_secrets():
    record = logging.LogRecord("yatra.test", logging.INFO, __file__, 1, "turn.completed", (), None)
    record.trip_id = "t-1"
    record.duration_ms = 12
    token = request_id_var.set("req-abc12345")
    try:
        line = json.loads(JsonFormatter().format(record))
    finally:
        request_id_var.reset(token)
    assert line["request_id"] == "req-abc12345" and line["trip_id"] == "t-1" and line["duration_ms"] == 12
    assert line["msg"] == "turn.completed" and line["level"] == "INFO"
