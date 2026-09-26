"""Weather tool: real HTTP calls to Open-Meteo (no API key needed).

Trips that start inside the 16-day forecast window use the forecast API. Days beyond it use
the archive API for the same calendar dates one year earlier and are labelled
"last-year-archive" so nothing historical is presented as a forecast.
"""
from __future__ import annotations

import math
from datetime import date, timedelta
from typing import Any

import httpx
from pydantic import BaseModel, Field

from agent.errors import ToolError
from agent.models import MAX_TRIP_DAYS, DayWeather

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
FORECAST_HORIZON_DAYS = 15
HOT_C = 38.0
TIMEOUT_SECONDS = 10.0

_WMO = {
    0: "Clear sky", 1: "Mostly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Rime fog",
    51: "Light drizzle", 53: "Drizzle", 55: "Heavy drizzle", 56: "Freezing drizzle", 57: "Freezing drizzle",
    61: "Light rain", 63: "Rain", 65: "Heavy rain", 66: "Freezing rain", 67: "Freezing rain",
    71: "Light snow", 73: "Snow", 75: "Heavy snow", 77: "Snow grains",
    80: "Rain showers", 81: "Rain showers", 82: "Violent rain showers",
    85: "Snow showers", 86: "Heavy snow showers",
    95: "Thunderstorm", 96: "Thunderstorm with hail", 99: "Thunderstorm with hail",
}
_WET_CODES = set(range(51, 68)) | {80, 81, 82, 95, 96, 99}


class WeatherReport(BaseModel):
    latitude: float
    longitude: float
    days: list[DayWeather]
    rainy_days: list[int] = Field(default_factory=list)  # 1-based trip day numbers
    hot_days: list[int] = Field(default_factory=list)
    used_archive: bool = False
    summary: str = ""


def _finite(value: Any, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ToolError(f"{name} must be a number.")
    f = float(value)
    if not math.isfinite(f):
        raise ToolError(f"{name} must be a finite number.")
    return f


def _classify(code: int | None, tmax: float | None, prob: float | None, mm: float | None) -> tuple[bool, bool, str]:
    wet_code = code in _WET_CODES if code is not None else False
    rainy = (wet_code and ((prob or 0) >= 40 or (mm or 0) >= 2)) or (prob or 0) >= 60 or (mm or 0) >= 5
    hot = tmax is not None and tmax >= HOT_C
    return bool(rainy), bool(hot), _WMO.get(code, "Unknown") if code is not None else ""


def _get_daily(client: httpx.Client, url: str, lat: float, lon: float, start: date, end: date, archive: bool) -> dict:
    daily = "weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum"
    if not archive:
        daily += ",precipitation_probability_max"
    params = {
        "latitude": f"{lat:.4f}",
        "longitude": f"{lon:.4f}",
        "daily": daily,
        "timezone": "auto",
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
    }
    try:
        resp = client.get(url, params=params, timeout=TIMEOUT_SECONDS)
        resp.raise_for_status()
        payload = resp.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise ToolError("The weather service (Open-Meteo) could not be reached.") from exc
    daily_block = payload.get("daily") if isinstance(payload, dict) else None
    if not isinstance(daily_block, dict) or not isinstance(daily_block.get("time"), list):
        raise ToolError("The weather service returned an unexpected response.")
    return daily_block


def _at(block: dict, key: str, i: int) -> Any:
    series = block.get(key)
    if isinstance(series, list) and i < len(series):
        return series[i]
    return None


def _num(v: Any) -> float | None:
    return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) else None


