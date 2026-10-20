# @Time: 2026/10/19 16:59
# @Author: yanggan

import logging.config
from contextvars import ContextVar

request_id_ctx = ContextVar("request_id", default="-")


class RequestIdFilter(logging.Filter):
    def filter(self, record):
        record.request_id = request_id_ctx.get()
        return True


LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "request_id": {
            "()": RequestIdFilter,
        }
    },
    "formatters": {
        "default": {
            "format": "[%(asctime)s] %(levelname)s [%(request_id)s] %(name)s:%(lineno)d - %(message)s",
        },
        "access": {
            "format": "[%(asctime)s] %(levelname)s [%(request_id)s] %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "filters": ["request_id"],
        },
        "access_console": {
            "class": "logging.StreamHandler",
            "formatter": "access",
            "filters": ["request_id"],
        },
    },
    "loggers": {
        "uvicorn.access": {
            "level": "INFO",
            "handlers": ["access_console"],
            "propagate": False,
        },
    },
    "root": {
        "level": "INFO",
        "handlers": ["console"],
    },
}
