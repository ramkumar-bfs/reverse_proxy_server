""""""
# 3rd-Party Imports
from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import APIRouter, Request


# Local Imports
from .utils import query_upstream
from reverse_proxy_server.config import ProductionTrackerSettings

# Module constants
router = APIRouter()
# Production Tracker upstream settings
_APPLICATION_SETTINGS = ProductionTrackerSettings()
_APPLICATION_LIMITER = Limiter(key_func=get_remote_address)

@router.api_route("/", methods=_APPLICATION_SETTINGS.supported_api_methods, tags=["production-tracker"], include_in_schema=False)
@router.api_route("/{full_path:path}", methods=_APPLICATION_SETTINGS.supported_api_methods, tags=["production-tracker"], include_in_schema=False)
@_APPLICATION_LIMITER.limit(f"{_APPLICATION_SETTINGS.rate_limit_per_minute}/minute")
async def production_tracker(request: Request, full_path: str =""):
    """"""
    return await query_upstream(full_path, request, _APPLICATION_SETTINGS)