""""""
# Local Imports
from .. import constants as CONSTANTS


LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": CONSTANTS.LOGGING_MSG_FORMAT,
            "datefmt": CONSTANTS.LOGGING_DATE_FORMAT,
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
            "level": CONSTANTS.PACKAGE_LOGGING_LEVEL,
        },
    },
    "loggers": {
        # Catch and handle logs specifically coming from your package
        "reverse_proxy_server": {
            "handlers": ["console"],
            "level": CONSTANTS.PACKAGE_LOGGING_LEVEL,
            "propagate": False,  # Prevent sending logs to the root logger twice
        },
    },
    "root": {  # Fallback for all other third-party libraries
        "handlers": ["console"],
        "level": CONSTANTS.ROOT_LOGGING_LEVEL,
    },
}
