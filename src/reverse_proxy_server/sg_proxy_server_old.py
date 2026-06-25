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
