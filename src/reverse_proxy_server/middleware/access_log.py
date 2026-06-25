""""""
# Default Imports
import time
import logging
# 3rd Party Imports
from starlette.middleware.base import BaseHTTPMiddleware

# MODULE CONSTANTS
LOGGER = logging.getLogger(__name__)


class AccessLogMiddleware(BaseHTTPMiddleware):
    """Log every request with method, path, status code, and duration."""

    async def dispatch(self, request, call_next):
        """"""
        start = time.perf_counter()
        response = await call_next(request)
        ms = (time.perf_counter() - start) * 1000
        rid = getattr(request.state, "request_id", "-")
        client_ip = request.client.host if request.client else "-"
        LOGGER.info(
            "%s %s → %d  %.1fms  rid=%s  client=%s",
            request.method,
            request.url.path,
            response.status_code,
            ms,
            rid,
            client_ip,
        )
        return response