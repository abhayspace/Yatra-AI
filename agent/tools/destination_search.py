"""Destination and place search over the bundled dataset (data/destinations.json).

Everything here is a deterministic lookup: a user string is only ever compared with dataset
names and aliases, never used to build a path, query or URL.
"""
from __future__ import annotations

import math
from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

from agent.data import find_origin, get_destination, load_dataset, match_destinations
from agent.errors import ToolError
from agent.models import INTERESTS, MAX_TRAVELERS, MAX_TRIP_DAYS, Attraction, Destination, Restaurant

DEFAULT_INTEREST_WEIGHT = 1.0
_GENERIC_CUISINES = {"cafe", "multi cuisine", "continental", "bakery", "italian", "greek", "chinese", "beach shack", "colonial", "fine dining"}


class SearchQuery(BaseModel):
    origin: str | None = None
    destinations: list[str] = Field(default_factory=list)
    region: str | None = None
    interests: list[str] = Field(default_factory=list)
    interest_weights: dict[str, float] = Field(default_factory=dict)
    budget: float | None = Field(default=None, gt=0)
    duration_days: int = Field(default=3, ge=1, le=MAX_TRIP_DAYS)
    travelers: int = Field(default=1, ge=1, le=MAX_TRAVELERS)
    start_date: date | None = None
    top_k: int = Field(default=3, ge=1, le=6)


class Candidate(BaseModel):
    destination_id: str
    name: str
    score: float
    reasons: list[str]
    min_cost_estimate: float | None = None
    feasible: bool | None = None
    season: Literal["good", "neutral", "avoid"] = "neutral"


class SearchResult(BaseModel):
    matched_by: Literal["named", "region", "interests"]
    candidates: list[Candidate]
    chosen_id: str | None = None
    unknown_names: list[str] = Field(default_factory=list)
    origin_supported: bool = True


class ScoredAttraction(BaseModel):
    attraction: Attraction
    score: float


class ScoredRestaurant(BaseModel):
    restaurant: Restaurant
    score: float


class PlaceMatches(BaseModel):
    destination_id: str
    attractions: list[ScoredAttraction]
    restaurants: list[ScoredRestaurant]


def effective_weights(interests: list[str], weights: dict[str, float]) -> dict[str, float]:
    """Weight per interest: stated interests default to 1.0, explicit weights override, extras allowed."""
    out = {i: DEFAULT_INTEREST_WEIGHT for i in interests if i in INTERESTS}
    for key, w in weights.items():
        if key in INTERESTS:
            out[key] = float(w)
    return {k: v for k, v in out.items() if v > 0}


def estimate_min_cost(dest: Destination, origin_name: str, days: int, travelers: int) -> float | None:
    options = dest.transport_from.get(origin_name)
    if not options:
        return None
    cheapest = min(o.one_way_per_person for o in options)
    nights = max(days - 1, 0)
    rooms = math.ceil(travelers / 2)
    transport = 2 * cheapest * travelers
    stay = nights * rooms * dest.stay["budget"]
    food = days * travelers * (dest.breakfast_pp["budget"] + 2 * dest.generic_meal_pp["budget"])
    local = days * dest.local_transport_per_day * math.ceil(travelers / 4)
    return float(transport + stay + food + local)


def _season(dest: Destination, month: int | None) -> Literal["good", "neutral", "avoid"]:
    if month is None:
        return "neutral"
    if month in dest.avoid_months:
        return "avoid"
    return "good" if month in dest.best_months else "neutral"


def _interest_score(dest: Destination, weights: dict[str, float]) -> float:
    if not weights:
        return 0.5
    total_w = sum(weights.values())
    acc = 0.0
    for interest, w in weights.items():
        count = sum(1 for a in dest.attractions if interest in a.themes)
        acc += w * min(1.0, count / 4)
    return acc / total_w


