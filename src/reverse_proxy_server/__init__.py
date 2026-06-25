""""""
# Default Imports
import logging
from logging.config import dictConfig

# Local import
from reverse_proxy_server.config import LOGGING_CONFIG

# Config reverse proxy server logging config
dictConfig(LOGGING_CONFIG)
# The parent logger for all modules in this package
logging.getLogger(__name__).addHandler(logging.NullHandler())

