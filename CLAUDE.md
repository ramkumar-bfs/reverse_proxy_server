# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A FastAPI reverse proxy that sits between clients and a ShotGrid server, forwarding requests through a secured network zone. It injects upstream auth (bearer token / cookie / API key header), strips hop-by-hop headers, retries transient connect failures, rate-limits per client IP, and optionally requires its own proxy API key from callers.

## Commands

```bash
pip install -r requirements.txt      # install runtime deps (fastapi, uvicorn, httpx, slowapi, tenacity, shotgun_api3, pydantic-settings)
python -m reverse_proxy_server       # run the packaged app (src/reverse_proxy_server/__main__.py), reads .env
pytest tests/                        # run tests (no pytest config/conftest present; this is the only test file)
pytest tests/test_resverse_sg_proxy_example.py   # run the single test/example file
```

There is no lint/format tooling configured (no ruff/black/flake8 config in the repo).

Configuration is via `.env` at the repo root (loaded by `pydantic-settings`). Required vars: `REVERSE_PROXY_HOST`, `REVERSE_PROXY_PORT`, `TARGET_API_BASE_URL`. See `.env` for the full list (timeouts, connection pool sizing, retry policy, rate limit, max body size, outbound corporate proxy).

The VS Code launch config (`.vscode/launch.json`) runs the module as `reverse_proxy_server` with `envFile` set to `.env`.

## Architecture — two parallel, divergent implementations

This codebase currently contains **two separate proxy implementations that don't share code**, at different stages of completeness. When making changes, check which one the user means.

1. **`src/reverse_proxy_server/sg_proxy_server.py`** — a complete, single-file ShotGrid proxy: request-ID + access-log middleware, `slowapi` rate limiting, `tenacity` retry-on-connect-error, header filtering via `HOP_BY_HOP_HEADERS`, upstream auth injection, body-size guard, `/health` upstream-reachability check, and a catch-all `/{full_path:path}` route forwarding all HTTP methods to `TARGET_API_BASE_URL`. Its settings model is `Settings` in `src/reverse_proxy_server/config.py`, which it imports as `from config import Settings` (a bare/absolute import, not a relative one) — this only resolves if `config.py`'s directory is on `sys.path` directly (e.g. running this file as a script from inside `src/reverse_proxy_server/`), not when importing it as part of the `reverse_proxy_server` package.
2. **The packaged app** — `app.py` builds the `FastAPI` instance, wires `life_span.py`'s `config_application_lifespan` (creates the shared `httpx.AsyncClient` with pool/timeout settings) and `api/routes.py` → `api/reverse_proxy_server.py`'s `router`. This is the actual entry point run by `__main__.py` / `python -m reverse_proxy_server`. It is currently a stub: the router only has `/` (welcome message) and `/list_up_stream` (hardcoded placeholder list) — none of the actual forwarding/retry/rate-limit/auth logic from `sg_proxy_server.py` has been ported in. `api/production_tracker.py` and `middleware/rate_limiter.py` are empty placeholder files.

**Known conflict:** `src/reverse_proxy_server/config.py` and `src/reverse_proxy_server/config/` (a package with `settings.py` defining `ReverseProxySettings`) coexist in the same directory. Python's import system resolves `config` to the package, not the module — so `config.py`'s `Settings` class is unreachable via normal package-relative imports (`import config` resolves to the empty `config/__init__.py`). `sg_proxy_server.py`'s `from config import Settings` import is currently broken when run as part of the installed package; it only works if invoked in a context where `config.py` shadows the package (e.g. script run directly from that directory). If asked to fix or unify configuration, this collision needs to be resolved (e.g. rename one, or move `Settings` into `config/settings.py` and update the import).

Constants shared by both implementations (header allowlist/denylist, app title/version, logging format, env var names) live in `constants.py`. Logging setup (`dictConfig`-based, package logger `reverse_proxy_server` set to propagate=False) is in `logging.py` and wired via `utils.config_logger()`.

`tests/test_resverse_sg_proxy_example.py` is not a pytest test — it's a standalone example script demonstrating direct `shotgun_api3` access to ShotGrid (bypassing the proxy entirely), used as a reference for what fields/filters look like against the real API.
