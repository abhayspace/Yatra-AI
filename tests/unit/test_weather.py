import os
from datetime import date, timedelta

import httpx
import pytest

from agent.errors import ToolError
from agent.tools.weather import fetch_weather

TODAY = date(2026, 3, 1)


def make_client(handler):
    return httpx.Client(transport=httpx.MockTransport(handler))


def forecast_payload(start: date, n: int, code=0, prob=0, mm=0.0, tmax=30.0):
    days = [(start + timedelta(days=i)).isoformat() for i in range(n)]
    return {
        "daily": {
            "time": days,
            "weather_code": [code] * n,
            "temperature_2m_max": [tmax] * n,
            "temperature_2m_min": [tmax - 10] * n,
            "precipitation_sum": [mm] * n,
            "precipitation_probability_max": [prob] * n,
        }
    }


def test_forecast_request_is_real_http_with_numeric_params_only():
    seen = []

    def handler(request: httpx.Request):
        seen.append(request)
        return httpx.Response(200, json=forecast_payload(date(2026, 3, 5), 3, code=63, prob=80, mm=12.0))

    report = fetch_weather(30.0869, 78.2676, date(2026, 3, 5), 3, client=make_client(handler), today=TODAY)
    assert len(seen) == 1
    req = seen[0]
    assert req.url.host == "api.open-meteo.com" and req.url.path == "/v1/forecast"
    params = dict(req.url.params)
    assert params["latitude"] == "30.0869" and params["longitude"] == "78.2676"
    assert params["start_date"] == "2026-03-05" and params["end_date"] == "2026-03-07"
    assert report.rainy_days == [1, 2, 3]
    assert report.days[0].summary == "Rain" and not report.used_archive


def test_hot_days_flagged():
    client = make_client(lambda r: httpx.Response(200, json=forecast_payload(date(2026, 3, 5), 2, tmax=41.0)))
    report = fetch_weather(26.9, 75.8, date(2026, 3, 5), 2, client=client, today=TODAY)
    assert report.hot_days == [1, 2] and report.rainy_days == []


def test_far_future_dates_use_archive_of_previous_year():
    seen = []

    def handler(request):
        seen.append(request)
        start = date.fromisoformat(request.url.params["start_date"])
        n = (date.fromisoformat(request.url.params["end_date"]) - start).days + 1
        payload = forecast_payload(start, n)
        del payload["daily"]["precipitation_probability_max"]
        return httpx.Response(200, json=payload)

    report = fetch_weather(15.5, 73.8, date(2026, 9, 10), 2, client=make_client(handler), today=TODAY)
    assert seen[0].url.host == "archive-api.open-meteo.com"
    assert seen[0].url.params["start_date"] == "2025-09-10"
    assert report.used_archive and all(d.source == "last-year-archive" for d in report.days)
    assert [d.date for d in report.days] == ["2026-09-10", "2026-09-11"]


def test_window_straddling_horizon_uses_both_sources():
    hosts = []

    def handler(request):
        hosts.append(request.url.host)
        start = date.fromisoformat(request.url.params["start_date"])
        n = (date.fromisoformat(request.url.params["end_date"]) - start).days + 1
        return httpx.Response(200, json=forecast_payload(start, n))

    report = fetch_weather(15.5, 73.8, TODAY + timedelta(days=14), 4, client=make_client(handler), today=TODAY)
    assert hosts == ["api.open-meteo.com", "archive-api.open-meteo.com"]
    assert [d.source for d in report.days] == ["forecast", "forecast", "last-year-archive", "last-year-archive"]


def test_network_failure_becomes_tool_error():
    def handler(request):
        raise httpx.ConnectError("boom")

    with pytest.raises(ToolError, match="could not be reached"):
        fetch_weather(15.5, 73.8, date(2026, 3, 5), 2, client=make_client(handler), today=TODAY)


def test_http_error_and_malformed_payload_become_tool_error():
    with pytest.raises(ToolError):
        fetch_weather(15.5, 73.8, date(2026, 3, 5), 2, client=make_client(lambda r: httpx.Response(500)), today=TODAY)
    with pytest.raises(ToolError, match="unexpected"):
        fetch_weather(15.5, 73.8, date(2026, 3, 5), 2, client=make_client(lambda r: httpx.Response(200, json={"oops": 1})), today=TODAY)


@pytest.mark.parametrize(
    "lat,lon,start,days",
    [
        ("0; DROP TABLE trips", 78.0, date(2026, 3, 5), 3),
        (30.0, "../../etc/passwd", date(2026, 3, 5), 3),
        (float("nan"), 78.0, date(2026, 3, 5), 3),
        (999.0, 78.0, date(2026, 3, 5), 3),
        (30.0, 78.0, "2026-03-05'; --", 3),
        (30.0, 78.0, date(2026, 3, 5), 10**6),
        (30.0, 78.0, date(2026, 3, 5), 0),
        (30.0, 78.0, date(2026, 3, 5), True),
    ],
)
def test_adversarial_inputs_are_rejected_before_any_request(lat, lon, start, days):
    def handler(request):
        raise AssertionError("no HTTP request should be made for invalid input")

    with pytest.raises(ToolError):
        fetch_weather(lat, lon, start, days, client=make_client(handler), today=TODAY)


@pytest.mark.live
@pytest.mark.skipif(os.getenv("RUN_NETWORK_TESTS") != "1", reason="set RUN_NETWORK_TESTS=1 to call the real Open-Meteo API")
def test_live_open_meteo_call():
    report = fetch_weather(30.0869, 78.2676, date.today() + timedelta(days=3), 3)
    assert len(report.days) == 3 and report.days[0].temp_max_c is not None
