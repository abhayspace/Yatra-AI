"""Runs eval cases through the real graph and checks trajectory + itinerary expectations."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from agent.data import get_destination
from agent.models import Itinerary
from agent.runner import run_turn, snapshot_of
from agent.settings import Settings

DATASET = Path(__file__).with_name("dataset.jsonl")


def load_cases(path: Path = DATASET) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


@dataclass
class TurnResult:
    user: str
    state: dict[str, Any]
    failures: list[str] = field(default_factory=list)


@dataclass
class CaseResult:
    case_id: str
    turns: list[TurnResult]

    @property
    def failures(self) -> list[str]:
        return [f"[{self.case_id} turn {i + 1}] {f}" for i, t in enumerate(self.turns) for f in t.failures]

    @property
    def passed(self) -> bool:
        return not self.failures


def tool_names(state: dict[str, Any]) -> list[str]:
    return [t["name"] for t in state.get("tool_trace", [])]


def _is_subsequence(needle: list[str], haystack: list[str]) -> bool:
    it = iter(haystack)
    return all(any(x == y for y in it) for x in needle)


def _themed_count(itinerary: dict[str, Any], theme: str) -> int:
    it = Itinerary.model_validate(itinerary)
    dest = get_destination(it.destination_id)
    by_id = {a.id: a for a in dest.attractions}
    return sum(theme in by_id[b.place_id].themes for d in it.days for b in d.blocks if b.kind == "activity" and b.place_id in by_id)


def _activities(itinerary: dict[str, Any]) -> list[list[str]]:
    it = Itinerary.model_validate(itinerary)
    return [[b.place_id for b in d.blocks if b.kind == "activity"] for d in it.days]


def check_turn(expect: dict[str, Any], state: dict[str, Any], prev: dict[str, Any] | None, live: bool) -> list[str]:
    """Return a list of failed expectations for one turn."""
    out: list[str] = []
    names = tool_names(state)
    if "tool_sequence" in expect and not _is_subsequence(expect["tool_sequence"], names):
        out.append(f"tool sequence {expect['tool_sequence']} not found in {names}")
    for tool in expect.get("tools_absent", []):
        if tool in names:
            out.append(f"tool {tool} should not have run (ran: {names})")
    if expect.get("no_error") and state.get("error"):
        out.append(f"unexpected error: {state['error']}")

    intent = state.get("intent") or {}
    for key, value in expect.get("intent", {}).items():
        if intent.get(key) != value:
            out.append(f"intent.{key} = {intent.get(key)!r}, expected {value!r}")
    for interest in expect.get("intent_interests_include", []):
        if interest not in intent.get("interests", []):
            out.append(f"intent.interests missing {interest}")

    it = state.get("itinerary")
    if expect.get("no_itinerary") and it:
        out.append("an itinerary was produced but a clarifying question was expected")
    if expect.get("itinerary_unchanged"):
        if not prev or state.get("itinerary") != prev.get("itinerary"):
            out.append("itinerary changed but should not have")
    spec = expect.get("itinerary")
    if spec:
        if not it:
            out.append("no itinerary produced")
        else:
            out.extend(_check_itinerary(spec, state, prev))
    if "budget_status_in" in expect:
        status = (state.get("budget_report") or {}).get("status")
        if status not in expect["budget_status_in"]:
            out.append(f"budget status {status!r} not in {expect['budget_status_in']}")
    if "version" in expect and state.get("version") != expect["version"]:
        out.append(f"version {state.get('version')} != {expect['version']}")
    if expect.get("guard_flagged") and not any(t["name"] == "input_guard" and t["status"] == "flagged" for t in state.get("tool_trace", [])):
        out.append("input guard did not flag the injection")
    reply = state.get("reply", "")
    for pat in expect.get("reply_matches", []):
        if not re.search(pat, reply):
            out.append(f"reply does not match /{pat}/: {reply!r}")
    for pat in expect.get("reply_not_matches", []):
        if re.search(pat, reply):
            out.append(f"reply matches forbidden /{pat}/: {reply!r}")
    joined = " ".join(state.get("change_summary", []))
    for text in expect.get("changes_include", []):
        if text not in joined:
            out.append(f"change summary missing {text!r}: {joined!r}")
    return out


def _check_itinerary(spec: dict[str, Any], state: dict[str, Any], prev: dict[str, Any] | None) -> list[str]:
    out: list[str] = []
    it = Itinerary.model_validate(state["itinerary"])
    budget = (state.get("intent") or {}).get("budget")
    report = state.get("budget_report") or {}
    if "duration_days" in spec and it.duration_days != spec["duration_days"]:
        out.append(f"duration {it.duration_days} != {spec['duration_days']}")
    if spec.get("total_lte_budget") and budget and it.total_cost > budget:
        out.append(f"total {it.total_cost} exceeds budget {budget}")
    if spec.get("total_positive") and it.total_cost <= 0:
        out.append("total cost is not positive")
    if "destination_in" in spec and it.destination_id not in spec["destination_in"]:
        out.append(f"destination {it.destination_id} not in {spec['destination_in']}")
    if "stay_tier_in" in spec and it.stay_tier not in spec["stay_tier_in"]:
        out.append(f"stay tier {it.stay_tier} not in {spec['stay_tier_in']}")
    per_day = [sum(1 for b in d.blocks if b.kind == "activity") for d in it.days]
    if "max_activities_per_day" in spec and max(per_day) > spec["max_activities_per_day"]:
        out.append(f"{max(per_day)} activities in a day exceeds pace limit {spec['max_activities_per_day']}")
    if "min_total_activities" in spec and sum(per_day) < spec["min_total_activities"]:
        out.append(f"only {sum(per_day)} activities")
    for theme in spec.get("themes_present", []):
        if _themed_count(state["itinerary"], theme) < 1:
            out.append(f"no activity matches interest {theme}")
    if prev and prev.get("itinerary"):
        if spec.get("same_destination_as_prev") and prev["itinerary"]["destination_id"] != it.destination_id:
            out.append("destination changed but should have stayed")
        for theme in spec.get("themed_increase", []):
            before, after = _themed_count(prev["itinerary"], theme), _themed_count(state["itinerary"], theme)
            if after <= before:
                out.append(f"{theme} activities did not increase ({before} -> {after})")
        for theme in spec.get("themed_decrease", []):
            before, after = _themed_count(prev["itinerary"], theme), _themed_count(state["itinerary"], theme)
            if after >= before:
                out.append(f"{theme} activities did not decrease ({before} -> {after})")
    if spec.get("rainy_days_indoor_or_annotated"):
        for d in it.days:
            if d.weather and d.weather.rainy:
                for b in d.blocks:
                    if b.kind == "activity" and not b.indoor and not b.weather_note:
                        out.append(f"day {d.day}: outdoor activity {b.title} on a rainy day without a note")
    if report and report.get("status") not in (None, "over_budget") and spec.get("total_lte_budget") and budget:
        if report["total"] > budget:
            out.append("budget report inconsistent with itinerary")
    return out


def run_case(case: dict[str, Any], graph, settings: Settings, live: bool = False) -> CaseResult:
    """Run every turn of a case through the graph, carrying persisted state between turns."""
    snapshot: dict[str, Any] | None = None
    history: list[dict[str, str]] = []
    prev_state: dict[str, Any] | None = None
    results: list[TurnResult] = []
    for turn in case["turns"]:
        state = run_turn(graph, settings, turn["user"], snapshot, history)
        failures = check_turn(turn.get("expect", {}), state, prev_state, live)
        results.append(TurnResult(turn["user"], dict(state), failures))
        history += [{"role": "user", "content": turn["user"]}, {"role": "assistant", "content": state.get("reply", "")}]
        snapshot = snapshot_of(state)
        prev_state = dict(state)
    return CaseResult(case["id"], results)
