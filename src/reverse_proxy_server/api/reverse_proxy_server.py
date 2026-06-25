""""""
# 3rd-Party Imports
from fastapi import APIRouter, Request

# Local Imports
from .utils import query_upstream
from reverse_proxy_server.config import ProductionTrackerSettings

router = APIRouter()

# Endpoint for welcome message
@router.get("/", tags=["HomePage"])
async def welcome():
    """"""
    return {"message": "Welcome to the Reverse Proxy Server!"}

@router.get("/list_up_stream", tags=["Upstreams"])
async def list_upstream():
    """"""
    # Placeholder for actual upstream listing logic
    return {"upstreams": ["upstream1", "upstream2", "upstream3"]}

# production-tracker (ShotGrid) emits root-absolute paths (e.g. /dist/...,
# /javascripts/..., /forge/init_authentication) that bypass the
# /production-tracker prefix entirely, since the browser resolves them
# against the bare host. There's no other site sharing this fallback, so
# anything not already claimed by an earlier route (welcome, list_up_stream,
# /production-tracker/*) is forwarded to production-tracker by default,
# rather than maintaining a per-prefix allowlist that needs a new entry
# every time ShotGrid's UI or its OAuth flow surfaces another first-party
# endpoint.
_DEFAULT_SITE_SETTINGS = ProductionTrackerSettings()

@router.api_route(
    "/{full_path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
    include_in_schema=False,
)
async def default_site_fallback(request: Request, full_path: str):
    """"""
    return await query_upstream(full_path, request, _DEFAULT_SITE_SETTINGS)