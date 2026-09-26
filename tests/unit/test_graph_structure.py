"""Deterministic checks on the state machine itself: nodes, conditional edges and router decisions."""
import httpx
import pytest
from langgraph.graph import END

import agent.graph as g
from agent.graph import Deps, build_graph, make_route_after_budget, route_after_apply, route_after_followup, route_after_parse, route_after_patch, route_after_tools, should_replan
from agent.settings import Settings
from agent.tools.itinerary_builder import LAST_RUNG
from tests.fakes import TODAY, ScriptedLLM, weather_transport


@pytest.fixture(scope="module")
def compiled():
    deps = Deps(llm=ScriptedLLM(), settings=Settings(_env_file=None), http_client=httpx.Client(transport=weather_transport()), today=lambda: TODAY)
    return build_graph(deps)


def test_main_graph_has_the_planning_nodes_and_a_patch_subgraph(compiled):
    names = set(compiled.get_graph().nodes)
    for node in ("guard_input", "parse_intent", "clarify", "plan", "call_tools", "build_itinerary", "check_budget", "adjust_plan", "synthesize", "patch"):
        assert node in names, node
    inner = {n for n in compiled.get_graph(xray=True).nodes if n.startswith("patch:")}
    assert {"patch:parse_followup", "patch:apply_delta", "patch:refresh_tools", "patch:rebuild", "patch:check_budget", "patch:adjust_plan", "patch:synthesize", "patch:answer_question"} <= inner


def test_should_replan_is_a_real_conditional_branch(compiled):
    edges = [(e.source, e.target, e.conditional) for e in compiled.get_graph().edges]
    assert ("guard_input", "patch", True) in edges and ("guard_input", "parse_intent", True) in edges
    assert ("adjust_plan", "build_itinerary", False) in edges  # the recovery loop
    assert ("check_budget", "adjust_plan", True) in edges and ("check_budget", "compare_alts", True) in edges
    assert ("compare_alts", "synthesize", False) in edges


def test_should_replan_routes_on_existing_itinerary():
    assert should_replan({}) == "parse_intent"
    assert should_replan({"itinerary": None}) == "parse_intent"
    assert should_replan({"itinerary": {"days": []}}) == "patch"


def test_budget_router_loops_only_while_over_budget_and_within_caps():
    route = make_route_after_budget(Settings(_env_file=None, max_budget_revisions=2))
    over = {"budget_report": {"status": "over_budget"}, "plan_rung": 1, "revisions": 0}
    assert route(over) == "adjust_plan"
    assert route({**over, "revisions": 2}) == "synthesize"          # revision cap reached
    assert route({**over, "plan_rung": LAST_RUNG}) == "synthesize"  # nothing cheaper left
    assert route({**over, "budget_report": {"status": "within_budget"}}) == "synthesize"
    assert route({**over, "error": "boom"}) == END


def test_parse_and_tool_routers():
    assert route_after_parse({"missing_fields": ["origin"]}) == "clarify"
    assert route_after_parse({"missing_fields": []}) == "plan"
    assert route_after_parse({"error": "x"}) == END
    assert route_after_tools({"missing_fields": ["known_destination"]}) == "clarify"
    assert route_after_tools({"missing_fields": []}) == "build_itinerary"


@pytest.mark.parametrize(
    "action,expected",
    [("question", "answer_question"), ("modify", "apply_delta"), ("new_trip", "reset_for_new_trip"), ("other", "other"), ("weird", "other")],
)
def test_followup_router(action, expected):
    assert route_after_followup({"delta": {"action": action}}) == expected
    assert route_after_followup({"delta": {"action": action}, "error": "x"}) == END


def test_patch_exits_and_reentry():
    assert route_after_apply({"affected": []}) == END
    assert route_after_apply({"affected": ["budget"]}) == "refresh_tools"
    assert route_after_patch({"delta": {"action": "new_trip"}, "itinerary": None}) == "parse_intent"
    assert route_after_patch({"delta": {"action": "modify"}, "itinerary": {"x": 1}}) == END


def test_step_cap_and_recursion_limit_are_explicit():
    assert g.run_config(Settings(_env_file=None, max_graph_steps=17)) == {"recursion_limit": 17}
