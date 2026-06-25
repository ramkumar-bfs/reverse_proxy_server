from __future__ import annotations

import logging
import os
import time
import uuid
from contextlib import asynccontextmanager

import httpx
import tenacity
from fastapi import FastAPI, HTTPException, Request, Response
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware

from config import Settings

# ── Settings ──────────────────────────────────────────────────────────────────
settings = Settings()
# ── Rate limiter ──────────────────────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address)


# ── Lifespan: startup / shutdown ──────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    limits = httpx.Limits(
        max_connections=settings.max_connections,
        max_keepalive_connections=settings.max_keepalive_connections,
        keepalive_expiry=settings.keepalive_expiry,
    )
    timeout = httpx.Timeout(
        connect=settings.connect_timeout,
        read=settings.read_timeout,
        write=settings.write_timeout,
        pool=settings.pool_timeout,
    )
    # Resolve effective outbound proxy: explicit setting wins, then fall back to
    # HTTP_PROXY / HTTPS_PROXY env vars. Normalize scheme in both cases so a
    # bare "host:port" value (common in launch scripts) doesn't crash httpx.
    effective_proxy = settings.outbound_proxy
    if not effective_proxy:
        effective_proxy = os.getenv("HTTPS_PROXY") or os.getenv("HTTP_PROXY") or ""
        if effective_proxy and not effective_proxy.startswith(("http://", "https://")):
            effective_proxy = f"http://{effective_proxy}"

    app.state.http_client = httpx.AsyncClient(
        limits=limits,
        timeout=timeout,
        follow_redirects=True,
        proxy=effective_proxy if effective_proxy else None,
        trust_env=False,  # we handle proxy resolution ourselves above
    )
    log.info("Proxy started  →  target: %s", settings.target_api_base_url)
    if effective_proxy:
        log.info("Outbound proxy →  %s", effective_proxy)
    else:
        log.info("Outbound proxy →  none (direct connection)")
    log.info(
        "Pool: max=%d keepalive=%d  |  Timeouts: connect=%.0fs read=%.0fs",
        settings.max_connections,
        settings.max_keepalive_connections,
        settings.connect_timeout,
        settings.read_timeout,
    )
    yield
    await app.state.http_client.aclose()
    log.info("Proxy shut down cleanly.")


# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="ShotGrid FastAPI Proxy",
    description="Production-grade reverse proxy for ShotGrid access from a secured network zone.",
    version="2.0.0",
    lifespan=lifespan,
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# ── Middleware: Request ID ─────────────────────────────────────────────────────
class RequestIDMiddleware(BaseHTTPMiddleware):
    """Attach a unique X-Request-ID to every request for end-to-end tracing."""

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["x-request-id"] = request_id
        return response


# ── Middleware: Access log ─────────────────────────────────────────────────────
class AccessLogMiddleware(BaseHTTPMiddleware):
    """Log every request with method, path, status code, and duration."""

    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        ms = (time.perf_counter() - start) * 1000
        rid = getattr(request.state, "request_id", "-")
        client_ip = request.client.host if request.client else "-"
        log.info(
            "%s %s → %d  %.1fms  rid=%s  client=%s",
            request.method,
            request.url.path,
            response.status_code,
            ms,
            rid,
            client_ip,
        )
        return response


# Middleware order matters: RequestID must run before AccessLog so the log can use the ID.
app.add_middleware(AccessLogMiddleware)
app.add_middleware(RequestIDMiddleware)


# ── Helpers ───────────────────────────────────────────────────────────────────
def _build_target_url(full_path: str, request: Request) -> str:
    base = settings.target_api_base_url.rstrip("/")
    path = f"/{full_path}" if full_path else ""
    qs = request.url.query
    return f"{base}{path}?{qs}" if qs else f"{base}{path}"


def _filter_headers(headers: dict) -> dict:
    return {k: v for k, v in headers.items() if k.lower() not in HOP_BY_HOP_HEADERS}


