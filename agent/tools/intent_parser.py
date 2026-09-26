"""Intent and constraint extraction, and follow-up interpretation.

The language model reads the free text; a rule-based extractor reads the same text for
explicit numerals (budget, days, travellers, dates). When the text states a number outright,
that number wins over the model's, so a manipulated or mistaken model output cannot move
the budget. Everything the model returns is validated field by field before it is used.
"""
from __future__ import annotations

import re
from datetime import date, timedelta
from typing import Any

from pydantic import BaseModel, ConfigDict, ValidationError

from agent.data import find_origin, load_dataset, match_destinations, normalize
from agent.errors import ToolError
from agent.guardrails import sanitize_user_text, wrap_user_request
from agent.llm_client import LLMClient
from agent.models import INTERESTS, FollowUpParse, IntentDelta, TripIntent
from agent.prompts import FOLLOWUP_SYSTEM, INTENT_SYSTEM
from agent.tools.budget import parse_amount

DEFAULT_DURATION = 3
DEFAULT_TRAVELERS = 1
DEFAULT_PACE = "balanced"

_INTEREST_WORDS: dict[str, tuple[str, ...]] = {
    "nature": ("nature", "scenic", "scenery", "mountain", "mountains", "hills", "hill", "lakes", "waterfalls", "forest", "outdoors", "greenery", "tea garden", "tea gardens", "landscape"),
    "food": ("food", "foodie", "cuisine", "eating", "street food", "culinary", "restaurants", "cafes", "dining"),
    "culture": ("culture", "cultural", "local life", "traditions", "art", "crafts"),
    "adventure": ("adventure", "trekking", "trek", "rafting", "paragliding", "thrill", "adrenaline", "hiking", "water sports"),
    "beach": ("beach", "beaches", "seaside", "coast", "sea"),
    "relaxation": ("relaxation", "relax", "relaxing", "chill", "unwind", "peaceful", "quiet", "laid back", "laid-back"),
    "heritage": ("heritage", "history", "historical", "forts", "fort", "palaces", "palace", "monuments", "architecture"),
    "spiritual": ("spiritual", "temples", "temple", "pilgrimage", "yoga", "ashram", "monastery", "monasteries"),
    "nightlife": ("nightlife", "clubs", "party", "parties", "pubs", "bars"),
    "shopping": ("shopping", "markets", "bazaar", "souvenirs"),
    "wellness": ("wellness", "spa", "ayurveda", "massage", "detox"),
    "wildlife": ("wildlife", "safari", "animals", "birds", "birdwatching", "national park"),
}
_WORD_TO_INTEREST = {w: k for k, words in _INTEREST_WORDS.items() for w in words}
_MONTHS = {m: i + 1 for i, m in enumerate(["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"])}
_MONTHS.update({k[:3]: v for k, v in list(_MONTHS.items())})
_NUM_WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10}
_NUM = r"(?P<n>[0-9]{1,2}|" + "|".join(_NUM_WORDS) + r")"


def _to_int(token: str) -> int:
    return _NUM_WORDS.get(token.lower()) or int(token)


def _interests_in(text: str) -> list[str]:
    low = " " + normalize(text) + " "
    found: list[str] = []
    for word, interest in sorted(_WORD_TO_INTEREST.items(), key=lambda kv: -len(kv[0])):
        if f" {normalize(word)} " in low and interest not in found:
            found.append(interest)
    return sorted(found, key=lambda i: low.index(next(f" {normalize(w)} " for w in _INTEREST_WORDS[i] if f" {normalize(w)} " in low)))


