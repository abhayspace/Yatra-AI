"""Budget calculator: pure arithmetic over explicitly typed numeric fields.

No user-supplied string is ever evaluated. Amounts arrive as numbers, or as strings that
must match a strict numeric pattern and are then converted with float().
"""
from __future__ import annotations

import math
import re
from typing import Any

from pydantic import BaseModel, Field, ValidationError, field_validator

from agent.errors import ToolError
from agent.models import BudgetReport, CostLines, MAX_TRAVELERS

MAX_AMOUNT = 100_000_000.0
TIGHT_THRESHOLD = 0.95  # spending more than 95% of the budget is flagged as tight

_AMOUNT_RE = re.compile(r"^(?P<num>[0-9]+(?:\.[0-9]+)?)\s*(?P<unit>k|l|lakh|lac|lakhs)?$")
_UNIT = {None: 1.0, "k": 1_000.0, "l": 100_000.0, "lakh": 100_000.0, "lac": 100_000.0, "lakhs": 100_000.0}


def parse_amount(raw: Any) -> float:
    """Validate and convert a rupee amount. Accepts numbers or strings like '₹50,000', '50k', '1.5 lakh'."""
    if isinstance(raw, bool):
        raise ToolError("Amount must be a number.")
    if isinstance(raw, (int, float)):
        value = float(raw)
    elif isinstance(raw, str):
        cleaned = raw.strip().lower()
        cleaned = re.sub(r"^(?:₹|rs\.?|inr)\s*", "", cleaned)
        cleaned = cleaned.replace(",", "").replace("/-", "").strip()
        match = _AMOUNT_RE.match(cleaned)
        if not match:
            raise ToolError("Amount is not a plain number.")
        value = float(match.group("num")) * _UNIT[match.group("unit")]
    else:
        raise ToolError("Amount must be a number.")
    if not math.isfinite(value) or value < 0 or value > MAX_AMOUNT:
        raise ToolError("Amount is out of the supported range.")
    return value


class BudgetInput(BaseModel):
    transport: float = Field(ge=0, le=MAX_AMOUNT)
    stay: float = Field(ge=0, le=MAX_AMOUNT)
    food: float = Field(ge=0, le=MAX_AMOUNT)
    activities: float = Field(ge=0, le=MAX_AMOUNT)
    local_transport: float = Field(default=0.0, ge=0, le=MAX_AMOUNT)
    travelers: int = Field(default=1, ge=1, le=MAX_TRAVELERS)
    budget: float | None = Field(default=None, gt=0, le=MAX_AMOUNT)

    @field_validator("transport", "stay", "food", "activities", "local_transport", "budget", mode="before")
    @classmethod
    def _validated_amount(cls, v: Any) -> Any:
        if v is None:
            return v
        try:
            return parse_amount(v)
        except ToolError as exc:
            raise ValueError(str(exc)) from exc

    @field_validator("travelers", mode="before")
    @classmethod
    def _validated_count(cls, v: Any) -> Any:
        if isinstance(v, bool):
            raise ValueError("Travelers must be a whole number.")
        if isinstance(v, str):
            if not re.fullmatch(r"[0-9]{1,3}", v.strip()):
                raise ValueError("Travelers must be a whole number.")
            return int(v.strip())
        if isinstance(v, float):
            if not v.is_integer():
                raise ValueError("Travelers must be a whole number.")
            return int(v)
        return v


_SUGGESTIONS = {
    "transport": "Transport is the largest cost; a train or bus instead of a flight would cut it.",
    "stay": "Stay is the largest cost; a budget-tier hotel or fewer nights would cut it.",
    "food": "Food is the largest cost; choosing casual local eateries would cut it.",
    "activities": "Paid activities are the largest cost; swapping a few for free sights would cut it.",
    "local_transport": "Local transport is the largest cost; shorter days or fewer cab trips would cut it.",
}


def compute_budget(data: BudgetInput | dict) -> BudgetReport:
    """Sum the cost lines and compare with the ceiling. Raises ToolError on invalid input."""
    try:
        inp = data if isinstance(data, BudgetInput) else BudgetInput.model_validate(data)
    except ValidationError as exc:
        fields = ", ".join(sorted({str(e["loc"][0]) for e in exc.errors() if e["loc"]}))
        raise ToolError(f"Invalid budget input ({fields}).") from exc

    lines = CostLines(
        transport=round(inp.transport),
        stay=round(inp.stay),
        food=round(inp.food),
        activities=round(inp.activities),
        local_transport=round(inp.local_transport),
    )
    parts = lines.model_dump()
    total = float(sum(parts.values()))
    pct = {k: round(100 * v / total, 1) if total else 0.0 for k, v in parts.items()}

    remaining = overage = None
    status = "no_budget_given"
    suggestions: list[str] = []
    if inp.budget is not None:
        remaining = inp.budget - total
        if total > inp.budget:
            status, overage = "over_budget", total - inp.budget
        elif total > TIGHT_THRESHOLD * inp.budget:
            status = "tight"
        else:
            status = "within_budget"
        if status == "over_budget" and total:
            biggest = max(parts, key=lambda k: parts[k])
            suggestions.append(_SUGGESTIONS[biggest])

    return BudgetReport(
        components=lines,
        total=total,
        per_person=round(total / inp.travelers),
        budget=inp.budget,
        remaining=remaining,
        status=status,
        overage=overage or 0.0,
        breakdown_pct=pct,
        suggestions=suggestions,
    )
