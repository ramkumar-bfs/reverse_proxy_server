""""""

# MODULE CONSTANTS
# Unicorn CONSTANTS
DEFAULT_MAX_WORKERS = 4
DEFAULT_MODE = "development"
#######################################################

# Reverse Proxy Configuration settings
# TODO: Convert the configuration to yaml file
# TIMEOUTS SETTINGS
CONNECT_TIMEOUT=10
READ_TIMEOUT=60
WRITE_TIMEOUT=30
POOL_TIMEOUT=10

# CONNECTION SETTINGS
MAX_CONNECTIONS = 100
MAX_KEEPALIVE_CONNECTIONS=30
KEEPALIVE_EXPIRY=30

# Retry Settings
MAX_RETRIES=3
RETRY_MIN_WAIT=0.5
RETRY_MAX_WAIT=5.0

# RATE LIMITING SETTINGS
RATE_LIMIT_PER_MINUTE=300 # Per Client

# Body Size Limit (bytes)
MAX_BODY_BYTES=536870912 # 512MB

# UPSTREAM SETTINGS
UPSTREAM_API_MAPPER = {
    "production-tracker": "https://production-tracker.example.com",
    "google": "https://www.google.com"
    }

###############################################################

# FASTAPI CONSTANTS
APP_TITLE = "Reverse Proxy Server"
APP_VERSION = "1.0"
#############################################################

# UNICORN CONSTANTS
HOST= "REVERSE_PROXY_HOST"
PORT= "REVERSE_PROXY_PORT"
MAX_WORKERS="REVERSE_PROXY_MAX_WORKERS"
REVERSE_PROXY_MODE="REVERSE_PROXY_MODE"
PROXY_URL = "PROXY_URL"
###########################################################

# LOGGING CONSTANTS
LOGGING_MSG_FORMAT = "%(asctime)s %(levelname)-8s %(name)s — %(message)s"
LOGGING_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
PACKAGE_LOGGING_LEVEL = "INFO"
ROOT_LOGGING_LEVEL = "INFO"

############################################################

# REVERSE_PROXY SERVER CONSTANTS
# Header names that should be stripped from requests and responses when forwarding to upstream servers. See https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers#hop-by-hop_headers
HOP_BY_HOP_HEADERS = {
    "connection", "keep-alive", "proxy-authenticate", "proxy-authorization",
    "te", "trailers", "transfer-encoding", "upgrade", "host",
    "content-length", "content-encoding", "permissions-policy",
    # Prevent internal client IPs leaking to ShotGrid
    "x-forwarded-for", "x-forwarded-host", "x-forwarded-proto",
    "x-real-ip", "x-original-ip",
    # Strip proxy auth before forwarding to ShotGrid
    "x-proxy-api-key",
}
###############################################################