def _find_amount(text: str) -> float | None:
    patterns = [
        r"(?:under|below|within|upto|up to|max(?:imum)?|less than|around|about|budget(?: of| is)?|for|to|of)\s*(?:only |just |about |around |roughly |now |at )?(?:rs\.?|inr|₹)?\s*(?P<a>[0-9][0-9,]*(?:\.[0-9]+)?\s*(?:k|lakhs?|lacs?|l)?)\b(?!\s*(?:days?|nights?|people|persons?|travell?ers?|of us|adults?))",
        r"(?:₹|rs\.?|inr)\s*(?P<a>[0-9][0-9,]*(?:\.[0-9]+)?\s*(?:k|lakhs?|lacs?|l)?)\b",
        r"(?P<a>[0-9][0-9,]*(?:\.[0-9]+)?\s*(?:k|lakhs?|lacs?))\s*(?:budget|total|max|rupees|inr)?\b",
    ]
    for pat in patterns:
        for m in re.finditer(pat, text, re.I):
            raw = m.group("a").strip()
            try:
                value = parse_amount(raw)
            except ToolError:
                continue
            if value >= 1000 or re.search(r"[a-z₹]", m.group(0), re.I) and value >= 500:
                per_person = re.search(r"per\s+(?:person|head|traveller|traveler)|\beach\b|\bpp\b", text[m.end(): m.end() + 25], re.I)
                return -value if per_person else value  # negative marks "per person"
    return None


def heuristic_extract(text: str, today: date | None = None) -> dict[str, Any]:
    """Rule-based extraction of explicit constraints. Returns only what the text states."""
    today = today or date.today()
    out: dict[str, Any] = {}
    low = text.lower()

    # origin: "from Delhi"
    m = re.search(r"\b(?:from|leaving|starting from|departing from|ex-?)\s+([A-Za-z][A-Za-z .'-]{1,30}?)(?=\s+(?:for|to|under|with|within|in|on|by|and|budget|of|we|i|at)\b|[,.;:!?\n]|$)", text, re.I)
    if m:
        out["origin"] = m.group(1).strip()

    # duration
    m = re.search(_NUM + r"\s*(?:-|\s)?\s*(?:day|days|d)\b", low)
    if m and not re.search(_NUM + r"\s*(?:-|\s)?\s*days?\s*(?:of|per)\s*(?:leave|holiday)", low):
        out["duration_days"] = _to_int(m.group("n"))
    else:
        m = re.search(_NUM + r"\s*(?:-|\s)?\s*nights?\b", low)
        if m:
            out["duration_days"] = _to_int(m.group("n")) + 1
        elif re.search(r"\bweekend\b", low):
            out["duration_days"] = 3
        elif re.search(r"\b(a|one)\s+week\b", low):
            out["duration_days"] = 7
        elif re.search(r"\b(two|2)\s+weeks?\b", low):
            out["duration_days"] = 14

    # travellers
    m = re.search(r"\bfor\s+" + _NUM + r"\s*(?:people|persons?|adults?|travell?ers?|pax|of us|friends|members)\b", low) or re.search(
        _NUM + r"\s*(?:people|persons?|adults?|travell?ers?|pax|of us)\b", low)
    if m:
        out["travelers"] = _to_int(m.group("n"))
    elif re.search(r"\b(couple|honeymoon|my (?:wife|husband|partner|girlfriend|boyfriend)|with my (?:wife|husband|partner))\b", low):
        out["travelers"] = 2
    elif re.search(r"\b(solo|alone|by myself|just me)\b", low):
        out["travelers"] = 1
    else:
        m = re.search(r"\bfamily of\s+" + _NUM, low) or re.search(
            r"\bfor\s+" + _NUM + r"\b(?!\s*(?:days?|nights?|weeks?|months?|hours?|k\b|l\b|lakhs?|lacs?|rs\b|inr|₹|%|-))", low)
        if m:
            out["travelers"] = _to_int(m.group("n"))

    # budget (total, INR)
    amount = _find_amount(text)
    if amount is not None:
        if amount < 0:
            out["budget_per_person"] = -amount
        else:
            out["budget"] = amount

    # pace
    if re.search(r"\b(relaxed|relaxing|slow|leisurely|laid[- ]back|easy[- ]going|chill|not (?:too )?packed|unhurried)\b", low):
        out["pace"] = "relaxed"
    elif re.search(r"\b(packed|busy|action[- ]packed|hectic|jam[- ]packed|see as much|fast[- ]paced)\b", low):
        out["pace"] = "packed"
    elif re.search(r"\bbalanced\b", low):
        out["pace"] = "balanced"

    # interests
    interests = _interests_in(text)
    if interests:
        out["interests"] = interests

    # named destinations: any dataset name/alias appearing as a phrase
    named: list[str] = []
    norm = " " + normalize(text) + " "
    for dest in load_dataset().destinations:
        base = re.sub(r"\(.*?\)", "", dest.name).strip()
        for term in {base, *dest.aliases}:
            key = normalize(term)
            if len(key) >= 3 and f" {key} " in norm and base not in named:
                named.append(base)
    origin = find_origin(out.get("origin"))
    if origin:
        named = [n for n in named if n.lower() != origin.name.lower()]
    if named:
        out["destinations"] = named

    # date: ISO, "15 December", "December 15", "in December"
    m = re.search(r"\b(20[0-9]{2})-([01][0-9])-([0-3][0-9])\b", text)
    parsed: date | None = None
    if m:
        try:
            parsed = date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            parsed = None
    else:
        month_re = "|".join(sorted(_MONTHS, key=len, reverse=True))
        m = re.search(rf"\b(?P<d>[0-3]?[0-9])(?:st|nd|rd|th)?\s+(?:of\s+)?(?P<m>{month_re})\b", low) or None
        m2 = re.search(rf"\b(?P<m>{month_re})\s+(?P<d>[0-3]?[0-9])(?:st|nd|rd|th)?\b", low)
        m3 = re.search(rf"\b(?:in|during|this|next)\s+(?P<m>{month_re})\b", low)
        for mm, has_day in ((m, True), (m2, True), (m3, False)):
            if mm:
                month = _MONTHS[mm.group("m")]
                day = int(mm.group("d")) if has_day else 10
                try:
                    candidate = date(today.year, month, day)
                    if candidate < today:
                        candidate = date(today.year + 1, month, day)
                    parsed = candidate
                except ValueError:
                    parsed = None
                break
    if parsed and parsed >= today:
        out["start_date"] = parsed.isoformat()
    return out


