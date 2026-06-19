""""""
# Default Imports
import logging
# 3rd Party Imports
from contextlib import asynccontextmanager
import httpx

LOGGER = logging.getLogger(__name__)


# Reverse Proxy Server  LifeSpan Configuration
@asynccontextmanager
async def config_application_lifespan(app, settings):
    """"""
    # Application Limit
    limits = httpx.Limits(
        max_connections=settings.max_connections,
        max_keepalive_connections=settings.max_keepalive_connections,
        keepalive_expiry=settings.keepalive_expiry,
    )
    # APPlication Timeout
    timeout = httpx.Timeout(
        connect=settings.connect_timeout,
        read=settings.read_timeout,
        write=settings.write_timeout,
        pool=settings.pool_timeout,
    )
    # Proxy Resolution: Explicit setting wins, then fall back to HTTP_PROXY / HTTPS_PROXY env vars. Normalize scheme in both cases so a bare "host:port" value (common in launch scripts) doesn't crash httpx.
    effective_proxy = settings.outbound_proxy
    if effective_proxy and not effective_proxy.startswith(("http://", "https://")):
        effective_proxy = f"http://{effective_proxy}"

    # Setup HTTP Client
    app.state.http_client = httpx.AsyncClient(
        limits=limits,
        timeout=timeout,
        follow_redirects=True,
        proxy=effective_proxy if effective_proxy else None,
        trust_env=False,  # we handle proxy resolution ourselves above
    )
    LOGGER.info("Reverse Proxy Server started.")
    if effective_proxy:
        LOGGER.info("Outbound proxy →  %s", effective_proxy)
    else:
        LOGGER.info("Outbound proxy →  none (direct connection)")
    LOGGER.info(
        "Pool: max=%d keepalive=%d  |  Timeouts: connect=%.0fs read=%.0fs",
        settings.max_connections,
        settings.max_keepalive_connections,
        settings.connect_timeout,
        settings.read_timeout,
    )

    yield
    await app.state.http_client.aclose()
    LOGGER.info("Reverse Proxy Server shut down cleanly.")