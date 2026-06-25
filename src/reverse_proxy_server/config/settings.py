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

    # Proxy self-auth: if set, clients must send this value in X-Proxy-Api-Key.
    proxy_api_key: str = ""

    # Base domain sites are mounted under, as "<subdomain>.<proxy_base_domain>".
    proxy_base_domain: str = CONSTANTS.DEFAULT_PROXY_BASE_DOMAIN

# Production-Tracker Configuration
class ProductionTrackerSettings(ReverseProxySettings):
    """"""
    supported_api_methods: list = CONSTANTS.PRODUCTION_TRACKER_API_METHODS
    rate_limit_per_minute : int = CONSTANTS.PRODUCTION_TRACKER_RATE_LIMIT_PER_MINUTE
    upstream_url : str | None  = None
    
    max_body_bytes: int = CONSTANTS.MAX_BODY_BYTES
    max_retries: int = CONSTANTS.MAX_RETRIES
    retry_min_wait: float = CONSTANTS.RETRY_MIN_WAIT
    retry_max_wait: float = CONSTANTS.RETRY_MAX_WAIT

    # Upstream auth injected into every outbound request to this site. Use ONE of these.
    upstream_authorization: str = ""
    upstream_cookie: str = ""
    upstream_api_key_header: str = ""
    upstream_api_key_value: str = ""

    # 2. Automatically compute the value right after validation
    @model_validator(mode="after")
    def set_upstream_url(self):
        if self.upstream_api_mapper and CONSTANTS.PRODUCTION_TRACKER_SUBDOMAIN in self.upstream_api_mapper:
            self.upstream_url = self.upstream_api_mapper.get(CONSTANTS.PRODUCTION_TRACKER_SUBDOMAIN)
        return self