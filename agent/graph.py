"""LangGraph state machine for Yatra AI.

Main graph:
    guard_input -> should_replan? --no--> parse_intent -> (clarify | plan -> call_tools -> build_itinerary
                                             -> check_budget -> (adjust_plan -> build_itinerary)* -> synthesize)
                                  --yes-> patch (subgraph)

The patch subgraph handles a follow-up on an existing trip without re-running the whole
pipeline:
    parse_followup -> answer_question | apply_delta -> refresh_tools -> rebuild -> check_budget
                   -> (adjust_plan -> rebuild)* -> synthesize
Only the tools affected by the changed constraints run again, and untouched days are kept.

Every node bumps step_count and is refused once MAX_GRAPH_STEPS is exceeded; the compiled graph
also carries LangGraph's own recursion_limit set to the same number.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import date
from typing import Any, Callable, Literal

import httpx
from langgraph.graph import END, START, StateGraph

from agent.data import find_origin, get_destination, load_dataset, match_destinations
from agent.errors import GraphLimitError, LLMError, ToolError
from agent.guardrails import detect_injection, sanitize_user_text
from agent.llm_client import LLMClient
from agent.models import BudgetReport, Itinerary, ToolCall, TripIntent, FollowUpParse
from agent.settings import Settings, get_settings
from agent.state import TripState
from agent.synthesis import answer_question, build_facts, compose_reply, rupees
from agent.tools.budget import compute_budget
from agent.tools.destination_search import PlaceMatches, SearchQuery, SearchResult, search_destinations, search_places
from agent.tools.intent_parser import apply_defaults, apply_delta, parse_followup, parse_intent
from agent.tools.itinerary_builder import LADDER, LAST_RUNG, TIER_LABEL, BuildRequest, build_itinerary, diff_itineraries, initial_rung
from agent.tools.weather import WeatherReport, fetch_weather


@dataclass
class Deps:
    """Everything the graph needs from the outside world, injected so tests can control it."""

    llm: LLMClient
    settings: Settings = field(default_factory=get_settings)
    http_client: httpx.Client | None = None
    today: Callable[[], date] = date.today


# --------------------------------------------------------------------------- helpers


def _call(name: str, label: str, started: float, summary: str, args: dict | None = None, result: dict | None = None,
          status: Literal["ok", "error", "flagged"] = "ok") -> dict[str, Any]:
    return ToolCall(
        name=name, label=label, status=status, args=args or {}, summary=summary, result=result or {},
        duration_ms=int((time.perf_counter() - started) * 1000),
    ).model_dump()


def _intent(state: TripState) -> TripIntent:
    return TripIntent.model_validate(state["intent"])


def _describe_intent(i: TripIntent) -> str:
    bits = []
    if i.duration_days:
        bits.append(f"{i.duration_days} days")
    if i.travelers:
        bits.append(f"{i.travelers} traveller(s)")
    if i.budget:
        bits.append(rupees(i.budget))
    if i.interests:
        bits.append(", ".join(i.interests))
    if i.pace:
        bits.append(i.pace)
    if i.origin:
        bits.append(f"from {i.origin}")
    return " · ".join(bits) or "no constraints yet"


def _supported_origins() -> str:
    return ", ".join(sorted(load_dataset().origins))


# --------------------------------------------------------------------------- shared tool runners


def _run_destination_search(intent: TripIntent, today: date) -> tuple[SearchResult, dict[str, Any]]:
    started = time.perf_counter()
    query = SearchQuery(
        origin=intent.origin, destinations=intent.destinations, region=intent.region, interests=intent.interests,
        interest_weights=intent.interest_weights, budget=intent.budget, duration_days=intent.duration_days or 3,
        travelers=intent.travelers or 1, start_date=intent.start_date,
    )
    result = search_destinations(query)
    if result.chosen_id:
        top = result.candidates[0]
        others = ", ".join(c.name.split(" (")[0] for c in result.candidates[1:])
        summary = f"Picked {top.name} (score {top.score:g})" + (f"; also considered {others}" if others else "")
    elif result.unknown_names:
        summary = f"No data for {', '.join(result.unknown_names)}"
    else:
        summary = "No matching destination"
    entry = _call("destination_search", "Searched destinations", started, summary,
                  args={"origin": intent.origin, "interests": intent.interests, "named": intent.destinations or ([intent.region] if intent.region else [])},
                  result={"candidates": [{"id": c.destination_id, "name": c.name, "score": c.score, "reasons": c.reasons,
                                          "min_cost": c.min_cost_estimate} for c in result.candidates]},
                  status="ok" if result.chosen_id else "flagged")
    return result, entry


def _run_places(dest_id: str, intent: TripIntent) -> tuple[PlaceMatches, dict[str, Any]]:
    started = time.perf_counter()
    places = search_places(dest_id, intent.interests, intent.interest_weights)
    dest = get_destination(dest_id)
    top = [s.attraction.name for s in places.attractions[:4]]
    entry = _call("place_search", "Looked up attractions and restaurants", started,
                  f"{len(places.attractions)} attractions and {len(places.restaurants)} restaurants in {dest.name.split(' (')[0]}; top fits: {', '.join(top)}",
                  args={"destination": dest_id, "interests": intent.interests, "weights": intent.interest_weights},
                  result={"top_attractions": top})
    return places, entry


def _run_weather(dest_id: str, intent: TripIntent, deps: Deps) -> tuple[WeatherReport | None, dict[str, Any], list[str]]:
    started = time.perf_counter()
    dest = get_destination(dest_id)
    try:
        report = fetch_weather(dest.lat, dest.lon, intent.start_date, intent.duration_days or 3, client=deps.http_client, today=deps.today())
    except ToolError as exc:
        entry = _call("weather", "Checked weather", started, f"{exc} Planned without a forecast.",
                      args={"lat": dest.lat, "lon": dest.lon, "start": intent.start_date.isoformat()}, status="error")
        return None, entry, ["Weather data was unavailable, so activities were not adjusted for weather."]
    entry = _call("weather", "Checked weather", started, report.summary,
                  args={"source": "Open-Meteo", "start": intent.start_date.isoformat(), "days": intent.duration_days},
                  result={"rainy_days": report.rainy_days, "hot_days": report.hot_days,
                          "days": [{"date": d.date, "summary": d.summary, "max_c": d.temp_max_c, "rain_pct": d.precip_probability} for d in report.days]})
    return report, entry, []


# --------------------------------------------------------------------------- node factory


def make_nodes(deps: Deps) -> dict[str, Callable[[TripState], dict[str, Any]]]:
    llm, settings = deps.llm, deps.settings

    def _wrap(fn: Callable[[TripState], dict[str, Any]], name: str, label: str) -> Callable[[TripState], dict[str, Any]]:
        def wrapper(state: TripState) -> dict[str, Any]:
            steps = state.get("step_count", 0) + 1
            if steps > settings.max_graph_steps:
                raise GraphLimitError(f"Exceeded the maximum of {settings.max_graph_steps} graph steps.")
            started = time.perf_counter()
            try:
                update = fn(state)
            except (LLMError, ToolError) as exc:
                return {"step_count": steps, "error": str(exc),
                        "tool_trace": [_call(name, label, started, str(exc), status="error")]}
            update["step_count"] = steps
            return update

        wrapper.__name__ = name
        return wrapper

    # ---- shared

    def guard_input(state: TripState) -> dict[str, Any]:
        started = time.perf_counter()
        raw = state.get("user_message", "")
        clean = sanitize_user_text(raw, settings.max_message_chars)
        flags = detect_injection(raw)
        update: dict[str, Any] = {"user_message": clean}
        if flags:
            update["tool_trace"] = [_call(
                "input_guard", "Input safety check", started,
                "Your message contained instruction-like text. It is treated as data only and cannot change budget rules or costs.",
                args={"patterns": flags}, status="flagged")]
        return update

    def parse_intent_node(state: TripState) -> dict[str, Any]:
        started = time.perf_counter()
        prior = _intent(state) if state.get("intent") else None
        result = parse_intent(state["user_message"], llm, prior, deps.today())
        return {
            "intent": result.intent.model_dump(mode="json"),
            "missing_fields": result.missing,
            "tool_trace": [_call("intent_parser", "Understood your request", started, _describe_intent(result.intent),
                                 args={"explicit_values": result.heuristics},
                                 result=result.intent.model_dump(mode="json", exclude={"assumptions"}, exclude_none=True))],
        }

    def clarify(state: TripState) -> dict[str, Any]:
        intent = _intent(state)
        missing = state.get("missing_fields", [])
        parts: list[str] = []
        if "origin" in missing:
            if intent.origin:
                parts.append(f"I don't have fares from {intent.origin} yet. I can plan trips from: {_supported_origins()}. Which of these is closest?")
            else:
                parts.append("Where will you be travelling from?")
        if "destination_or_interests" in missing:
            parts.append("Where would you like to go, or what kind of trip do you want (for example nature, food, beaches, heritage)?")
        if "known_destination" in missing:
            names = ", ".join((state.get("candidates") or {}).get("unknown", [])) or "that place"
            options = ", ".join(c["name"].split(" (")[0] for c in (state.get("candidates") or {}).get("alternatives", []))
            parts.append(f"I don't have data for {names} yet." + (f" Based on your interests I could plan {options} instead. Should I go with one of those?" if options else ""))
        return {
            "reply": " ".join(parts) or "Could you tell me a little more about the trip?",
            "tool_trace": [_call("clarify", "Asked for missing details", time.perf_counter(),
                                 "Needs: " + ", ".join(missing).replace("_", " "), status="flagged")],
        }

    # ---- planning path

    def plan(state: TripState) -> dict[str, Any]:
        started = time.perf_counter()
        intent = apply_defaults(_intent(state), deps.today())
        tool_plan = [
            {"tool": "destination_search"}, {"tool": "place_search"}, {"tool": "weather"},
            {"tool": "itinerary_builder"}, {"tool": "budget"},
        ]
        rung = initial_rung(intent.budget, intent.duration_days, intent.travelers)
        return {
            "intent": intent.model_dump(mode="json"),
            "tool_plan": tool_plan,
            "plan_rung": rung,
            "revisions": 0,
            "tool_trace": [_call("plan", "Planned the steps", started,
                                 " → ".join(t["tool"].replace("_", " ") for t in tool_plan),
                                 result={"assumptions": intent.assumptions})],
        }

    def call_tools(state: TripState) -> dict[str, Any]:
        intent = _intent(state)
        trace: list[dict[str, Any]] = []
        warnings: list[str] = []
        update: dict[str, Any] = {}
        candidates: dict[str, Any] = {}
        for step in state.get("tool_plan", []):
            tool = step["tool"]
            if tool == "destination_search":
                result, entry = _run_destination_search(intent, deps.today())
                trace.append(entry)
                candidates["search"] = result.model_dump(mode="json")
                if not result.chosen_id:
                    unknown = result.unknown_names
                    candidates.update(unknown=unknown, alternatives=[c.model_dump(mode="json") for c in result.candidates])
                    update.update(candidates=candidates, missing_fields=["known_destination"], tool_trace=trace)
                    return update
                candidates["chosen_id"] = result.chosen_id
            elif tool == "place_search":
                places, entry = _run_places(candidates["chosen_id"], intent)
                trace.append(entry)
                candidates["places"] = places.model_dump(mode="json")
            elif tool == "weather":
                report, entry, warn = _run_weather(candidates["chosen_id"], intent, deps)
                trace.append(entry)
                warnings.extend(warn)
                update["weather"] = report.model_dump(mode="json") if report else {}
        update.update(candidates=candidates, tool_trace=trace, warnings=warnings, missing_fields=[])
        return update

    def build_node(state: TripState) -> dict[str, Any]:
        started = time.perf_counter()
        intent = _intent(state)
        cands = state["candidates"]
        rung = state.get("plan_rung", 1)
        locked = _locked_days(state, intent)
        weather = WeatherReport.model_validate(state["weather"]) if state.get("weather") else None
        itinerary = build_itinerary(BuildRequest(
            destination_id=cands["chosen_id"], origin=intent.origin, start_date=intent.start_date,
            duration_days=intent.duration_days, travelers=intent.travelers, pace=intent.pace, interests=intent.interests,
            rung=rung, places=PlaceMatches.model_validate(cands["places"]), weather=weather, locked=locked,
        ))
        acts = sum(1 for d in itinerary.days for b in d.blocks if b.kind == "activity")
        kept = f", kept {len(locked)} unchanged day(s)" if locked else ""
        return {
            "itinerary": itinerary.model_dump(mode="json"),
            "tool_trace": [_call("itinerary_builder", "Built the itinerary", started,
                                 f"{itinerary.duration_days} days, {acts} activities, {TIER_LABEL[itinerary.stay_tier]} stay, {itinerary.transport_mode}{kept}",
                                 args={"rung": rung, "pace": intent.pace}, result={"total_cost": itinerary.total_cost})],
        }

    def check_budget(state: TripState) -> dict[str, Any]:
        started = time.perf_counter()
        it = Itinerary.model_validate(state["itinerary"])
        intent = _intent(state)
        report = compute_budget(dict(
            transport=it.cost_lines.transport, stay=it.cost_lines.stay, food=it.cost_lines.food,
            activities=it.cost_lines.activities, local_transport=it.cost_lines.local_transport,
            travelers=it.travelers, budget=intent.budget,
        ))
        if report.status == "over_budget":
            summary = f"{rupees(report.total)} total, {rupees(report.overage)} over the {rupees(report.budget)} budget"
        elif report.budget:
            summary = f"{rupees(report.total)} total, {rupees(report.remaining)} under the {rupees(report.budget)} budget"
        else:
            summary = f"{rupees(report.total)} total ({rupees(report.per_person)} per person), no budget stated"
        return {
            "budget_report": report.model_dump(mode="json"),
            "tool_trace": [_call("budget", "Computed the budget", started, summary,
                                 args=report.components.model_dump(),
                                 result={"total": report.total, "status": report.status, "per_person": report.per_person},
                                 status="flagged" if report.status == "over_budget" else "ok")],
        }

    def adjust_plan(state: TripState) -> dict[str, Any]:
        started = time.perf_counter()
        rung = min(state.get("plan_rung", 1) + 1, LAST_RUNG)
        r = LADDER[rung]
        report = BudgetReport.model_validate(state["budget_report"])
        return {
            "plan_rung": rung,
            "revisions": state.get("revisions", 0) + 1,
            "tool_trace": [_call("budget_adjust", "Adjusted to fit the budget", started,
                                 f"Over by {rupees(report.overage)}; trying {TIER_LABEL[r.stay]} stays, {'cheapest' if r.transport == 'cheap' else 'fastest'} transport"
                                 + ("" if r.paid_activities else ", free activities only"),
                                 args={"rung": rung}, status="flagged")],
        }

    def synthesize(state: TripState) -> dict[str, Any]:
        started = time.perf_counter()
        intent = _intent(state)
        itinerary = Itinerary.model_validate(state["itinerary"])
        report = BudgetReport.model_validate(state["budget_report"])
        previous = state.get("previous_itinerary")
        change_summary = diff_itineraries(previous, itinerary) if previous else []
        revised = bool(previous)
        weather_summary = None
        if state.get("weather"):
            weather_summary = WeatherReport.model_validate(state["weather"]).summary
        alternatives = [c["name"].split(" (")[0] for c in ((state.get("candidates") or {}).get("search") or {}).get("candidates", [])[1:]]
        facts = build_facts(intent, itinerary, report, weather_summary, alternatives, change_summary)
        reply, themes, violations = compose_reply(llm, state.get("user_message", ""), facts, itinerary, report, intent, revised)
        trace: list[dict[str, Any]] = []
        if themes:
            for day, theme in zip(itinerary.days, themes):
                day.theme = theme
        if violations:
            trace.append(_call("output_guard", "Checked the reply against tool results", started,
                               "Rejected a draft reply (" + "; ".join(violations) + "). Used a reply built directly from tool results instead.",
                               args={"violations": violations}, status="flagged"))
        version = state.get("version", 0) + 1
        return {
            "reply": reply,
            "itinerary": itinerary.model_dump(mode="json"),
            "version": version,
            "change_summary": change_summary,
            "tool_trace": trace,
        }

    # ---- patch (follow-up) path

    def parse_followup_node(state: TripState) -> dict[str, Any]:
        started = time.perf_counter()
        intent = _intent(state)
        parsed = parse_followup(state["user_message"], intent, state.get("itinerary"), llm, deps.today(), state.get("history"))
        return {
            "delta": parsed.model_dump(mode="json"),
            "tool_trace": [_call("followup_parser", "Interpreted your follow-up", started,
                                 f"{parsed.action}: " + (", ".join(f"{k}={v}" for k, v in parsed.delta.model_dump(mode="json", exclude_defaults=True, exclude_none=True).items()) or "no constraint changes"),
                                 result=parsed.model_dump(mode="json", exclude_defaults=True, exclude_none=True))],
        }

    def answer_question_node(state: TripState) -> dict[str, Any]:
        started = time.perf_counter()
        intent = _intent(state)
        itinerary = Itinerary.model_validate(state["itinerary"])
        report = BudgetReport.model_validate(state["budget_report"])
        weather = WeatherReport.model_validate(state["weather"]).summary if state.get("weather") else None
        facts = build_facts(intent, itinerary, report, weather, [], [])
        question = (state.get("delta") or {}).get("question") or state["user_message"]
        answer, violations = answer_question(llm, question, facts, itinerary, report, intent)
        trace = [_call("answer", "Answered from the current plan", started, "Answered without changing the itinerary")]
        if violations:
            trace.append(_call("output_guard", "Checked the reply against tool results", started,
                               "Rejected a draft answer (" + "; ".join(violations) + "). Used a safe summary instead.",
                               args={"violations": violations}, status="flagged"))
        return {"reply": answer, "change_summary": [], "tool_trace": trace}

    def other_node(state: TripState) -> dict[str, Any]:
        return {"reply": "I can change your current plan (days, budget, travellers, pace, focus, destination) or answer questions about it. What would you like to adjust?",
                "change_summary": []}

    def reset_for_new_trip(state: TripState) -> dict[str, Any]:
        started = time.perf_counter()
        return {
            "itinerary": None, "budget_report": None, "candidates": None, "weather": None, "intent": None,
            "previous_itinerary": None, "plan_rung": 1, "revisions": 0,
            "tool_trace": [_call("new_trip", "Starting a new plan", started, "Treating this as a new trip request; earlier versions are kept in history.")],
        }

    def apply_delta_node(state: TripState) -> dict[str, Any]:
        started = time.perf_counter()
        intent = _intent(state)
        current = Itinerary.model_validate(state["itinerary"])
        delta = FollowUpParse.model_validate(state["delta"]).delta
        rejected: list[str] = []
        if delta.origin and not find_origin(delta.origin):
            rejected.append(f"I don't have fares from {delta.origin}; I can plan from: {_supported_origins()}.")
            delta = delta.model_copy(update={"origin": None})
        if delta.destination:
            hits = match_destinations(delta.destination)
            if not hits:
                rejected.append(f"I don't have data for {delta.destination} yet, so I kept {current.destination_name.split(' (')[0]}.")
            if not hits or current.destination_id in {h.id for h in hits}:
                delta = delta.model_copy(update={"destination": None})
        new_intent, affected = apply_delta(intent, delta)
        trace = [_call("replan", "Updated only what changed", started,
                       "Changed: " + (", ".join(affected) if affected else "nothing"), args={"affected": affected})]
        if not affected:
            msg = " ".join(rejected) or "That already matches the current plan, so nothing needed to change."
            return {"reply": msg, "affected": [], "change_summary": [], "tool_trace": trace}
        rung = state.get("plan_rung", 1)
        if set(affected) & {"budget", "destination", "origin"}:
            rung = initial_rung(new_intent.budget, new_intent.duration_days or 3, new_intent.travelers or 1)
        update: dict[str, Any] = {
            "intent": new_intent.model_dump(mode="json"), "affected": affected, "plan_rung": rung, "revisions": 0,
            "previous_itinerary": state["itinerary"], "tool_trace": trace,
        }
        if rejected:
            update["warnings"] = rejected
        return update

    def refresh_tools(state: TripState) -> dict[str, Any]:
        intent = _intent(state)
        affected = set(state.get("affected", []))
        cands = dict(state.get("candidates") or {})
        trace: list[dict[str, Any]] = []
        warnings: list[str] = []
        update: dict[str, Any] = {}
        if affected & {"destination", "origin"}:
            result, entry = _run_destination_search(intent, deps.today())
            trace.append(entry)
            if not result.chosen_id:
                raise ToolError("I couldn't find a matching destination for that change.")
            cands.update(search=result.model_dump(mode="json"), chosen_id=result.chosen_id)
        if affected & {"destination", "origin", "interests"}:
            places, entry = _run_places(cands["chosen_id"], intent)
            trace.append(entry)
            cands["places"] = places.model_dump(mode="json")
        if affected & {"destination", "duration_days", "start_date"}:
            report, entry, warn = _run_weather(cands["chosen_id"], intent, deps)
            trace.append(entry)
            warnings.extend(warn)
            update["weather"] = report.model_dump(mode="json") if report else {}
        update.update(candidates=cands, tool_trace=trace, warnings=warnings)
        return update

    return {
        "guard_input": _wrap(guard_input, "input_guard", "Input safety check"),
        "parse_intent": _wrap(parse_intent_node, "intent_parser", "Understanding your request"),
        "clarify": _wrap(clarify, "clarify", "Asking for details"),
        "plan": _wrap(plan, "plan", "Planning the steps"),
        "call_tools": _wrap(call_tools, "call_tools", "Running search and weather tools"),
        "build_itinerary": _wrap(build_node, "itinerary_builder", "Building the itinerary"),
        "check_budget": _wrap(check_budget, "budget", "Computing the budget"),
        "adjust_plan": _wrap(adjust_plan, "budget_adjust", "Adjusting to the budget"),
        "synthesize": _wrap(synthesize, "synthesize", "Writing the reply"),
        "parse_followup": _wrap(parse_followup_node, "followup_parser", "Interpreting your follow-up"),
        "answer_question": _wrap(answer_question_node, "answer", "Answering your question"),
        "other": _wrap(other_node, "other", "Replying"),
        "reset_for_new_trip": _wrap(reset_for_new_trip, "new_trip", "Starting a new plan"),
        "apply_delta": _wrap(apply_delta_node, "replan", "Applying the change"),
        "refresh_tools": _wrap(refresh_tools, "refresh_tools", "Refreshing the affected tools"),
    }


def _locked_days(state: TripState, intent: TripIntent) -> dict[int, list[str]]:
    """Which days' activity choices to keep when rebuilding.

    During the budget loop every day from the first pass is kept, so only tiers and transport
    change. On a follow-up's first pass, days survive unless the change affects what is selected.
    """
    in_budget_loop = state.get("revisions", 0) > 0
    source = state.get("itinerary") if in_budget_loop else state.get("previous_itinerary")
    if not source:
        return {}
    old = Itinerary.model_validate(source)
    keep = old.duration_days
    if not in_budget_loop:
        affected = set(state.get("affected", []))
        if affected & {"destination", "origin", "interests", "pace"}:
            return {}
        if "duration_days" in affected and intent.duration_days:
            keep = min(old.duration_days, intent.duration_days)
    return {d.day: [b.place_id for b in d.blocks if b.kind == "activity" and b.place_id] for d in old.days[:keep]}


# --------------------------------------------------------------------------- routers


def should_replan(state: TripState) -> Literal["patch", "parse_intent"]:
    """A stored itinerary means this message is a follow-up: take the lightweight patch path."""
    return "patch" if state.get("itinerary") else "parse_intent"


def route_after_parse(state: TripState) -> Literal["clarify", "plan", "__end__"]:
    if state.get("error"):
        return END
    return "clarify" if state.get("missing_fields") else "plan"


def route_after_tools(state: TripState) -> Literal["clarify", "build_itinerary", "__end__"]:
    if state.get("error"):
        return END
    return "clarify" if state.get("missing_fields") else "build_itinerary"


def make_route_after_budget(settings: Settings) -> Callable[[TripState], str]:
    def route_after_budget(state: TripState) -> str:
        if state.get("error"):
            return END
        report = state.get("budget_report") or {}
        if (
            report.get("status") == "over_budget"
            and state.get("plan_rung", 1) < LAST_RUNG
            and state.get("revisions", 0) < settings.max_budget_revisions
        ):
            return "adjust_plan"
        return "synthesize"

    return route_after_budget


def route_or_end(next_node: str) -> Callable[[TripState], str]:
    def _route(state: TripState) -> str:
        return END if state.get("error") else next_node

    return _route


def route_after_followup(state: TripState) -> str:
    if state.get("error"):
        return END
    action = (state.get("delta") or {}).get("action", "other")
    return {"question": "answer_question", "modify": "apply_delta", "new_trip": "reset_for_new_trip"}.get(action, "other")


def route_after_apply(state: TripState) -> str:
    if state.get("error") or not state.get("affected"):
        return END
    return "refresh_tools"


def route_after_patch(state: TripState) -> str:
    """After the patch subgraph: a new-trip request continues into the full planning path."""
    if state.get("error"):
        return END
    return "parse_intent" if (state.get("delta") or {}).get("action") == "new_trip" and not state.get("itinerary") else END


# --------------------------------------------------------------------------- graph assembly


def build_patch_graph(nodes: dict[str, Callable], settings: Settings):
    g = StateGraph(TripState)
    for name in ("parse_followup", "answer_question", "other", "reset_for_new_trip", "apply_delta", "refresh_tools",
                 "check_budget", "adjust_plan", "synthesize"):
        g.add_node(name, nodes[name])
    g.add_node("rebuild", nodes["build_itinerary"])
    g.add_edge(START, "parse_followup")
    g.add_conditional_edges("parse_followup", route_after_followup,
                            ["answer_question", "apply_delta", "reset_for_new_trip", "other", END])
    g.add_conditional_edges("apply_delta", route_after_apply, ["refresh_tools", END])
    g.add_conditional_edges("refresh_tools", route_or_end("rebuild"), ["rebuild", END])
    g.add_conditional_edges("rebuild", route_or_end("check_budget"), ["check_budget", END])
    g.add_conditional_edges("check_budget", make_route_after_budget(settings), ["adjust_plan", "synthesize", END])
    g.add_edge("adjust_plan", "rebuild")
    g.add_edge("synthesize", END)
    for terminal in ("answer_question", "other", "reset_for_new_trip"):
        g.add_edge(terminal, END)
    return g.compile()


def build_graph(deps: Deps):
    """Compile the full Yatra AI graph."""
    nodes = make_nodes(deps)
    g = StateGraph(TripState)
    for name in ("guard_input", "parse_intent", "clarify", "plan", "call_tools", "build_itinerary", "check_budget",
                 "adjust_plan", "synthesize"):
        g.add_node(name, nodes[name])
    g.add_node("patch", build_patch_graph(nodes, deps.settings))

    g.add_edge(START, "guard_input")
    g.add_conditional_edges("guard_input", should_replan, ["patch", "parse_intent"])
    g.add_conditional_edges("parse_intent", route_after_parse, ["clarify", "plan", END])
    g.add_conditional_edges("plan", route_or_end("call_tools"), ["call_tools", END])
    g.add_conditional_edges("call_tools", route_after_tools, ["clarify", "build_itinerary", END])
    g.add_conditional_edges("build_itinerary", route_or_end("check_budget"), ["check_budget", END])
    g.add_conditional_edges("check_budget", make_route_after_budget(deps.settings), ["adjust_plan", "synthesize", END])
    g.add_edge("adjust_plan", "build_itinerary")
    g.add_edge("clarify", END)
    g.add_edge("synthesize", END)
    g.add_conditional_edges("patch", route_after_patch, ["parse_intent", END])
    return g.compile()


def run_config(settings: Settings) -> dict[str, Any]:
    """LangGraph run config carrying the explicit step cap."""
    return {"recursion_limit": settings.max_graph_steps}
