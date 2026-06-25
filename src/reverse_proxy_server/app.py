""""""
# Default Imports
import logging

# Local Import
from .middleware import RequestIDMiddleware, AccessLogMiddleware
from .config import ReverseProxySettings
from .api import GLOBAL_ROUTES, SITE_ROUTES
from .life_span import config_application_lifespan
# 3rd-Party Imports

from fastapi import FastAPI
from starlette.routing import Host, Router

# MODULE CONSTANTS
LOGGER = logging.getLogger(__name__)
_APPLICATION_SETTINGS = ReverseProxySettings()



# FastAPI Application Instance
app = FastAPI(
    title=_APPLICATION_SETTINGS.application_name,
    version=_APPLICATION_SETTINGS.version,
    lifespan=lambda app: config_application_lifespan(app, _APPLICATION_SETTINGS)
)

# Add MiddleWare to Application
app.add_middleware(RequestIDMiddleware)
app.add_middleware(AccessLogMiddleware)

# Routes mounted only under their own subdomain, so upstream apps that emit
# root-absolute asset paths (e.g. ShotGrid's /dist/...) resolve correctly.
# Must be registered before the host-agnostic global routes below: Starlette
# matches routes in order, and a plain Route (no host restriction) would
# otherwise match a subdomain's "/" before the Host() entry ever gets a look.
for subdomain, router in SITE_ROUTES:
    app.router.routes.append(
        Host(f"{subdomain}.{_APPLICATION_SETTINGS.proxy_base_domain}", app=Router(routes=router.routes))
    )

# Routes available on any other hostname
for route in GLOBAL_ROUTES:
    app.include_router(route)

