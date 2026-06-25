""""""
# Local Imports
from reverse_proxy_server import constants as CONSTANTS
from reverse_proxy_server.utils import get_proxy_url

# 3rd-Party Imports
from pydantic import model_validator
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

# Production-Tracker Configuration
class ProductionTrackerSettings(ReverseProxySettings):
    """"""
    supported_api_methods: list = CONSTANTS.PRODUCTION_TRACKER_API_METHODS
    rate_limit_per_minute : int = CONSTANTS.PRODUCTION_TRACKER_RATE_LIMIT_PER_MINUTE
    upstream_url : str | None  = None

    # 2. Automatically compute the value right after validation
    @model_validator(mode="after")
    def set_upstream_url(self):
        if self.upstream_api_mapper and "production-tracker" in self.upstream_api_mapper:
            self.upstream_url = self.upstream_api_mapper.get("production-tracker")
        return self