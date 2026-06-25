""""""
# Default Imports
import logging

# Local Import
from .middleware import RequestIDMiddleware, AccessLogMiddleware
from .config import ReverseProxySettings
from .api import ROUTES
from .life_span import config_application_lifespan
# 3rd-Party Imports

from fastapi import FastAPI

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

# Include API Routes
for route in ROUTES:
    app.include_router(route)

