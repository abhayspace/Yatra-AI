"""One conversational turn: load the trip, run the graph, persist the outcome, stream progress."""
from __future__ import annotations

import logging
from typing import Any, Callable, Iterator
from uuid import UUID

from agent.errors import GraphLimitError
from agent.runner import snapshot_of, stream_turn
from agent.settings import ConfigError, Settings
from backend.repository import PersistenceError, TripRepository
from backend.schemas import ApiError, ChatResult

log = logging.getLogger("yatra.service")

NODE_LABELS = {
    "guard_input": "Checking your message",
    "parse_intent": "Understanding your request",
    "clarify": "Working out what to ask",
    "plan": "Planning the steps",
    "call_tools": "Searching destinations and checking weather",
    "build_itinerary": "Building the itinerary",
    "rebuild": "Rebuilding the affected days",
    "check_budget": "Computing the budget",
    "adjust_plan": "Adjusting to fit your budget",
    "synthesize": "Writing the reply",
    "patch": "Updating your plan",
    "parse_followup": "Interpreting your follow-up",
    "apply_delta": "Applying only what changed",
    "refresh_tools": "Refreshing the affected tools",
    "answer_question": "Answering from your plan",
}


class TripNotFound(Exception):
    pass


class ChatService:
    def __init__(self, repo: TripRepository, graph_provider: Callable[[], Any], settings: Settings):
        self.repo = repo
        self._graph_provider = graph_provider
        self.settings = settings

    # ---- reads

    def trip_payload(self, trip: dict[str, Any]) -> dict[str, Any]:
        state = trip.get("state_json") or {}
        return {
            "trip": {
                **{k: v for k, v in trip.items() if k != "state_json"},
                "intent": state.get("intent"),
                "itinerary": state.get("itinerary"),
                "budget_report": state.get("budget_report"),
            },
            "messages": self.repo.list_messages(trip["id"]),
            "versions": self.repo.list_versions(trip["id"]),
        }

    def get_trip(self, trip_id: str) -> dict[str, Any]:
        try:
            UUID(trip_id)
        except ValueError as exc:
            raise TripNotFound() from exc
        trip = self.repo.get_trip(trip_id)
        if not trip:
            raise TripNotFound()
        return trip

    # ---- a turn

    def run_turn(self, trip_id: str | None, message: str) -> Iterator[dict[str, Any]]:
        """Yield progress events and finish with a single `done` or `error` event."""
        try:
            trip = self.get_trip(trip_id) if trip_id else self.repo.create_trip()
            yield {"type": "trip", "trip_id": trip["id"]}
            history = [{"role": m["role"], "content": m["content"]} for m in self.repo.list_messages(trip["id"])]
            self.repo.add_message(trip["id"], "user", message)
            snapshot = trip.get("state_json") or {}

            final = None
            for kind, data in stream_turn(self._graph_provider(), self.settings, message, snapshot, history):
                if kind == "update":
                    node, update = data
                    yield {"type": "step", "node": node, "label": NODE_LABELS.get(node, node)}
                    for call in update.get("tool_trace", []) if isinstance(update, dict) else []:
                        yield {"type": "tool", "call": call}
                else:
                    final = data
            assert final is not None
            yield {"type": "done", "result": self._persist(trip, final).model_dump(mode="json")}
        except TripNotFound:
            yield {"type": "error", "error": ApiError(code="not_found", message="That trip no longer exists.").model_dump()}
        except PersistenceError as exc:
            yield {"type": "error", "error": ApiError(code="database", message=str(exc)).model_dump()}
        except ConfigError as exc:
            yield {"type": "error", "error": ApiError(code="config", message=str(exc)).model_dump()}
        except GraphLimitError as exc:
            yield {"type": "error", "error": ApiError(code="limit", message=str(exc)).model_dump()}
        except Exception:  # noqa: BLE001 - never leak internals to the browser
            log.exception("unhandled error while running a turn")
            yield {"type": "error", "error": ApiError(code="internal", message="Something went wrong on our side. Please try again.").model_dump()}

    def _persist(self, trip: dict[str, Any], final: dict[str, Any]) -> ChatResult:
        trip_id = trip["id"]
        trace = final.get("tool_trace", [])
        if final.get("error"):
            reply = f"I couldn't finish that: {final['error']}"
            kind = (trace[-1].get("result") or {}).get("kind", "tool") if trace else "tool"
            self.repo.add_message(trip_id, "assistant", reply, trace, None, is_error=True)
            return ChatResult(
                trip_id=trip_id, reply=reply, error=ApiError(code=kind, message=final["error"]),
                tool_trace=trace, itinerary=(trip.get("state_json") or {}).get("itinerary"),
                version=trip.get("current_version", 0), warnings=final.get("warnings", []),
            )

        snapshot = snapshot_of(final)
        itinerary, intent = final.get("itinerary"), final.get("intent") or {}
        new_version = final.get("version", 0)
        saved_version = new_version if itinerary and new_version > trip.get("current_version", 0) else None
        if saved_version:
            report = final.get("budget_report")
            self.repo.add_version(trip_id, saved_version, itinerary, report, itinerary["total_cost"], final.get("change_summary", []))
        fields: dict[str, Any] = {
            "state_json": snapshot, "current_version": max(new_version, trip.get("current_version", 0)) if itinerary else trip.get("current_version", 0),
            "origin": intent.get("origin"), "start_date": intent.get("start_date"), "duration_days": intent.get("duration_days"),
            "travelers": intent.get("travelers"), "budget": intent.get("budget"), "interests": intent.get("interests", []),
            "pace": intent.get("pace"),
        }
        if itinerary:
            fields["destination"] = itinerary["destination_name"]
            fields["title"] = f"{itinerary['destination_name'].split(' (')[0]} · {itinerary['duration_days']} days"
        elif not trip.get("title"):
            fields["title"] = "New trip"
            fields["destination"] = None
        else:
            fields["destination"] = None  # no plan yet (asking for details, or a new trip is being clarified)
        self.repo.update_trip(trip_id, fields)
        self.repo.add_message(trip_id, "assistant", final.get("reply", ""), trace, saved_version)
        return ChatResult(
            trip_id=trip_id, reply=final.get("reply", ""), tool_trace=trace, itinerary=itinerary,
            budget_report=final.get("budget_report"), intent=intent or None, version=fields["current_version"],
            change_summary=final.get("change_summary", []), warnings=final.get("warnings", []),
        )
