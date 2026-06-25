""""""
# Local Imports
from .. import constants as CONSTANTS
from .reverse_proxy_server import router as reverse_proxy_router
from .production_tracker import router as production_tracker_router

# Routers mounted regardless of which hostname the request came in on.
GLOBAL_ROUTES = [
    reverse_proxy_router,
]

# Routers mounted only under their own subdomain ("<subdomain>.<proxy_base_domain>"),
# so upstream apps that emit root-absolute asset paths resolve correctly.
SITE_ROUTES = [
    (CONSTANTS.PRODUCTION_TRACKER_SUBDOMAIN, production_tracker_router),
]