def fetch_weather(
    lat: float,
    lon: float,
    start_date: date,
    days: int,
    *,
    client: httpx.Client | None = None,
    today: date | None = None,
) -> WeatherReport:
    """Daily weather for the trip window. Raises ToolError if inputs are invalid or Open-Meteo fails."""
    lat, lon = _finite(lat, "latitude"), _finite(lon, "longitude")
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        raise ToolError("Coordinates are out of range.")
    if not isinstance(start_date, date):
        raise ToolError("Start date must be a date.")
    if isinstance(days, bool) or not isinstance(days, int) or not (1 <= days <= MAX_TRIP_DAYS):
        raise ToolError(f"Trip length must be between 1 and {MAX_TRIP_DAYS} days.")

    today = today or date.today()
    horizon = today + timedelta(days=FORECAST_HORIZON_DAYS)
    dates = [start_date + timedelta(days=i) for i in range(days)]
    forecast_dates = [d for d in dates if today <= d <= horizon]
    archive_dates = [d for d in dates if d not in forecast_dates]

    own_client = client is None
    http = client or httpx.Client()
    try:
        by_date: dict[date, DayWeather] = {}
        if forecast_dates:
            block = _get_daily(http, FORECAST_URL, lat, lon, forecast_dates[0], forecast_dates[-1], archive=False)
            for i, iso in enumerate(block["time"]):
                d = date.fromisoformat(iso)
                code, tmax = _at(block, "weather_code", i), _num(_at(block, "temperature_2m_max", i))
                prob, mm = _num(_at(block, "precipitation_probability_max", i)), _num(_at(block, "precipitation_sum", i))
                rainy, hot, text = _classify(int(code) if code is not None else None, tmax, prob, mm)
                by_date[d] = DayWeather(
                    date=iso, temp_max_c=tmax, temp_min_c=_num(_at(block, "temperature_2m_min", i)),
                    precip_probability=prob, precip_mm=mm, summary=text, rainy=rainy, hot=hot, source="forecast",
                )
        if archive_dates:
            # same calendar dates a year earlier; Feb 29 falls back to Feb 28
            def last_year(d: date) -> date:
                try:
                    return d.replace(year=d.year - 1)
                except ValueError:
                    return d.replace(year=d.year - 1, day=28)

            past = [last_year(d) for d in archive_dates]
            block = _get_daily(http, ARCHIVE_URL, lat, lon, min(past), max(past), archive=True)
            index = {iso: i for i, iso in enumerate(block["time"])}
            for d, p in zip(archive_dates, past):
                i = index.get(p.isoformat())
                if i is None:
                    continue
                code, tmax = _at(block, "weather_code", i), _num(_at(block, "temperature_2m_max", i))
                mm = _num(_at(block, "precipitation_sum", i))
                rainy, hot, text = _classify(int(code) if code is not None else None, tmax, None, mm)
                by_date[d] = DayWeather(
                    date=d.isoformat(), temp_max_c=tmax, temp_min_c=_num(_at(block, "temperature_2m_min", i)),
                    precip_probability=None, precip_mm=mm, summary=text, rainy=rainy, hot=hot, source="last-year-archive",
                )
    finally:
        if own_client:
            http.close()

    ordered = [by_date[d] for d in dates if d in by_date]
    if not ordered:
        raise ToolError("The weather service returned no data for these dates.")
    rainy_days = [i + 1 for i, d in enumerate(dates) if d in by_date and by_date[d].rainy]
    hot_days = [i + 1 for i, d in enumerate(dates) if d in by_date and by_date[d].hot]
    used_archive = any(w.source == "last-year-archive" for w in ordered)
    tmax_vals = [w.temp_max_c for w in ordered if w.temp_max_c is not None]
    bits = []
    if tmax_vals:
        bits.append(f"highs {min(tmax_vals):.0f}-{max(tmax_vals):.0f}°C")
    bits.append(f"{len(rainy_days)} rainy day(s)" if rainy_days else "no significant rain expected")
    if hot_days:
        bits.append(f"{len(hot_days)} very hot day(s)")
    if used_archive:
        bits.append("beyond the forecast window, using last year's conditions for those dates")
    return WeatherReport(
        latitude=lat, longitude=lon, days=ordered, rainy_days=rainy_days, hot_days=hot_days,
        used_archive=used_archive, summary="; ".join(bits),
    )
