"""Shared helpers for tests."""
from datetime import date

from agent.tools.destination_search import search_places
from agent.tools.itinerary_builder import build_itinerary


def sample_itinerary(dest="goa", origin="Mumbai", days=3, travelers=2, rung=1):
    return build_itinerary(dict(
        destination_id=dest, origin=origin, start_date=date(2026, 12, 4), duration_days=days, travelers=travelers,
        pace="balanced", interests=["food", "beach"], rung=rung, places=search_places(dest, ["food", "beach"]),
    ))
