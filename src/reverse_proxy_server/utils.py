""""""
# Default Imports
import os
from logging.config import dictConfig

# Local imports
from .logging import LOGGING_CONFIG
from . import constants as CONSTANTS

# MODULE Support Functions
def _get_env(env_name, required=False):
    """"""
    value = os.getenv(env_name)
    if required and not value:
        raise ValueError(f"Environment variable '{env_name}' is required but not set.")
    return value

def get_proxy_url():
    """"""
    return _get_env(CONSTANTS.PROXY_URL)
def get_host():
    """"""
    return _get_env(CONSTANTS.HOST, required=True)

def get_port():
    """"""
    return int(_get_env(CONSTANTS.PORT, required=True))

def get_max_workers():
    """"""
    return int(_get_env(CONSTANTS.MAX_WORKERS) or CONSTANTS.DEFAULT_MAX_WORKERS)

def hot_reload():
    """"""
    mode = _get_env(CONSTANTS.REVERSE_PROXY_MODE)
    return True if mode == CONSTANTS.DEFAULT_MODE else False

def config_logger():
    """"""
    # Setup reverse proxy server logger
    dictConfig(LOGGING_CONFIG)
