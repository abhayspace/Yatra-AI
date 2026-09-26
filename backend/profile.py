"""Preference memory: what this browser's earlier trips say about how they like to travel.

Derived from the owner's own saved trips (origin, pace, party size, interests), so it needs no extra storage
and stays scoped to the same owner token as the trips themselves.
"""
from __future__ import annotations

from collections import Counter
from typing import Any


def build_profile(trips: list[dict[str, Any]], exclude_trip_id: str | None = None) -> dict[str, Any] | None:
    rows = [t for t in trips if t.get("destination") and t.get("id") != exclude_trip_id][:10]
    if not rows:
        return None

    def most_common(key: str) -> Any:
        values = [t[key] for t in rows if t.get(key)]
        return Counter(values).most_common(1)[0][0] if values else None

    interests = Counter(i for t in rows for i in (t.get("interests") or []))
    return {
        "origin": most_common("origin"),
        "pace": most_common("pace"),
        "travelers": most_common("travelers"),
        "interests": [i for i, _ in interests.most_common(3)],
        "trips": len(rows),
    }
