"""Request and response shapes for the REST/WebSocket API."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator

MAX_MESSAGE_CHARS = 2000


class ChatRequest(BaseModel):
    trip_id: str | None = None
    message: str = Field(min_length=1, max_length=MAX_MESSAGE_CHARS)

    @field_validator("message")
    @classmethod
    def _not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Message cannot be blank.")
        return v


class ApiError(BaseModel):
    code: str  # llm | database | limit | config | internal
    message: str


class ChatResult(BaseModel):
    trip_id: str
    reply: str
    error: ApiError | None = None
    tool_trace: list[dict[str, Any]] = Field(default_factory=list)
    itinerary: dict[str, Any] | None = None
    budget_report: dict[str, Any] | None = None
    intent: dict[str, Any] | None = None
    version: int = 0
    change_summary: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
