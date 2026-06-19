from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ── Required ──────────────────────────────────────────────────────────────
    # The actual ShotGrid server this proxy forwards to.
    # Example: http://192.168.1.24:8282
    target_api_base_url: str

    # ── Upstream auth (all optional) ─────────────────────────────────────────
    # Injected into every outbound request to ShotGrid.
    upstream_authorization: str = ""
    upstream_cookie: str = ""
    upstream_api_key_header: str = ""
    upstream_api_key_value: str = ""

    # ── Proxy self-auth (optional) ────────────────────────────────────────────
    # If set, every client request must include this value in X-Proxy-Api-Key.
    # Leave empty to disable proxy-level auth (rely on network/firewall instead).
    proxy_api_key: str = ""

    # ── Timeouts (seconds) ────────────────────────────────────────────────────
    connect_timeout: float = 10.0   # time to establish TCP connection
    read_timeout: float = 60.0      # time waiting for upstream response bytes
    write_timeout: float = 30.0     # time to send request body upstream
    pool_timeout: float = 10.0      # time to acquire a connection from the pool

    # ── Connection pool ───────────────────────────────────────────────────────
    # Tune based on concurrent users. 100 connections handles 30+ users safely.
    max_connections: int = 100
    max_keepalive_connections: int = 30
    keepalive_expiry: float = 30.0  # seconds to keep idle connections alive

    # ── Retry on transient upstream failures ──────────────────────────────────
    max_retries: int = 3
    retry_min_wait: float = 0.5     # seconds
    retry_max_wait: float = 5.0     # seconds (exponential backoff cap)

    # ── Rate limiting ─────────────────────────────────────────────────────────
    # Max requests per minute per client IP hitting the proxy.
    rate_limit_per_minute: int = 300

    # ── Body size guard ───────────────────────────────────────────────────────
    # Prevents memory exhaustion from very large uploads. Default 512 MB.
    max_body_bytes: int = 512 * 1024 * 1024

    # ── Outbound proxy ────────────────────────────────────────────────────────
    # Corporate/network HTTP proxy the FastAPI process must route through to
    # reach the upstream ShotGrid server. Leave blank for direct connections.
    # Accepts both "10.10.1.52:3128" and "http://10.10.1.52:3128".
    outbound_proxy: str = ""

    @field_validator("outbound_proxy")
    @classmethod
    def ensure_proxy_scheme(cls, v: str) -> str:
        if v and not v.startswith(("http://", "https://")):
            return f"http://{v}"
        return v

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}
