"""Pydantic models: grounding dataset records, trip intent, itinerary and budget."""
from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, field_validator

INTERESTS: tuple[str, ...] = (
    "nature", "food", "culture", "adventure", "beach", "relaxation",
    "heritage", "spiritual", "nightlife", "shopping", "wellness", "wildlife",
)
Pace = Literal["relaxed", "balanced", "packed"]
Tier = Literal["budget", "mid", "premium"]
TimeOfDay = Literal["morning", "afternoon", "evening"]
BlockKind = Literal["transit", "stay", "activity", "meal", "leisure"]

MAX_TRIP_DAYS = 14
MAX_TRAVELERS = 20


# --------------------------------------------------------------------------- dataset


class TransportOption(BaseModel):
    mode: str
    one_way_per_person: int = Field(ge=0)
    hours: float = Field(ge=0)


class Access(BaseModel):
    rail: bool
    air: bool
    bus: bool
    last_mile_pp: int = Field(ge=0)
    air_surcharge: int = Field(ge=0)


class Attraction(BaseModel):
    id: str
    name: str
    type: str
    themes: list[str]
    duration_hours: float = Field(gt=0)
    cost_per_person: float = Field(ge=0)
    indoor: bool
    best_time: Literal["morning", "afternoon", "evening", "any"]
    area: str
    note: str


class Restaurant(BaseModel):
    id: str
    name: str
    cuisine: str
    meals: list[Literal["breakfast", "lunch", "dinner"]]
    tier: Tier
    cost_per_person: float = Field(ge=0)
    signature: str
    area: str


class Destination(BaseModel):
    id: str
    name: str
    state: str
    region: str
    aliases: list[str]
    lat: float
    lon: float
    tagline: str
    best_months: list[int]
    avoid_months: list[int]
    avoid_reason: str
    access: Access
    stay: dict[Tier, int]
    breakfast_pp: dict[Tier, int]
    generic_meal_pp: dict[Tier, int]
    local_transport_per_day: int
    themes: list[str]
    attractions: list[Attraction]
    restaurants: list[Restaurant]
    transport_from: dict[str, list[TransportOption]]


class Origin(BaseModel):
    name: str
    lat: float
    lon: float
    aliases: list[str]


class Dataset(BaseModel):
    meta: dict
    origins: dict[str, Origin]
    destinations: list[Destination]


# --------------------------------------------------------------------------- intent


class TripIntent(BaseModel):
    """Everything the agent knows about what the traveller wants."""

    origin: str | None = None
    destinations: list[str] = Field(default_factory=list)
    region: str | None = None
    duration_days: int | None = Field(default=None, ge=1, le=MAX_TRIP_DAYS)
    travelers: int | None = Field(default=None, ge=1, le=MAX_TRAVELERS)
    budget: float | None = Field(default=None, gt=0, le=100_000_000)
    interests: list[str] = Field(default_factory=list)
    interest_weights: dict[str, float] = Field(default_factory=dict)
    pace: Pace | None = None
    start_date: date | None = None
    notes: str = Field(default="", max_length=300)
    assumptions: list[str] = Field(default_factory=list)

    @field_validator("interests")
    @classmethod
    def _known_interests(cls, v: list[str]) -> list[str]:
        out: list[str] = []
        for item in v:
            key = str(item).strip().lower()
            if key in INTERESTS and key not in out:
                out.append(key)
        return out

    @field_validator("interest_weights")
    @classmethod
    def _clean_weights(cls, v: dict[str, float]) -> dict[str, float]:
        return {k.lower(): min(3.0, max(0.0, float(w))) for k, w in v.items() if k.lower() in INTERESTS}

    @field_validator("origin", "region")
    @classmethod
    def _short_text(cls, v: str | None) -> str | None:
        return v.strip()[:80] if v and v.strip() else None

    @field_validator("destinations")
    @classmethod
    def _short_dests(cls, v: list[str]) -> list[str]:
        return [d.strip()[:80] for d in v if d and d.strip()][:5]

    @field_validator("notes")
    @classmethod
    def _strip_notes(cls, v: str) -> str:
        return v.strip()


