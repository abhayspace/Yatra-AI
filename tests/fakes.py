"""Test doubles: a scripted language model and a fake Open-Meteo transport.

ScriptedLLM implements the same LLMClient interface as the Azure AI Foundry client. It reads
the request text with the rule-based extractors and writes replies from the facts it is given,
so graph plumbing, tools, guardrails and persistence can be tested offline and repeatably.
Semantic quality of the real model is checked by the live evals instead.
"""
from __future__ import annotations

import json
import re
from datetime import date, timedelta

import httpx

from agent.llm_client import LLMClient
from agent.tools.intent_parser import (
    _CHANGE_VERB, _QUESTION_START, LLMIntentOut, heuristic_delta, heuristic_extract,
)
from agent.models import TripIntent

TODAY = date(2026, 10, 1)


def _between(text: str, open_tag: str, close_tag: str) -> str:
    """Contents of the last <tag>...</tag> block; the current request always comes last in a prompt."""
    found = re.findall(re.escape(open_tag) + r"\n?(.*?)\n?" + re.escape(close_tag), text, re.S)
    return found[-1] if found else ""


class ScriptedLLM(LLMClient):
    def __init__(self, today: date = TODAY):
        self.today = today
        self.calls: list[tuple[str, str, str]] = []

    def complete_structured(self, task, system, user, schema):
        self.calls.append((task, system, user))
        request = _between(user, "<user_request>", "</user_request>")
        if task == "parse_intent":
            h = heuristic_extract(request, self.today)
            data = {k: v for k, v in h.items() if k in LLMIntentOut.model_fields}
            if "destinations" not in data:  # a real model would also pick up places the dataset does not know
                origin = h.get("origin", "")
                stop = {"explore", "plan", "visit", "see", "have", "go", "get", "the", "a", "an", "my", "our", "make", "nature", "food", "beach"}
                names = [n for n in re.findall(r"\b(?:in|to|visit)\s+([A-Za-z]{3,})\b", request)
                         if n.lower() not in stop and n.lower() != origin.lower() and not n.isdigit()]
                if names:
                    data["destinations"] = names[:1]
            return schema(**data)
        if task == "parse_followup":
            facts = _between(user, "<trip_facts>", "</trip_facts>")
            intent = TripIntent(travelers=2)
            delta = heuristic_delta(request, intent, self.today)
            low = request.lower()
            if re.search(r"new trip|start over|different trip", low):
                action = "new_trip"
            elif delta:
                action = "modify"
            elif _QUESTION_START.match(request) and not _CHANGE_VERB.search(request):
                action = "question"
            else:
                action = "other"
            d = {k: (v.isoformat() if isinstance(v, date) else v) for k, v in delta.items()}
            return schema(action=action, delta=d, question=request if action == "question" else None)
        if task == "plan_tools":
            facts = json.loads(_between(user, "<trip_facts>", "</trip_facts>"))
            tools = ["weather"] + ([] if facts.get("destinations") else ["compare_alternatives"])
            return schema(tools=tools, rationale="Scripted: forecast always, comparison when recommending a destination.")
        if task == "compose_reply":
            facts = json.loads(_between(user, "<trip_facts>", "</trip_facts>"))
            return schema(reply=self.reply_text(facts, request), day_themes=self.themes(facts))
        if task == "answer_question":
            facts = json.loads(_between(user, "<trip_facts>", "</trip_facts>"))
            return schema(answer=f"The plan for {facts['destination']} totals ₹{facts['total_cost_inr']:,.0f}.")
        raise AssertionError(f"unexpected task {task}")

    def reply_text(self, facts, request: str) -> str:
        line = (
            f"Your {facts['days']}-day trip to {facts['destination']} comes to ₹{facts['total_cost_inr']:,.0f} "
            f"(₹{facts['per_person_inr']:,.0f} per person)."
        )
        if facts["change_summary"]:
            line = "Updated. " + facts["change_summary"][0] + " " + line
        return line

    def themes(self, facts) -> list[str]:
        return [f"Day {p['day']} highlights" for p in facts["day_plans"]]


class InjectionCompliantLLM(ScriptedLLM):
    """Worst case: a model that obeys instructions embedded in the user's message."""

    def reply_text(self, facts, request: str) -> str:
        if "free" in request.lower():
            return "Great news! The trip is free, so ₹0 total and no cost at all."
        return super().reply_text(facts, request)


class InventedPriceLLM(ScriptedLLM):
    def reply_text(self, facts, request: str) -> str:
        return f"Hotels there are only ₹1,234 a night and I've booked your flight to {facts['destination']}."


CODES = {"clear": 1, "rain": 63}


def weather_transport(rainy_offsets: set[int] | None = None, hot: bool = False, fail: bool = False) -> httpx.MockTransport:
    """Open-Meteo lookalike that answers forecast and archive calls with plausible data."""
    calls: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        if fail:
            raise httpx.ConnectError("offline")
        start = date.fromisoformat(request.url.params["start_date"])
        end = date.fromisoformat(request.url.params["end_date"])
        n = (end - start).days + 1
        days = [(start + timedelta(days=i)).isoformat() for i in range(n)]
        archive = "archive" in request.url.host
        wet = [(i in (rainy_offsets or set())) for i in range(n)]
        daily = {
            "time": days,
            "weather_code": [63 if w else 1 for w in wet],
            "temperature_2m_max": [40.0 if hot else 28.0] * n,
            "temperature_2m_min": [20.0] * n,
            "precipitation_sum": [12.0 if w else 0.0 for w in wet],
        }
        if not archive:
            daily["precipitation_probability_max"] = [85 if w else 5 for w in wet]
        return httpx.Response(200, json={"daily": daily})

    transport = httpx.MockTransport(handler)
    transport.calls = calls  # type: ignore[attr-defined]
    return transport
