""""""
# Default Imports
import logging
# 3rd-Party Imports
import uvicorn

# Local Imports
from .utils import  get_host, get_port, get_max_workers, hot_reload

# MODULE CONSTANTS
LOGGER = logging.getLogger(__name__)


if __name__ == "__main__":
    """"""
    LOGGER.info("Starting Reverse Proxy Server...")
    # Placeholder for actual server startup logic
    uvicorn.run("reverse_proxy_server.app:app", host=get_host(), port=get_port(), workers=get_max_workers(), reload=hot_reload())