# --------------------------------------------------------------------------- LLM output


class LLMIntentOut(BaseModel):
    """Lenient shape for the model's answer; each field is validated individually afterwards."""

    model_config = ConfigDict(extra="ignore")

    origin: str | None = None
    destinations: list[str] | None = None
    region: str | None = None
    duration_days: int | float | str | None = None
    travelers: int | float | str | None = None
    budget: int | float | str | None = None
    interests: list[str] | None = None
    interest_weights: dict[str, float] | None = None
    pace: str | None = None
    start_date: str | None = None
    notes: str | None = None


def _clean_intent(raw: dict[str, Any]) -> TripIntent:
    """Build a TripIntent from untrusted fields, dropping any field that fails validation."""
    data = {k: v for k, v in raw.items() if v not in (None, "", [], {})}
    for _ in range(len(data) + 1):
        try:
            return TripIntent.model_validate(data)
        except ValidationError as exc:
            bad = {str(e["loc"][0]) for e in exc.errors() if e["loc"]}
            if not bad:
                break
            for key in bad:
                data.pop(key, None)
    return TripIntent()


def _coerce_llm_numbers(raw: dict[str, Any]) -> dict[str, Any]:
    out = dict(raw)
    for key in ("duration_days", "travelers"):
        v = out.get(key)
        try:
            out[key] = int(float(v)) if v is not None and float(v) == int(float(v)) else None
        except (TypeError, ValueError):
            out[key] = None
    if out.get("budget") is not None:
        try:
            out["budget"] = parse_amount(out["budget"])
        except ToolError:
            out["budget"] = None
    if out.get("pace") not in (None, "relaxed", "balanced", "packed"):
        out["pace"] = None
    if out.get("start_date"):
        try:
            out["start_date"] = date.fromisoformat(str(out["start_date"])[:10])
        except ValueError:
            out["start_date"] = None
    return out