def _apply_upstream_auth(headers: dict) -> dict:
    if settings.upstream_authorization:
        headers["authorization"] = settings.upstream_authorization
    if settings.upstream_cookie:
        headers["cookie"] = settings.upstream_cookie
    if settings.upstream_api_key_header and settings.upstream_api_key_value:
        headers[settings.upstream_api_key_header] = settings.upstream_api_key_value
    return headers


def _check_proxy_auth(request: Request) -> None:
    """Reject requests that don't carry the correct proxy API key (if configured)."""
    if not settings.proxy_api_key:
        return
    if request.headers.get("x-proxy-api-key", "") != settings.proxy_api_key:
        raise HTTPException(status_code=401, detail="Invalid or missing X-Proxy-Api-Key.")


async def _read_body(request: Request) -> bytes:
    """Buffer the request body, enforcing the configured size limit."""
    chunks: list[bytes] = []
    total = 0
    async for chunk in request.stream():
        total += len(chunk)
        if total > settings.max_body_bytes:
            raise HTTPException(
                status_code=413,
                detail=f"Request body exceeds the {settings.max_body_bytes // (1024 * 1024)} MB limit.",
            )
        chunks.append(chunk)
    return b"".join(chunks)


# ── Endpoints ─────────────────────────────────────────────────────────────────
@app.get("/health", tags=["ops"])
async def health_check(request: Request):
    """
    Liveness + readiness check.
    Returns 200 when the proxy is up and can reach the upstream ShotGrid server.
    Returns 503 when the upstream is unreachable.
    """
    upstream_ok = False
    try:
        resp = await request.app.state.http_client.get(
            settings.target_api_base_url.rstrip("/") + "/",
            timeout=5.0,
        )
        upstream_ok = resp.status_code < 500
    except Exception:
        pass

    payload = {
        "status": "ok" if upstream_ok else "degraded",
        "upstream": settings.target_api_base_url,
        "upstream_reachable": upstream_ok,
    }
    if not upstream_ok:
        return Response(
            content=str(payload),
            status_code=503,
            media_type="application/json",
        )
    return payload


_PROXY_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"]


@app.api_route("/", methods=_PROXY_METHODS, include_in_schema=False)
@app.api_route("/{full_path:path}", methods=_PROXY_METHODS, tags=["proxy"])
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def proxy_request(request: Request, full_path: str = ""):
    """Forward any request to the upstream ShotGrid server."""
    _check_proxy_auth(request)

    target_url = _build_target_url(full_path, request)
    body = await _read_body(request)
    headers = _apply_upstream_auth(_filter_headers(dict(request.headers)))
    rid = getattr(request.state, "request_id", "-")

    log.debug("→ upstream  %s %s  rid=%s", request.method, target_url, rid)

    # Retry on transient network errors (connect drops, protocol resets, timeouts).
    # Does NOT retry on 4xx/5xx — those are intentional upstream responses.
    try:
        async for attempt in tenacity.AsyncRetrying(
            stop=tenacity.stop_after_attempt(settings.max_retries),
            wait=tenacity.wait_exponential(
                min=settings.retry_min_wait,
                max=settings.retry_max_wait,
            ),
            retry=tenacity.retry_if_exception_type(
                (httpx.ConnectError, httpx.RemoteProtocolError)
            ),
            reraise=True,
        ):
            with attempt:
                upstream = await request.app.state.http_client.request(
                    method=request.method,
                    url=target_url,
                    headers=headers,
                    content=body,
                )
    except httpx.TimeoutException:
        log.warning("Upstream timeout  rid=%s  url=%s", rid, target_url)
        raise HTTPException(status_code=504, detail="Upstream request timed out.")
    except httpx.RequestError as exc:
        log.error("Upstream unreachable  rid=%s  error=%s", rid, type(exc).__name__)
        raise HTTPException(status_code=502, detail="Could not reach the upstream API.")

    response_headers = _filter_headers(dict(upstream.headers))
    response_headers["x-request-id"] = rid

    return Response(
        content=upstream.content,
        status_code=upstream.status_code,
        headers=response_headers,
        media_type=upstream.headers.get("content-type"),
    )
