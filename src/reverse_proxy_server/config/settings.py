""""""
# Local Imports
from reverse_proxy_server import constants as CONSTANTS
from reverse_proxy_server.utils import get_proxy_url

# 3rd-Party Imports
from pydantic_settings import BaseSettings

class ReverseProxySettings(BaseSettings):
    """"""
    # Application Info
    application_name: str = CONSTANTS.APP_TITLE
    version: str = CONSTANTS.APP_VERSION

    # Reverse Proxy Support upstream mapper
    upstream_api_mapper: dict = CONSTANTS.UPSTREAM_API_MAPPER

    # Reverse Proxy connection settings
    max_connections: int = CONSTANTS.MAX_CONNECTIONS
    max_keepalive_connections: int = CONSTANTS.MAX_KEEPALIVE_CONNECTIONS
    keepalive_expiry: int = CONSTANTS.KEEPALIVE_EXPIRY

    connection_timeout: int = CONSTANTS.CONNECT_TIMEOUT
    read_timeout: int = CONSTANTS.READ_TIMEOUT
    write_timeout: int = CONSTANTS.WRITE_TIMEOUT
    pool_timeout: int = CONSTANTS.POOL_TIMEOUT

    proxy_url: str | None = get_proxy_url()

