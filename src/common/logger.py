import logging
import logging.config
import os
import sys
from pathlib import Path
from typing import Optional

import structlog


def initialize_logging() -> None:
    """Configure structlog to output log entries"""
    if os.getenv("LOG_MODE", "JSON") == "LOCAL":
        renderer = structlog.dev.ConsoleRenderer(colors=True)
    else:
        renderer = structlog.processors.JSONRenderer()

    structlog.configure(
        processors=[
            # If log level is too low, abort pipeline and throw away log entry.
            structlog.stdlib.filter_by_level,
            # Add the name of the logger to event dict.
            structlog.stdlib.add_logger_name,
            # Add log level to event dict.
            structlog.processors.add_log_level,
            # Perform %-style formatting.
            structlog.stdlib.PositionalArgumentsFormatter(),
            # Add a timestamp in ISO 8601 format.
            structlog.processors.TimeStamper(fmt="iso"),
            # If the "stack_info" key in the event dict is true, remove it and
            # render the current stack trace in the "stack" key.
            structlog.processors.StackInfoRenderer(),
            # Replace an ``exc_info`` field with an ``exception`` string field using Python's
            # built-in traceback formatting.
            structlog.processors.dict_tracebacks,
            # Add callsite parameters.
            structlog.processors.CallsiteParameterAdder(
                {
                    structlog.processors.CallsiteParameter.FILENAME,
                    structlog.processors.CallsiteParameter.FUNC_NAME,
                    structlog.processors.CallsiteParameter.LINENO,
                }
            ),
            # If some value is in bytes, decode it to a Unicode str.
            structlog.processors.UnicodeDecoder(),
            renderer,
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(
    logger_name: str,
    log_file: Optional[str] = None,
) -> structlog.BoundLogger:
    """Init logging and return logger with given name.

    Args:
    logger_name (str): name of the logger
    log_file (Optional, optional): Optional .log file to save the logs Defaults to None.

    Returns:
    structlog.BoundLogger: A structlog logger object
    """
    # Create a StreamHandler for console output
    initialize_logging()
    if log_file is None:
        logging.basicConfig(
            format="%(message)s",
            stream=sys.stdout,
            level=logging.INFO,
        )
    else:
        log_file = Path(os.path.join(os.getenv("LOGS_ROOT", os.path.join(os.getcwd(), "logs")), log_file))
        os.makedirs(log_file.parent, exist_ok=True)

        logging.config.dictConfig(
            {
                "version": 1,
                "disable_existing_loggers": False,
                "handlers": {
                    "default": {
                        "level": "INFO",
                        "class": "logging.StreamHandler",
                    },
                    "file": {
                        "level": "INFO",
                        "class": "logging.handlers.WatchedFileHandler",
                        "filename": log_file,
                    },
                },
                "loggers": {
                    "": {
                        "handlers": ["default", "file"],
                        "level": "INFO",
                        "propagate": True,
                    },
                },
            }
        )

    # Get a structlog logger
    logger = structlog.get_logger(logger_name)

    return logger
