"""Model-chosen tool plan, validated against an allowlist.

destination_search and place_search always run. The model decides whether the optional tools add value for
this request. Whatever it returns is filtered to known tool names and put in a fixed order, so it cannot
introduce an unlisted tool or reorder the pipeline; if the model call fails, a default plan is used and the
trace says so.
"""
from __future__ import annotations

import json

from pydantic import BaseModel, Field

from agent.errors import LLMError
from agent.llm_client import LLMClient
from agent.models import TripIntent
from agent.prompts import PLAN_SYSTEM

CORE_TOOLS = ("destination_search", "place_search")
OPTIONAL_TOOLS = ("weather", "compare_alternatives")
ALLOWED_TOOLS = (*CORE_TOOLS, *OPTIONAL_TOOLS)


class ToolPlanDecision(BaseModel):
    tools: list[str] = Field(default_factory=list, max_length=8)
    rationale: str = Field(default="", max_length=300)


class ToolPlan(BaseModel):
    tools: list[str]
    rationale: str
    source: str  # "model" or "default"


def default_plan(intent: TripIntent) -> list[str]:
    tools = [*CORE_TOOLS, "weather"]
    if not intent.destinations:
        tools.append("compare_alternatives")
    return tools


def decide_plan(llm: LLMClient, intent: TripIntent) -> ToolPlan:
    facts = intent.model_dump(mode="json", include={"origin", "destinations", "region", "duration_days", "travelers", "budget", "interests", "pace", "start_date"})
    user = f"<trip_facts>\n{json.dumps(facts, ensure_ascii=False)}\n</trip_facts>"
    try:
        decision = llm.complete_structured("plan_tools", PLAN_SYSTEM, user, ToolPlanDecision)
    except LLMError as exc:
        return ToolPlan(tools=default_plan(intent), rationale=f"Model plan unavailable ({exc}); used the default plan.", source="default")
    chosen = {t for t in decision.tools if t in OPTIONAL_TOOLS}
    ordered = [*CORE_TOOLS, *[t for t in OPTIONAL_TOOLS if t in chosen]]
    return ToolPlan(tools=ordered, rationale=decision.rationale.strip() or "No rationale given.", source="model")
