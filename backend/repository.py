"""Persistence for trips, conversation turns and itinerary versions in Supabase.

Only the backend holds the service role key; the browser never talks to Supabase.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Any, Protocol

import httpx
from postgrest.exceptions import APIError
from supabase import Client, create_client

from agent.settings import get_settings


class PersistenceError(RuntimeError):
    """Supabase could not be reached or rejected the request."""


class TripRepository(Protocol):
    def create_trip(self) -> dict[str, Any]: ...
    def get_trip(self, trip_id: str) -> dict[str, Any] | None: ...
    def list_trips(self, limit: int = 30) -> list[dict[str, Any]]: ...
    def latest_trip(self) -> dict[str, Any] | None: ...
    def update_trip(self, trip_id: str, fields: dict[str, Any]) -> dict[str, Any]: ...
    def add_message(self, trip_id: str, role: str, content: str, tool_trace: list[dict] | None = None,
                    itinerary_version: int | None = None, is_error: bool = False) -> dict[str, Any]: ...
    def list_messages(self, trip_id: str) -> list[dict[str, Any]]: ...
    def add_version(self, trip_id: str, version_number: int, itinerary: dict, budget: dict | None,
                    total_cost: float, change_summary: list[str]) -> dict[str, Any]: ...
    def list_versions(self, trip_id: str) -> list[dict[str, Any]]: ...


TRIP_LIST_COLUMNS = "id,created_at,updated_at,title,origin,destination,start_date,duration_days,travelers,budget,interests,pace,current_version"


def _wrap(fn):
    def inner(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except APIError as exc:
            raise PersistenceError(f"The database (Supabase) rejected the request ({exc.code or 'error'}).") from exc
        except (httpx.HTTPError, OSError) as exc:
            raise PersistenceError("The database (Supabase) could not be reached.") from exc

    inner.__name__ = fn.__name__
    return inner


class SupabaseRepository:
    def __init__(self, url: str, service_role_key: str):
        self._db: Client = create_client(url, service_role_key)

    @_wrap
    def create_trip(self) -> dict[str, Any]:
        return self._db.table("trips").insert({}).execute().data[0]

    @_wrap
    def get_trip(self, trip_id: str) -> dict[str, Any] | None:
        rows = self._db.table("trips").select("*").eq("id", trip_id).limit(1).execute().data
        return rows[0] if rows else None

    @_wrap
    def list_trips(self, limit: int = 30) -> list[dict[str, Any]]:
        return self._db.table("trips").select(TRIP_LIST_COLUMNS).order("updated_at", desc=True).limit(limit).execute().data

    @_wrap
    def latest_trip(self) -> dict[str, Any] | None:
        rows = self._db.table("trips").select("*").order("updated_at", desc=True).limit(1).execute().data
        return rows[0] if rows else None

    @_wrap
    def update_trip(self, trip_id: str, fields: dict[str, Any]) -> dict[str, Any]:
        return self._db.table("trips").update(fields).eq("id", trip_id).execute().data[0]

    @_wrap
    def add_message(self, trip_id, role, content, tool_trace=None, itinerary_version=None, is_error=False):
        row = {"trip_id": trip_id, "role": role, "content": content, "tool_trace": tool_trace or [],
               "itinerary_version": itinerary_version, "is_error": is_error}
        return self._db.table("messages").insert(row).execute().data[0]

    @_wrap
    def list_messages(self, trip_id: str) -> list[dict[str, Any]]:
        return self._db.table("messages").select("*").eq("trip_id", trip_id).order("created_at").execute().data

    @_wrap
    def add_version(self, trip_id, version_number, itinerary, budget, total_cost, change_summary):
        row = {"trip_id": trip_id, "version_number": version_number, "itinerary_json": itinerary,
               "budget_json": budget, "total_cost": total_cost, "change_summary": change_summary}
        return self._db.table("itinerary_versions").insert(row).execute().data[0]

    @_wrap
    def list_versions(self, trip_id: str) -> list[dict[str, Any]]:
        return (self._db.table("itinerary_versions").select("*").eq("trip_id", trip_id)
                .order("version_number").execute().data)


@lru_cache
def get_repository() -> TripRepository:
    settings = get_settings()
    settings.require_supabase()
    return SupabaseRepository(settings.supabase_url, settings.supabase_service_role_key.get_secret_value())
