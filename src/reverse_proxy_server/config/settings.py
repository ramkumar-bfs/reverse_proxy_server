""""""
# Local Imports
from reverse_proxy_server import constants as CONSTANTS

# 3rd-Party Imports
from pydantic_settings import BaseSettings

class ReverseProxySettings(BaseSettings):
    """"""
    application_name: str = CONSTANTS.APP_TITLE
    version: str = CONSTANTS.APP_VERSION
    upstream_api_mapper = CONSTANTS.UPSTREAM_API_MAPPER
