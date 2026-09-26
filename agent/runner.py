"""Helpers to run one conversational turn through the graph.

The API layer and the eval harness both go through here so a turn behaves the same everywhere:
persisted trip state goes in, one new user message is added, and the resulting state comes out.
"""
from __future__ import annotations

from typing import Any, Iterator

from langgraph.errors import GraphRecursionError

from agent.errors import GraphLimitError
from agent.graph import run_config
from agent.settings import Settings
from agent.state import TripState

# State that survives between turns (and is stored with the trip). Everything else is per-turn.
PERSISTENT_KEYS = ("intent", "candidates", "weather", "itinerary", "budget_report", "plan_rung", "version")


def initial_state(message: str, snapshot: dict[str, Any] | None = None, history: list[dict[str, str]] | None = None) -> TripState:
    state: TripState = {
        "user_message": message,
        "history": list(history or [])[-8:],
        "version": 0,
        "tool_trace": [],
        "warnings": [],
        "step_count": 0,
    }
    for key in PERSISTENT_KEYS:
        if snapshot and snapshot.get(key) is not None:
            state[key] = snapshot[key]  # type: ignore[literal-required]
    return state


def snapshot_of(final: TripState) -> dict[str, Any]:
    """The part of a finished turn's state that should be stored with the trip."""
    return {k: final.get(k) for k in PERSISTENT_KEYS if final.get(k) is not None}  # type: ignore[misc]


def _limit_error(settings: Settings) -> GraphLimitError:
    return GraphLimitError(f"The request needed more than {settings.max_graph_steps} steps and was stopped.")


def run_turn(graph, settings: Settings, message: str, snapshot: dict[str, Any] | None = None,
             history: list[dict[str, str]] | None = None) -> TripState:
    try:
        return graph.invoke(initial_state(message, snapshot, history), run_config(settings))
    except GraphRecursionError as exc:
        raise _limit_error(settings) from exc


def stream_turn(graph, settings: Settings, message: str, snapshot: dict[str, Any] | None = None,
                history: list[dict[str, str]] | None = None) -> Iterator[tuple[str, Any]]:
    """Yield ("update", (node, update)) per finished node, then ("final", state)."""
    final: TripState | None = None
    try:
        for namespace, mode, data in graph.stream(
            initial_state(message, snapshot, history), run_config(settings),
            stream_mode=["updates", "values"], subgraphs=True,
        ):
            if mode == "updates":
                for node, update in data.items():
                    yield "update", (node, update)
            elif not namespace:
                final = data
    except GraphRecursionError as exc:
        raise _limit_error(settings) from exc
    assert final is not None
    yield "final", final
