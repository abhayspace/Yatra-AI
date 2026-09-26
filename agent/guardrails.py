"""Input sanitising, prompt-injection flags and output validation.

Two layers protect the plan from untrusted text:
1. User text is stripped of our delimiter tags, length-capped and wrapped in <user_request>
   before it is placed in a prompt, and the system prompt tells the model it is data.
2. Whatever the model writes back is checked against the facts the tools produced. A reply
   that quotes a price no tool computed, calls the trip free, or claims a booking is rejected.
"""
from __future__ import annotations

import re
import unicodedata

from agent.models import BudgetReport, Itinerary

OPEN_TAG = "<user_request>"
CLOSE_TAG = "</user_request>"

_TAG_RE = re.compile(r"<\s*/?\s*(?:user_request|trip_facts|system|assistant|instructions?)\b[^>]*>", re.IGNORECASE)
_CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")

_INJECTION_PATTERNS: dict[str, re.Pattern[str]] = {
    "override_instructions": re.compile(r"\b(ignore|disregard|forget|override|bypass)\b[^.\n]{0,40}\b(instructions?|rules?|prompts?|guidelines?|constraints?|limits?)\b", re.I),
    "reveal_prompt": re.compile(r"\b(reveal|show|print|repeat|leak)\b[^.\n]{0,30}\b(system prompt|instructions|hidden|secret|api key)", re.I),
    "role_hijack": re.compile(r"\b(you are now|act as|pretend (to be|you are)|developer mode|jailbreak|dan mode)\b", re.I),
    "free_claim": re.compile(r"\b(say|state|claim|tell me|respond|reply)\b[^.\n]{0,40}\b(free|no cost|costs? nothing|zero cost)\b", re.I),
    "delimiter_break": re.compile(r"</?\s*(user_request|trip_facts|system)\s*>", re.I),
}

_AMOUNT_RE = re.compile(
    r"(?:₹|\brs\.?|\binr)\s*(?P<a>[0-9][0-9,]*(?:\.[0-9]+)?)\s*(?P<au>k|l|lakh|lakhs|lac)?\b"
    r"|(?P<b>[0-9][0-9,]*(?:\.[0-9]+)?)\s*(?P<bu>k|l|lakh|lakhs|lac)?\s*(?:rupees|inr)\b",
    re.IGNORECASE,
)
_UNIT = {None: 1.0, "k": 1e3, "l": 1e5, "lakh": 1e5, "lakhs": 1e5, "lac": 1e5}

_FREE_CLAIMS = [
    re.compile(r"\b(trip|plan|itinerary|holiday|vacation|it)\b[^.\n]{0,30}\b(is|are|will be|would be|comes?)\s+(?:completely |totally |entirely )?(free|costless|free of charge)\b", re.I),
    re.compile(r"\b(costs?|will cost|would cost)\s+(you\s+)?(nothing|zero|no money)\b", re.I),
    re.compile(r"\b(at no cost|no cost at all|zero cost|free of charge|entirely free|completely free|totally free)\b", re.I),
]
_BOOKING_CLAIMS = [
    re.compile(r"\bI(?:'ve| have)?\s+(?:just\s+|already\s+|now\s+)?(booked|reserved|purchased|paid for|confirmed)\b", re.I),
    re.compile(r"\byour\s+(flights?|hotels?|tickets?|train|stay|booking|reservation)s?\s+(?:is|are|has been|have been)\s+(booked|confirmed|reserved)\b", re.I),
]


def sanitize_user_text(text: str, max_chars: int = 2000) -> str:
    """Normalise, strip control chars and our delimiter tags, and cap the length."""
    text = unicodedata.normalize("NFKC", str(text))
    text = _CONTROL_RE.sub(" ", text)
    text = _TAG_RE.sub(" ", text)
    text = re.sub(r"[ \t]+", " ", text).strip()
    return text[:max_chars]


def wrap_user_request(text: str, max_chars: int = 2000) -> str:
    """Wrap untrusted text in explicit delimiters so the model treats it as data."""
    return f"{OPEN_TAG}\n{sanitize_user_text(text, max_chars)}\n{CLOSE_TAG}"


def detect_injection(text: str) -> list[str]:
    """Names of injection heuristics the raw text trips. Used for flagging; never as the only defence."""
    return [name for name, pat in _INJECTION_PATTERNS.items() if pat.search(text)]


def extract_amounts(text: str) -> list[tuple[float, bool]]:
    """Rupee amounts mentioned in text as (value, was_abbreviated) pairs."""
    out: list[tuple[float, bool]] = []
    for m in _AMOUNT_RE.finditer(text):
        raw, unit = (m.group("a"), m.group("au")) if m.group("a") else (m.group("b"), m.group("bu"))
        unit = unit.lower() if unit else None
        try:
            out.append((float(raw.replace(",", "")) * _UNIT[unit], unit is not None))
        except ValueError:
            continue
    return out


def allowed_amounts(itinerary: Itinerary | None, report: BudgetReport | None, user_budget: float | None = None,
                    extra: list[float] | None = None) -> set[float]:
    """Every rupee figure a reply may legitimately quote: those the tools produced, and the user's own budget."""
    vals: set[float] = {0.0, *(extra or [])}
    if user_budget:
        vals.add(float(user_budget))
    if report:
        c = report.components
        vals.update({report.total, report.per_person, c.transport, c.stay, c.food, c.activities, c.local_transport})
        for extra in (report.budget, report.remaining, report.overage):
            if extra is not None:
                vals.add(float(extra))
    if itinerary:
        vals.add(itinerary.total_cost)
        for d in itinerary.days:
            vals.update({d.day_cost, d.stay_cost, d.local_transport})
            for b in d.blocks:
                vals.update({b.cost_per_person, b.cost_total})
    return {round(float(v), 2) for v in vals}


def validate_reply(reply: str, allowed: set[float]) -> list[str]:
    """Return a list of violations; an empty list means the reply is safe to show."""
    problems: list[str] = []
    for value, abbreviated in extract_amounts(reply):
        tol = 0.02 * value if abbreviated else 1.0
        if not any(abs(value - a) <= max(tol, 1.0) for a in allowed):
            problems.append(f"quotes a price not produced by any tool: {value:,.0f}")
    if any(p.search(reply) for p in _FREE_CLAIMS):
        problems.append("claims the trip is free")
    if any(p.search(reply) for p in _BOOKING_CLAIMS):
        problems.append("claims a booking or payment was made")
    return problems
