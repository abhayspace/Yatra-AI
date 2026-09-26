"""FastAPI app exposing the Yatra AI graph over REST and a streaming WebSocket."""
from __future__ import annotations

import logging
import re
import uuid
from contextlib import asynccontextmanager
from functools import lru_cache
from typing import Any, Iterator

from fastapi import Depends, FastAPI, Header, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from starlette.concurrency import iterate_in_threadpool

from agent.graph import Deps, build_graph
from agent.llm_client import get_llm
from agent.settings import ConfigError, Settings, get_settings
from backend.observability import request_id_var, setup_logging
from backend.owner import Unauthorized, owner_hash
from backend.ratelimit import RateLimiter
from backend.repository import PersistenceError, get_repository
from backend.schemas import ChatRequest
from backend.service import ChatService, TripNotFound

log = logging.getLogger("yatra.api")


@lru_cache
def _graph():
    settings = get_settings()
    return build_graph(Deps(llm=get_llm(), settings=settings))


def get_service() -> ChatService:
    """Dependency: production wiring. Tests override this with in-memory doubles."""
    return ChatService(get_repository(), _graph, get_settings())


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    yield


app = FastAPI(title="Yatra AI API", version="1.0.0", lifespan=lifespan)
_settings = get_settings()
limiter = RateLimiter(_settings.rate_limit_per_minute)
_REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9._-]{8,64}$")


@app.middleware("http")
async def correlation_id(request: Request, call_next):
    """Attach a request id to every log line and echo it back so a failure can be traced."""
    inbound = request.headers.get("x-request-id", "")
    rid = inbound if _REQUEST_ID_RE.match(inbound) else uuid.uuid4().hex[:16]
    token = request_id_var.set(rid)
    try:
        response = await call_next(request)
    finally:
        request_id_var.reset(token)
    response.headers["X-Request-ID"] = rid
    return response


def client_key(request: Request | WebSocket) -> str:
    """Client address for rate limiting.

    Behind N trusted proxies the real client is the Nth entry from the right of X-Forwarded-For (each trusted
    proxy appends the address it saw); entries further left are client-supplied and ignored, so they cannot be spoofed.
    """
    hops = get_settings().trusted_proxy_hops
    forwarded = [p.strip() for p in request.headers.get("x-forwarded-for", "").split(",") if p.strip()]
    if hops and len(forwarded) >= hops:
        return forwarded[-hops][:64]
    return request.client.host if request.client else "unknown"


def owner(x_owner_token: str | None = Header(default=None)) -> str:
    """Dependency: hash of the caller's anonymous owner token (see backend/owner.py)."""
    return owner_hash(x_owner_token)


app.add_middleware(
    CORSMiddleware,
    allow_origins=_settings.cors_origin_list,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-Owner-Token", "X-Request-ID"],
)


def _error_response(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"detail": {"code": code, "message": message}})


@app.exception_handler(Unauthorized)
async def _unauthorized(request: Request, exc: Unauthorized) -> JSONResponse:
    return _error_response(401, "unauthorized", "This browser has no valid owner token. Reload the page and try again.")


@app.exception_handler(TripNotFound)
async def _trip_not_found(request: Request, exc: TripNotFound) -> JSONResponse:
    return _error_response(404, "not_found", "That trip no longer exists.")


@app.exception_handler(PersistenceError)
async def _persistence_error(request: Request, exc: PersistenceError) -> JSONResponse:
    return _error_response(503, "database", str(exc))


@app.exception_handler(ConfigError)
async def _config_error(request: Request, exc: ConfigError) -> JSONResponse:
    return _error_response(503, "config", str(exc))


@app.exception_handler(Exception)
async def _unhandled(request: Request, exc: Exception) -> JSONResponse:
    log.exception("unhandled error")
    return _error_response(500, "internal", "Something went wrong on our side. Please try again.")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/trips")
def list_trips(who: str = Depends(owner), service: ChatService = Depends(get_service)) -> list[dict[str, Any]]:
    return service.list_trips(who)


@app.get("/api/trips/latest")
def latest_trip(who: str = Depends(owner), service: ChatService = Depends(get_service)) -> dict[str, Any] | None:
    """This browser's most recently updated trip with its messages and versions, or null if there are none."""
    return service.latest_payload(who)


@app.get("/api/trips/{trip_id}")
def get_trip(trip_id: str, who: str = Depends(owner), service: ChatService = Depends(get_service)) -> dict[str, Any]:
    return service.trip_payload(service.get_trip(trip_id, who))


@app.post("/api/chat")
def chat(req: ChatRequest, request: Request, who: str = Depends(owner), service: ChatService = Depends(get_service)) -> dict[str, Any]:
    """Run one turn and return the final result (the WebSocket streams the same turn live)."""
    key = client_key(request)
    if not limiter.allow(key):
        raise HTTPException(429, {"code": "rate_limited", "message": "You're sending requests too quickly. Please wait a moment."},
                            headers={"Retry-After": str(limiter.retry_after(key))})
    last: dict[str, Any] = {}
    for event in service.run_turn(req.trip_id, req.message, who):
        last = event
    if last.get("type") == "error":
        status = {"not_found": 404, "database": 503, "config": 503, "limit": 422}.get(last["error"]["code"], 500)
        raise HTTPException(status, last["error"])
    return last["result"]


def _resolve_service() -> ChatService:
    """Same wiring as the REST dependency, so tests can override it for WebSocket calls too."""
    return app.dependency_overrides.get(get_service, get_service)()


def _origin_allowed(ws: WebSocket, settings: Settings) -> bool:
    origin = ws.headers.get("origin")
    return origin is None or origin.rstrip("/") in settings.cors_origin_list


@app.websocket("/ws/chat")
async def chat_ws(ws: WebSocket) -> None:
    """Client sends {trip_id?, message}; server streams step/tool events and ends each turn with done or error."""
    if not _origin_allowed(ws, get_settings()):
        await ws.close(code=1008)
        return
    await ws.accept()
    try:
        while True:
            raw = await ws.receive_json()
            try:
                req = ChatRequest.model_validate(raw)
            except ValidationError:
                await ws.send_json({"type": "error", "error": {"code": "invalid", "message": "Please send a message between 1 and 2000 characters."}})
                continue
            try:
                who = owner_hash(raw.get("owner_token") if isinstance(raw, dict) else None)
            except Unauthorized:
                await ws.send_json({"type": "error", "error": {"code": "unauthorized", "message": "This browser has no valid owner token. Reload the page and try again."}})
                continue
            if not limiter.allow(client_key(ws)):
                await ws.send_json({"type": "error", "error": {"code": "rate_limited", "message": "You're sending requests too quickly. Please wait a moment."}})
                continue
            try:
                service = _resolve_service()
            except Exception as exc:  # noqa: BLE001 - e.g. missing configuration
                code = "config" if isinstance(exc, ConfigError) else "internal"
                message = str(exc) if isinstance(exc, ConfigError) else "Something went wrong on our side."
                await ws.send_json({"type": "error", "error": {"code": code, "message": message}})
                continue
            token = request_id_var.set(uuid.uuid4().hex[:16])
            events: Iterator[dict[str, Any]] = service.run_turn(req.trip_id, req.message, who)
            try:
                async for event in iterate_in_threadpool(events):
                    await ws.send_json(event)
            finally:
                request_id_var.reset(token)
    except WebSocketDisconnect:
        return
