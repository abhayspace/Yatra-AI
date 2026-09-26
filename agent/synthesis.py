"""Turns tool results into the assistant's reply.

The language model writes the narration; every figure in it must match what the tools
computed. If the draft quotes an unknown price, calls the trip free, or claims a booking,
it is discarded and a deterministic template built from the same facts is used instead.
"""
from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, Field

from agent.guardrails import allowed_amounts, validate_reply, wrap_user_request
from agent.llm_client import LLMClient
from agent.models import BudgetReport, Itinerary, TripIntent
from agent.prompts import ANSWER_SYSTEM, REPLY_SYSTEM, TURN_KIND_NEW, TURN_KIND_REVISED
from agent.tools.itinerary_builder import TIER_LABEL


class ReplyDraft(BaseModel):
    reply: str = Field(max_length=1500)
    day_themes: list[str] = Field(default_factory=list, max_length=14)


class AnswerDraft(BaseModel):
    answer: str = Field(max_length=1000)


def rupees(x: float) -> str:
    return f"₹{x:,.0f}"


def build_facts(
    intent: TripIntent, itinerary: Itinerary, report: BudgetReport, weather_summary: str | None,
    alternatives: list[str], change_summary: list[str],
) -> dict[str, Any]:
    return {
        "destination": itinerary.destination_name,
        "origin": itinerary.origin,
        "days": itinerary.duration_days,
        "travelers": itinerary.travelers,
        "pace": itinerary.pace,
        "interests": intent.interests,
        "user_budget_inr": report.budget,
        "total_cost_inr": report.total,
        "per_person_inr": report.per_person,
        "budget_status": report.status,
        "over_by_inr": report.overage or None,
        "headroom_inr": report.remaining if report.remaining and report.remaining > 0 else None,
        "cost_breakdown_inr": report.components.model_dump(),
        "transport_mode": itinerary.transport_mode,
        "stay": f"{TIER_LABEL[itinerary.stay_tier]} hotel, {itinerary.nights} night(s), {itinerary.rooms} room(s)",
        "weather": weather_summary or "weather data unavailable",
        "day_plans": [
            {"day": d.day, "activities": [b.title for b in d.blocks if b.kind == "activity"]} for d in itinerary.days
        ],
        "assumptions": intent.assumptions,
        "notes": itinerary.notes,
        "other_destinations_considered": alternatives,
        "change_summary": change_summary,
    }


def template_reply(facts: dict[str, Any], revised: bool) -> str:
    """Deterministic reply built only from tool facts."""
    parts = []
    if revised and facts["change_summary"]:
        parts.append("I've updated your plan. " + " ".join(facts["change_summary"][:4]))
    interests = ", ".join(facts["interests"]) if facts["interests"] else "a mix of experiences"
    parts.append(
        f"Here is a {facts['days']}-day {facts['pace']} trip from {facts['origin']} to {facts['destination']} "
        f"for {facts['travelers']} traveller(s), built around {interests}."
    )
    parts.append(f"The estimated total is {rupees(facts['total_cost_inr'])} ({rupees(facts['per_person_inr'])} per person).")
    parts.append(budget_sentence(facts))
    if facts["weather"]:
        parts.append(f"Weather: {facts['weather']}.")
    return " ".join(p for p in parts if p)


def budget_sentence(facts: dict[str, Any]) -> str:
    status, budget = facts["budget_status"], facts["user_budget_inr"]
    if status == "over_budget":
        return (
            f"Heads up: this is {rupees(facts['over_by_inr'])} over your {rupees(budget)} budget even at the most economical "
            "settings I have, so you may want to shorten the trip, pick a nearer destination or raise the budget."
        )
    if status == "tight":
        return f"It fits your {rupees(budget)} budget, but only just."
    if status == "within_budget":
        room = f" with {rupees(facts['headroom_inr'])} to spare" if facts["headroom_inr"] else ""
        return f"It fits your {rupees(budget)} budget{room}."
    return ""


def compose_reply(
    llm: LLMClient, user_message: str, facts: dict[str, Any], itinerary: Itinerary, report: BudgetReport,
    intent: TripIntent, revised: bool,
) -> tuple[str, list[str] | None, list[str]]:
    """Returns (reply, day_themes or None, guardrail_violations). Violations non-empty means the draft was rejected."""
    system = REPLY_SYSTEM.format(turn_kind=TURN_KIND_REVISED if revised else TURN_KIND_NEW)
    user = f"<trip_facts>\n{json.dumps(facts, ensure_ascii=False)}\n</trip_facts>\n\n{wrap_user_request(user_message)}"
    draft = llm.complete_structured("compose_reply", system, user, ReplyDraft)
    allowed = allowed_amounts(itinerary, report, intent.budget)

    violations = validate_reply(draft.reply, allowed)
    themes = [t.strip() for t in draft.day_themes]
    themes_ok = (
        len(themes) == itinerary.duration_days
        and all(0 < len(t) <= 80 and not validate_reply(t, allowed) and "<" not in t for t in themes)
    )
    if violations:
        return template_reply(facts, revised), None, violations

    reply = draft.reply.strip()
    if report.status == "over_budget" and "over" not in reply.lower():
        reply = f"{reply} {budget_sentence(facts)}"
    return reply, (themes if themes_ok else None), []


def answer_question(llm: LLMClient, question: str, facts: dict[str, Any], itinerary: Itinerary, report: BudgetReport, intent: TripIntent) -> tuple[str, list[str]]:
    user = f"<trip_facts>\n{json.dumps(facts, ensure_ascii=False)}\n</trip_facts>\n\n{wrap_user_request(question)}"
    draft = llm.complete_structured("answer_question", ANSWER_SYSTEM, user, AnswerDraft)
    violations = validate_reply(draft.answer, allowed_amounts(itinerary, report, intent.budget))
    if violations:
        return (
            f"The plan for {facts['destination']} totals {rupees(facts['total_cost_inr'])} for {facts['travelers']} traveller(s). "
            "Ask me to change the days, budget, pace or focus and I'll update it."
        ), violations
    return draft.answer.strip(), []
