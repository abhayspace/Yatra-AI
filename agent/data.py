"""Loader and lookup helpers for the bundled grounding dataset (data/destinations.json)."""
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

from agent.models import Dataset, Destination, Origin

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "destinations.json"


@lru_cache
def load_dataset() -> Dataset:
    return Dataset.model_validate(json.loads(DATA_PATH.read_text(encoding="utf-8")))


def normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9 ]+", " ", text.lower()).strip()


def _squash(text: str) -> str:
    return re.sub(r"\s+", " ", normalize(text))


def find_origin(name: str | None) -> Origin | None:
    if not name:
        return None
    key = _squash(name)
    if not key:
        return None
    for origin in load_dataset().origins.values():
        names = {_squash(origin.name), *(_squash(a) for a in origin.aliases)}
        if key in names:
            return origin
    return None


def get_destination(dest_id: str) -> Destination | None:
    for dest in load_dataset().destinations:
        if dest.id == dest_id:
            return dest
    return None


def match_destinations(name: str | None) -> list[Destination]:
    """Destinations whose name, alias or region matches the text (exact phrase match only)."""
    if not name:
        return []
    key = _squash(name)
    if len(key) < 3:
        return []
    exact: list[Destination] = []
    by_region: list[Destination] = []
    for dest in load_dataset().destinations:
        names = {_squash(dest.name), _squash(dest.id), *(_squash(a) for a in dest.aliases)}
        # also the plain name without a parenthesised part, e.g. "Kerala (Kochi, ...)" -> "kerala"
        names.add(_squash(re.sub(r"\(.*?\)", "", dest.name)))
        if key in names:
            exact.append(dest)
        elif key == _squash(dest.region) or key == _squash(dest.state):
            by_region.append(dest)
    return exact or by_region