class ParseResult(BaseModel):
    intent: TripIntent
    missing: list[str]
    heuristics: dict[str, Any]


def merge_intent(base: TripIntent | None, new: TripIntent) -> TripIntent:
    """Overlay `new` on `base`: any field `new` states replaces the old value."""
    if base is None:
        return new
    merged = base.model_copy(deep=True)
    for field in ("origin", "region", "duration_days", "travelers", "budget", "pace", "start_date", "notes"):
        value = getattr(new, field)
        if value not in (None, ""):
            setattr(merged, field, value)
    if new.destinations:
        merged.destinations = new.destinations
    if new.interests:
        merged.interests = list(dict.fromkeys([*merged.interests, *new.interests]))
    if new.interest_weights:
        merged.interest_weights = {**merged.interest_weights, **new.interest_weights}
    return merged


def parse_intent(message: str, llm: LLMClient, prior: TripIntent | None = None, today: date | None = None) -> ParseResult:
    """Extract constraints from `message`, merged over any earlier partial intent."""
    today = today or date.today()
    heur = heuristic_extract(message, today)
    system = INTENT_SYSTEM.format(interests=", ".join(INTERESTS), today=today.isoformat())
    out = llm.complete_structured("parse_intent", system, wrap_user_request(message), LLMIntentOut)
    fields = _coerce_llm_numbers(out.model_dump())

    # explicit numerals stated in the text are authoritative
    for key in ("duration_days", "travelers", "budget", "start_date", "pace", "origin"):
        if key in heur:
            fields[key] = date.fromisoformat(heur[key]) if key == "start_date" else heur[key]
    if "budget_per_person" in heur and heur.get("travelers", fields.get("travelers")):
        fields["budget"] = heur["budget_per_person"] * (heur.get("travelers") or fields.get("travelers"))
    if heur.get("interests"):
        fields["interests"] = list(dict.fromkeys([*(fields.get("interests") or []), *heur["interests"]]))
    if heur.get("destinations") and not fields.get("destinations"):
        fields["destinations"] = heur["destinations"]
    new = _clean_intent(fields)
    intent = merge_intent(prior, new)

    missing: list[str] = []
    if find_origin(intent.origin) is None:
        missing.append("origin")
    if not (intent.destinations or intent.region or intent.interests):
        missing.append("destination_or_interests")
    return ParseResult(intent=intent, missing=missing, heuristics=heur)


def next_friday(today: date, min_lead_days: int = 8) -> date:
    d = today + timedelta(days=min_lead_days)
    return d + timedelta(days=(4 - d.weekday()) % 7)


def apply_defaults(intent: TripIntent, today: date | None = None) -> TripIntent:
    """Fill unstated constraints with sensible defaults and record each assumption."""
    today = today or date.today()
    out = intent.model_copy(deep=True)
    out.assumptions = []
    if out.duration_days is None:
        out.duration_days = DEFAULT_DURATION
        out.assumptions.append(f"Assumed a {DEFAULT_DURATION}-day trip.")
    if out.travelers is None:
        out.travelers = DEFAULT_TRAVELERS
        out.assumptions.append("Assumed 1 traveller.")
    if out.pace is None:
        out.pace = DEFAULT_PACE
        out.assumptions.append("Assumed a balanced pace.")
    if out.start_date is None or out.start_date < today:
        out.start_date = next_friday(today)
        out.assumptions.append(f"Assumed a start date of {out.start_date.isoformat()} so the weather forecast could be checked.")
    if out.budget is None:
        out.assumptions.append("No budget given; planned at mid-range comfort.")
    return out


# --------------------------------------------------------------------------- follow-ups


_QUESTION_START = re.compile(r"^\s*(what|how|why|when|where|which|who|is|are|does|do|can|could|should|will|would|tell me|show me)\b", re.I)
_CHANGE_VERB = re.compile(r"\b(make|change|switch|swap|reduce|extend|shorten|increase|decrease|add|remove|drop|skip|instead|actually|update|replace|cut|lower|raise)\b", re.I)


