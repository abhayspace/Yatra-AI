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
