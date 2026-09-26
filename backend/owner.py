"""Anonymous per-browser ownership of trips (isolation without accounts).

The browser generates a random secret and sends it with every request. Only its SHA-256 hash is stored,
inside each trip's state; every list, read and chat operation is scoped to the hash. This is not
authentication (there are no users), but a visitor cannot list, read or modify another visitor's trips even
if they learn a trip id.
"""
from __future__ import annotations

import hashlib
import re

_TOKEN_RE = re.compile(r"^[A-Za-z0-9_-]{32,128}$")


class Unauthorized(Exception):
    """The owner token is missing or malformed."""


def owner_hash(token: str | None) -> str:
    if not token or not _TOKEN_RE.match(token):
        raise Unauthorized()
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