def heuristic_delta(text: str, current: TripIntent, today: date | None = None) -> dict[str, Any]:
    """Explicit changes stated in a follow-up message."""
    today = today or date.today()
    low = text.lower()
    h = heuristic_extract(text, today)
    delta: dict[str, Any] = {}
    for key in ("duration_days", "travelers", "budget", "pace", "start_date"):
        if key in h:
            delta[key] = h[key]
    if "budget_per_person" in h:
        delta["budget"] = h["budget_per_person"] * (h.get("travelers") or current.travelers or 1)
    if h.get("origin") and find_origin(h["origin"]):
        delta["origin"] = h["origin"]
    if h.get("destinations"):
        delta["destination"] = h["destinations"][0]
    if re.search(r"\b(more relaxed|less packed|slower|slow down|fewer activities|take it easy)\b", low):
        delta["pace"] = "relaxed"
    if re.search(r"\b(more packed|busier|more activities|pack more|faster pace)\b", low):
        delta["pace"] = "packed"

    weights: dict[str, float] = {}
    add: list[str] = []
    remove: list[str] = []
    vocab = "|".join(sorted((re.escape(w) for w in _WORD_TO_INTEREST), key=len, reverse=True))
    for m in re.finditer(rf"\b(?<!no )(?:more|extra|add(?: more)?|include|focus on|emphasi[sz]e)\s+(?:of\s+)?({vocab})\b", low):
        kind = _WORD_TO_INTEREST[m.group(1)]
        weights[kind] = 1.6
        add.append(kind)
    for m in re.finditer(rf"\b(?:less|fewer|reduce|cut down on|not as much)\s+(?:of\s+)?({vocab})\b", low):
        weights[_WORD_TO_INTEREST[m.group(1)]] = 0.5
    for m in re.finditer(rf"\b(?:no more|skip|drop|remove|without|no)\s+(?:the\s+)?({vocab})\b", low):
        kind = _WORD_TO_INTEREST[m.group(1)]
        remove.append(kind)
        weights.pop(kind, None)
    if weights:
        delta["interest_weights"] = weights
    if add:
        delta["add_interests"] = list(dict.fromkeys(add))
    if remove:
        delta["remove_interests"] = list(dict.fromkeys(remove))
    return delta


def _summarise_for_prompt(intent: TripIntent, itinerary: dict | None) -> str:
    lines = [f"Current constraints: {intent.model_dump_json(exclude={'assumptions'}, exclude_none=True)}"]
    if itinerary:
        lines.append(
            f"Current itinerary: {itinerary.get('destination_name')} for {itinerary.get('duration_days')} days, "
            f"{itinerary.get('travelers')} traveller(s), total cost INR {itinerary.get('total_cost'):,.0f}."
        )
    return "\n".join(lines)


def _render_history(history: list[dict[str, str]] | None) -> str:
    """Recent turns for context. Earlier user text is re-wrapped as data; assistant text is our own."""
    lines = []
    for turn in (history or [])[-6:]:
        if turn.get("role") == "user":
            lines.append("user: " + wrap_user_request(turn.get("content", ""), 500).replace("\n", " "))
        else:
            lines.append("assistant: " + sanitize_user_text(turn.get("content", ""), 500))
    return "<recent_turns>\n" + "\n".join(lines) + "\n</recent_turns>\n\n" if lines else ""


