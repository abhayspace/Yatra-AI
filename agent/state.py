"""Typed state carried through the LangGraph state machine.

Values are plain JSON-friendly dicts (pydantic models are dumped with mode="json") so the
whole state can be stored in Supabase and restored for a follow-up turn.
"""
from __future__ import annotations

import operator
from typing import Annotated, Any, TypedDict


class TripState(TypedDict, total=False):
    # inputs supplied by the API layer
    user_message: str  # sanitised raw text of the latest turn (treated as data)
    history: list[dict[str, str]]  # recent {"role", "content"} turns for context
    version: int  # latest saved itinerary version (0 for a brand new trip)

    # understanding
    intent: dict[str, Any]  # TripIntent
    missing_fields: list[str]  # what is needed before planning can start
    delta: dict[str, Any]  # FollowUpParse for a follow-up turn
    affected: list[str]  # which constraints the follow-up changed

    # planning
    tool_plan: list[dict[str, Any]]  # ordered tool calls decided by the plan node
    candidates: dict[str, Any]  # destination_search result
    weather: dict[str, Any]  # weather tool result
    plan_rung: int  # position on the comfort/cost ladder
    revisions: int  # how many times budget adjustment has re-planned

    # results
    itinerary: dict[str, Any]  # Itinerary
    budget_report: dict[str, Any]  # BudgetReport
    change_summary: list[str]  # human-readable diff vs the previous version
    reply: str  # assistant message for this turn

    # bookkeeping
    tool_trace: Annotated[list[dict[str, Any]], operator.add]  # ToolCall per tool fired
    warnings: Annotated[list[str], operator.add]
    error: str | None
    step_count: int  # incremented by every node; enforced against MAX_GRAPH_STEPS
