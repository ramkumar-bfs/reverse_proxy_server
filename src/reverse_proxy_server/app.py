""""""
# Default Imports
import logging

# Local Import
from .config.settings import ReverseProxySettings
from .api.routes import REVERSE_PROXY_ROUTES
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

# Include API Routes
app.include_router(*REVERSE_PROXY_ROUTES)