def parse_followup(
    message: str, intent: TripIntent, itinerary: dict | None, llm: LLMClient, today: date | None = None,
    history: list[dict[str, str]] | None = None,
) -> FollowUpParse:
    """Interpret a follow-up as a change to the existing trip, a question, or a new trip."""
    today = today or date.today()
    system = FOLLOWUP_SYSTEM.format(interests=", ".join(INTERESTS), today=today.isoformat())
    user = (
        f"<trip_facts>\n{_summarise_for_prompt(intent, itinerary)}\n</trip_facts>\n\n"
        f"{_render_history(history)}{wrap_user_request(message)}"
    )
    raw = llm.complete_structured("parse_followup", system, user, _LLMFollowUpOut)

    heur = heuristic_delta(message, intent, today)
    merged: dict[str, Any] = {}
    llm_delta = _coerce_llm_numbers(raw.delta.model_dump()) if raw.delta else {}
    merged.update({k: v for k, v in llm_delta.items() if v not in (None, "", [], {})})
    for key, value in heur.items():  # explicit numerals / named places in the text win
        if key in ("add_interests", "remove_interests"):
            merged[key] = list(dict.fromkeys([*(merged.get(key) or []), *value]))
        elif key == "interest_weights":
            merged[key] = {**(merged.get(key) or {}), **value}
        else:
            merged[key] = value
    try:
        delta = IntentDelta.model_validate(merged)
    except ValidationError as exc:
        bad = {str(e["loc"][0]) for e in exc.errors() if e["loc"]}
        delta = IntentDelta.model_validate({k: v for k, v in merged.items() if k not in bad})

    action = raw.action if raw.action in ("modify", "new_trip", "question", "other") else "other"
    if action == "modify" and delta.is_empty():
        action = "question" if _QUESTION_START.match(message) and not _CHANGE_VERB.search(message) else "other"
    if action in ("question", "other") and not delta.is_empty() and _CHANGE_VERB.search(message):
        action = "modify"
    return FollowUpParse(action=action, delta=delta, question=(raw.question or message)[:400] if action == "question" else None)


class _LLMDeltaOut(BaseModel):
    model_config = ConfigDict(extra="ignore")

    origin: str | None = None
    destination: str | None = None
    duration_days: int | float | str | None = None
    travelers: int | float | str | None = None
    budget: int | float | str | None = None
    pace: str | None = None
    start_date: str | None = None
    add_interests: list[str] | None = None
    remove_interests: list[str] | None = None
    interest_weights: dict[str, float] | None = None


class _LLMFollowUpOut(BaseModel):
    model_config = ConfigDict(extra="ignore")

    action: str = "other"
    delta: _LLMDeltaOut | None = None
    question: str | None = None


# --------------------------------------------------------------------------- applying a delta


def apply_delta(intent: TripIntent, delta: IntentDelta) -> tuple[TripIntent, list[str]]:
    """Update only the changed constraints. Returns the new intent and the list of what changed."""
    new = intent.model_copy(deep=True)
    affected: list[str] = []

    def changed(field: str, value: Any) -> None:
        if value is not None and getattr(new, field) != value:
            setattr(new, field, value)
            affected.append("start_date" if field == "start_date" else field)

    changed("duration_days", delta.duration_days)
    changed("travelers", delta.travelers)
    changed("budget", delta.budget)
    changed("pace", delta.pace)
    changed("start_date", delta.start_date)
    if delta.origin and find_origin(delta.origin) and (find_origin(delta.origin).name != (find_origin(new.origin).name if find_origin(new.origin) else None)):
        new.origin = find_origin(delta.origin).name
        affected.append("origin")
    if delta.destination:
        hits = match_destinations(delta.destination)
        if hits:
            new.destinations = [hits[0].name.split(" (")[0]]
            new.region = None
            affected.append("destination")
        else:
            new.destinations = [delta.destination]
            affected.append("destination")

    interests = list(new.interests)
    weights = dict(new.interest_weights)
    before = (tuple(interests), tuple(sorted(weights.items())))
    for kind in delta.remove_interests:
        if kind in interests:
            interests.remove(kind)
        weights.pop(kind, None)
    for kind in delta.add_interests:
        if kind not in interests:
            interests.append(kind)
    for kind, w in delta.interest_weights.items():
        weights[kind] = w
        if kind not in interests and w > 0:
            interests.append(kind)
    if (tuple(interests), tuple(sorted(weights.items()))) != before:
        new.interests, new.interest_weights = interests, weights
        affected.append("interests")
    return new, list(dict.fromkeys(affected))
