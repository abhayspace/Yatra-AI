"""End-to-end trajectory evals: a natural-language prompt goes into the compiled LangGraph
(with a scripted language model and a mocked Open-Meteo transport), and the assertions are on
the tool-call sequence and the properties of the final itinerary, per required capability."""
import pytest

from evals.harness import load_cases, run_case

CASES = load_cases()


@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_trajectory_case(case, make_graph, settings):
    rainy = set(case.get("offline_weather", {}).get("rainy_day_offsets", []))
    graph = make_graph(rainy_offsets=rainy or None)
    result = run_case(case, graph, settings)
    assert result.passed, "\n".join(result.failures)


def test_dataset_covers_every_required_capability_and_edge_case():
    ids = {c["id"] for c in CASES}
    caps = {cap for c in CASES for cap in c["capabilities"]}
    assert {"intent", "destination_search", "weather", "budget", "itinerary", "replan", "safety"} <= caps
    assert {"happy_path", "tight_budget_achievable", "tight_budget_impossible", "prompt_injection"} <= ids
    assert any(c["id"].startswith("replan_") for c in CASES)


def test_itinerary_cites_dataset_and_live_weather(make_graph, settings):
    from agent.runner import run_turn

    state = run_turn(make_graph(), settings, "3 days in Goa from Mumbai for 2 people, food, budget 30000")
    kinds = [s["kind"] for s in state["itinerary"]["sources"]]
    assert kinds == ["dataset", "weather"]


KNOWN_TOOLS = {
    "input_guard", "output_guard", "intent_parser", "followup_parser", "plan", "destination_search", "place_search", "weather",
    "itinerary_builder", "budget", "budget_adjust", "replan", "answer", "clarify", "new_trip",
}


@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_trace_entries_and_outputs_follow_their_schemas(case, make_graph, settings):
    """Every tool call is on the allowlist and validates as a ToolCall; itinerary and budget validate as models."""
    from agent.models import BudgetReport, Itinerary, ToolCall

    rainy = set(case.get("offline_weather", {}).get("rainy_day_offsets", []))
    result = run_case(case, make_graph(rainy_offsets=rainy or None), settings)
    for turn in result.turns:
        for entry in turn.state["tool_trace"]:
            ToolCall.model_validate(entry)
            assert entry["name"] in KNOWN_TOOLS, entry["name"]
        if turn.state.get("itinerary"):
            it = Itinerary.model_validate(turn.state["itinerary"])
            assert round(it.total_cost) == round(BudgetReport.model_validate(turn.state["budget_report"]).total)
