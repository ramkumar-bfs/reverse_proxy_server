""""""
# Local Imports
from .reverse_proxy_server import router as reverse_proxy_router
from .production_tracker import router as production_tracker_router

REVERSE_PROXY_ROUTES = [
    # Production Tracker Routes — must be registered before reverse_proxy_router,
    # whose generic asset-fallback catch-all would otherwise swallow
    # /production-tracker requests first (Starlette matches in registration order).
    production_tracker_router,
    # Reverse Proxy Server Routes
    reverse_proxy_router,
]