import pytest

from agent.errors import LLMError
from agent.llm_client import LLMClient
from agent.models import TripIntent
from agent.planner import ALLOWED_TOOLS, ToolPlanDecision, decide_plan
from agent.tools.alternatives import compare_alternatives
from agent.tools.destination_search import SearchQuery, search_destinations
from tests.fakes import ScriptedLLM


class Fixed(LLMClient):
    def __init__(self, tools=None, error=None):
        self.tools, self.error = tools or [], error

    def complete_structured(self, task, system, user, schema):
        if self.error:
            raise self.error
        return ToolPlanDecision(tools=self.tools, rationale="fixed")


INTENT = TripIntent(origin="Delhi", duration_days=4, travelers=2, budget=50000, interests=["nature"], pace="balanced")


def test_core_tools_always_run_and_order_is_fixed():
    plan = decide_plan(Fixed(["compare_alternatives", "weather"]), INTENT)
    assert plan.tools == ["destination_search", "place_search", "weather", "compare_alternatives"] and plan.source == "model"
    assert decide_plan(Fixed([]), INTENT).tools == ["destination_search", "place_search"]


@pytest.mark.parametrize("hostile", [["rm -rf /", "itinerary_builder", "destination_search"], ["book_flight", "send_email"], ["weather", "weather"], ["../../x"]])
def test_model_cannot_add_unlisted_tools_or_reorder(hostile):
    plan = decide_plan(Fixed(hostile), INTENT)
    assert set(plan.tools) <= set(ALLOWED_TOOLS) and plan.tools[:2] == ["destination_search", "place_search"]
    assert len(plan.tools) == len(set(plan.tools))


def test_model_failure_falls_back_to_a_flagged_default_plan():
    plan = decide_plan(Fixed(error=LLMError("down")), INTENT)
    assert plan.source == "default" and "weather" in plan.tools and "compare_alternatives" in plan.tools
    named = decide_plan(Fixed(error=LLMError("down")), INTENT.model_copy(update={"destinations": ["Goa"]}))
    assert "compare_alternatives" not in named.tools


def test_scripted_model_compares_only_when_recommending():
    llm = ScriptedLLM()
    assert "compare_alternatives" in decide_plan(llm, INTENT).tools
    assert "compare_alternatives" not in decide_plan(llm, INTENT.model_copy(update={"destinations": ["Goa"]})).tools


def test_alternatives_are_costed_from_the_dataset_at_the_same_comfort_level():
    q = SearchQuery(origin="Delhi", interests=["nature", "food"], budget=50000, duration_days=4, travelers=2)
    search = search_destinations(q)
    alts = compare_alternatives(INTENT, search, chosen_total=30000, rung=1)
    assert 1 <= len(alts) <= 2 and all(a.destination_id != search.chosen_id for a in alts)
    for a in alts:
        assert a.total_cost > 0 and a.difference_vs_chosen == a.total_cost - 30000
        assert a.within_budget == (a.total_cost <= 50000)
