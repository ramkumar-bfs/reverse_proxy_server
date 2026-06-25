""""""
# Default Imports
import uuid

# 3rd party Imports
from starlette.middleware.base import BaseHTTPMiddleware

class RequestIDMiddleware(BaseHTTPMiddleware):
    """Attach a unique X-Request-ID to every request for end-to-end tracing."""

    async def dispatch(self, request, call_next):
        """"""
        
        request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["x-request-id"] = request_id
        return response