class IntentDelta(BaseModel):
    """Only the constraints a follow-up message changes."""

    origin: str | None = None
    destination: str | None = None
    duration_days: int | None = Field(default=None, ge=1, le=MAX_TRIP_DAYS)
    travelers: int | None = Field(default=None, ge=1, le=MAX_TRAVELERS)
    budget: float | None = Field(default=None, gt=0, le=100_000_000)
    pace: Pace | None = None
    start_date: date | None = None
    add_interests: list[str] = Field(default_factory=list)
    remove_interests: list[str] = Field(default_factory=list)
    interest_weights: dict[str, float] = Field(default_factory=dict)

    @field_validator("add_interests", "remove_interests")
    @classmethod
    def _known(cls, v: list[str]) -> list[str]:
        return [i for i in dict.fromkeys(x.strip().lower() for x in v) if i in INTERESTS]

    @field_validator("interest_weights")
    @classmethod
    def _clean_weights(cls, v: dict[str, float]) -> dict[str, float]:
        return {k.lower(): min(3.0, max(0.0, float(w))) for k, w in v.items() if k.lower() in INTERESTS}

    def is_empty(self) -> bool:
        return not self.model_dump(exclude_defaults=True, exclude_none=True)


class FollowUpParse(BaseModel):
    action: Literal["modify", "new_trip", "question", "other"]
    delta: IntentDelta = Field(default_factory=IntentDelta)
    question: str | None = Field(default=None, max_length=400)


# --------------------------------------------------------------------------- itinerary


class Block(BaseModel):
    id: str
    time_of_day: TimeOfDay
    start: str
    end: str
    kind: BlockKind
    category: str  # icon key: nature, food, culture, train, flight, stay, ...
    title: str
    description: str = ""
    place_id: str | None = None
    area: str | None = None
    cost_per_person: float = 0.0
    cost_total: float = 0.0
    indoor: bool = False
    weather_note: str | None = None


class DayWeather(BaseModel):
    date: str
    temp_max_c: float | None = None
    temp_min_c: float | None = None
    precip_probability: float | None = None
    precip_mm: float | None = None
    summary: str = ""
    rainy: bool = False
    hot: bool = False
    source: Literal["forecast", "last-year-archive"] = "forecast"


class Day(BaseModel):
    day: int
    date: str | None = None
    theme: str
    blocks: list[Block]
    weather: DayWeather | None = None
    day_cost: float = 0.0


class CostLines(BaseModel):
    transport: float = 0.0
    stay: float = 0.0
    food: float = 0.0
    activities: float = 0.0
    local_transport: float = 0.0


class Itinerary(BaseModel):
    destination_id: str
    destination_name: str
    origin: str
    start_date: str | None = None
    duration_days: int
    travelers: int
    pace: Pace
    stay_tier: Tier
    transport_mode: str
    rooms: int
    nights: int
    days: list[Day]
    cost_lines: CostLines
    total_cost: float
    notes: list[str] = Field(default_factory=list)


# --------------------------------------------------------------------------- budget


class BudgetReport(BaseModel):
    components: CostLines
    total: float
    per_person: float
    budget: float | None
    remaining: float | None
    status: Literal["within_budget", "tight", "over_budget", "no_budget_given"]
    overage: float = 0.0
    breakdown_pct: dict[str, float]
    suggestions: list[str] = Field(default_factory=list)


# --------------------------------------------------------------------------- trace


class ToolCall(BaseModel):
    name: str
    label: str
    status: Literal["ok", "error", "flagged"] = "ok"
    args: dict = Field(default_factory=dict)
    summary: str = ""
    result: dict = Field(default_factory=dict)
    duration_ms: int = 0
