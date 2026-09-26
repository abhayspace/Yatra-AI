"""Compare alternatives: cost the runner-up destinations with the same constraints.

Deterministic. It reuses the search ranking and the itinerary builder, so every figure comes from the
dataset, and lets the reply say what a different choice would have cost.
"""
from __future__ import annotations

from datetime import date

from pydantic import BaseModel

from agent.errors import ToolError
from agent.models import TripIntent
from agent.tools.destination_search import SearchResult, search_places
from agent.tools.itinerary_builder import BuildRequest, build_itinerary


class CostedAlternative(BaseModel):
    destination_id: str
    name: str
    total_cost: float
    transport_mode: str
    stay_tier: str
    within_budget: bool | None
    difference_vs_chosen: float  # positive = costs more than the chosen plan


def compare_alternatives(intent: TripIntent, search: SearchResult, chosen_total: float, rung: int, limit: int = 2) -> list[CostedAlternative]:
    """Cost up to `limit` runner-up destinations at the same comfort level as the chosen plan."""
    if not (intent.origin and intent.duration_days and intent.travelers and intent.pace):
        raise ToolError("Alternatives need origin, duration, travellers and pace.")
    out: list[CostedAlternative] = []
    for cand in search.candidates:
        if cand.destination_id == search.chosen_id:
            continue
        places = search_places(cand.destination_id, intent.interests, intent.interest_weights)
        it = build_itinerary(BuildRequest(
            destination_id=cand.destination_id, origin=intent.origin, start_date=intent.start_date if isinstance(intent.start_date, date) else None,
            duration_days=intent.duration_days, travelers=intent.travelers, pace=intent.pace, interests=intent.interests,
            rung=rung, places=places,
        ))
        out.append(CostedAlternative(
            destination_id=cand.destination_id, name=cand.name, total_cost=it.total_cost, transport_mode=it.transport_mode,
            stay_tier=it.stay_tier, within_budget=(it.total_cost <= intent.budget) if intent.budget else None,
            difference_vs_chosen=it.total_cost - chosen_total,
        ))
        if len(out) >= limit:
            break
    return out