def _score_destination(dest: Destination, q: SearchQuery, origin_name: str | None, weights: dict[str, float]) -> Candidate:
    score = 60 * _interest_score(dest, weights)
    reasons: list[str] = []
    stated = [i for i in weights if any(i in a.themes for a in dest.attractions)]
    if stated:
        reasons.append("Strong on " + ", ".join(stated[:3]))

    season = _season(dest, q.start_date.month if q.start_date else None)
    if season == "good":
        score += 15
        reasons.append("Good season for the travel dates")
    elif season == "avoid":
        score -= 25
        reasons.append(f"Off-season ({dest.avoid_reason})")

    estimate = feasible = None
    if origin_name:
        estimate = estimate_min_cost(dest, origin_name, q.duration_days, q.travelers)
        if estimate is not None and q.budget:
            ratio = estimate / q.budget
            feasible = ratio <= 1.0
            if ratio <= 0.6:
                score += 15
                reasons.append("Comfortably fits the budget")
            elif ratio <= 0.9:
                score += 8
                reasons.append("Fits the budget")
            elif ratio <= 1.0:
                reasons.append("Only just fits the budget at the cheapest level")
            else:
                score -= min(120.0, 40 + 40 * (ratio - 1))
                reasons.append("Even the cheapest version exceeds the budget")
        options = dest.transport_from.get(origin_name)
        if options:
            fastest = min(o.hours for o in options)
            score -= max(0.0, 2 * fastest - 0.3 * q.duration_days * 24)
            if 2 * fastest > 0.3 * q.duration_days * 24:
                reasons.append(f"Long journey (about {fastest:.0f}h each way) for {q.duration_days} days")
    return Candidate(
        destination_id=dest.id, name=dest.name, score=round(score, 2), reasons=reasons,
        min_cost_estimate=estimate, feasible=feasible, season=season,
    )


def search_destinations(query: SearchQuery | dict) -> SearchResult:
    """Pick and rank destinations for a query. Named places win; otherwise rank by interests."""
    try:
        q = query if isinstance(query, SearchQuery) else SearchQuery.model_validate(query)
    except Exception as exc:  # pydantic ValidationError
        raise ToolError("Invalid destination search input.") from exc

    origin = find_origin(q.origin)
    origin_name = origin.name if origin else None
    weights = effective_weights(q.interests, q.interest_weights)

    pool: dict[str, Destination] = {}
    unknown: list[str] = []
    named_terms = [*q.destinations, *([q.region] if q.region else [])]
    matched_by: Literal["named", "region", "interests"] = "interests"
    for term in named_terms:
        hits = match_destinations(term)
        if not hits:
            unknown.append(term)
        for d in hits:
            pool[d.id] = d
    if pool:
        matched_by = "named" if q.destinations else "region"
    elif not unknown:
        pool = {d.id: d for d in load_dataset().destinations}
    else:
        # user named places we do not have; still offer ranked alternatives, flagged as such
        pool = {d.id: d for d in load_dataset().destinations}

    if origin_name:
        pool = {k: d for k, d in pool.items() if d.name.split(" (")[0].lower() != origin_name.lower()}

    ranked = sorted(
        (_score_destination(d, q, origin_name, weights) for d in pool.values()),
        key=lambda c: (-c.score, c.destination_id),
    )[: q.top_k]
    chosen = ranked[0].destination_id if ranked else None
    if unknown and matched_by == "interests":
        chosen = None  # nothing the user asked for exists in the dataset; let the graph ask
    return SearchResult(
        matched_by=matched_by, candidates=ranked, chosen_id=chosen, unknown_names=unknown,
        origin_supported=origin is not None,
    )


def score_attraction(a: Attraction, weights: dict[str, float]) -> float:
    if not weights:
        return 0.5
    score = 0.0
    for interest, w in weights.items():
        if interest in a.themes:
            score += w
        if a.type == interest:
            score += 0.3 * w
    if a.cost_per_person == 0:
        score += 0.05
    return round(score, 3)


def score_restaurant(r: Restaurant, weights: dict[str, float]) -> float:
    food_w = weights.get("food", 0.0)
    local = r.cuisine.lower().replace("-", " ") not in _GENERIC_CUISINES
    return round(1.0 + (0.6 * food_w if local else 0.0), 3)


def search_places(dest_id: str, interests: list[str], weights: dict[str, float] | None = None) -> PlaceMatches:
    """All attractions and restaurants for a destination, ranked by fit with the stated interests."""
    dest = get_destination(dest_id) if isinstance(dest_id, str) else None
    if dest is None:
        raise ToolError("Unknown destination.")
    w = effective_weights(interests, weights or {})
    order = {a.id: i for i, a in enumerate(dest.attractions)}
    atts = sorted(
        (ScoredAttraction(attraction=a, score=score_attraction(a, w)) for a in dest.attractions),
        key=lambda s: (-s.score, order[s.attraction.id]),
    )
    rorder = {r.id: i for i, r in enumerate(dest.restaurants)}
    rests = sorted(
        (ScoredRestaurant(restaurant=r, score=score_restaurant(r, w)) for r in dest.restaurants),
        key=lambda s: (-s.score, rorder[s.restaurant.id]),
    )
    return PlaceMatches(destination_id=dest.id, attractions=atts, restaurants=rests)
