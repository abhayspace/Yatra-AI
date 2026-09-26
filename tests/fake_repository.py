"""In-memory stand-in for the Supabase repository, used only by tests."""
from __future__ import annotations

import copy
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from backend.repository import OWNER_KEY, PersistenceError


class InMemoryRepository:
    def __init__(self):
        self.trips: dict[str, dict[str, Any]] = {}
        self.messages: list[dict[str, Any]] = []
        self.versions: list[dict[str, Any]] = []
        self._tick = 0
        self.fail = False

    def _now(self) -> str:
        self._tick += 1
        return (datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(seconds=self._tick)).isoformat()

    def _check(self):
        if self.fail:
            raise PersistenceError("The database (Supabase) could not be reached.")

    def create_trip(self, owner_hash):
        self._check()
        now = self._now()
        trip = {"id": str(uuid.uuid4()), "created_at": now, "updated_at": now, "title": None, "origin": None, "destination": None,
                "start_date": None, "duration_days": None, "travelers": None, "budget": None, "interests": [], "pace": None,
                "state_json": {OWNER_KEY: owner_hash}, "current_version": 0}
        self.trips[trip["id"]] = trip
        return copy.deepcopy(trip)

    def get_trip(self, trip_id):
        self._check()
        return copy.deepcopy(self.trips.get(trip_id))

    def _owned(self, owner_hash):
        return [t for t in self.trips.values() if t["state_json"].get(OWNER_KEY) == owner_hash]

    def list_trips(self, owner_hash, limit=30):
        self._check()
        rows = sorted(self._owned(owner_hash), key=lambda t: t["updated_at"], reverse=True)[:limit]
        return [{k: v for k, v in copy.deepcopy(t).items() if k != "state_json"} for t in rows]

    def latest_trip(self, owner_hash):
        self._check()
        rows = sorted(self._owned(owner_hash), key=lambda t: t["updated_at"], reverse=True)
        return copy.deepcopy(rows[0]) if rows else None

    def update_trip(self, trip_id, fields):
        self._check()
        self.trips[trip_id].update(copy.deepcopy(fields))
        self.trips[trip_id]["updated_at"] = self._now()
        return copy.deepcopy(self.trips[trip_id])

    def add_message(self, trip_id, role, content, tool_trace=None, itinerary_version=None, is_error=False):
        self._check()
        row = {"id": str(uuid.uuid4()), "trip_id": trip_id, "role": role, "content": content, "tool_trace": copy.deepcopy(tool_trace or []),
               "itinerary_version": itinerary_version, "is_error": is_error, "created_at": self._now()}
        self.messages.append(row)
        return copy.deepcopy(row)

    def list_messages(self, trip_id):
        self._check()
        return copy.deepcopy([m for m in self.messages if m["trip_id"] == trip_id])

    def add_version(self, trip_id, version_number, itinerary, budget, total_cost, change_summary):
        self._check()
        if any(v["trip_id"] == trip_id and v["version_number"] == version_number for v in self.versions):
            raise PersistenceError("The database (Supabase) rejected the request (23505).")
        row = {"id": str(uuid.uuid4()), "trip_id": trip_id, "version_number": version_number, "itinerary_json": copy.deepcopy(itinerary),
               "budget_json": copy.deepcopy(budget), "total_cost": total_cost, "change_summary": list(change_summary), "created_at": self._now()}
        self.versions.append(row)
        return copy.deepcopy(row)

    def list_versions(self, trip_id):
        self._check()
        return copy.deepcopy(sorted((v for v in self.versions if v["trip_id"] == trip_id), key=lambda v: v["version_number"]))
