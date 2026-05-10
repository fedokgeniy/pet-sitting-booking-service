"""
Centralized logging configuration for the service.

Provides a configured logger with a consistent format across the application.
The log level can be controlled via the LOG_LEVEL environment variable
(defaults to INFO).
"""
import logging
import os
import sys

_LOG_FORMAT = (
    "%(asctime)s | %(levelname)-8s | %(name)s | "
    "%(filename)s:%(lineno)d | %(message)s"
)

_configured = False


def configure_logging() -> None:
    """Configure the root logger once for the whole process."""
    global _configured
    if _configured:
        return

    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(_LOG_FORMAT))

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)

    # Tame the very noisy Azure SDK loggers but keep warnings.
    logging.getLogger("azure").setLevel(logging.WARNING)
    logging.getLogger("uamqp").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    _configured = True


def get_logger(name: str) -> logging.Logger:
    """Return a module logger, ensuring logging is configured first."""
    configure_logging()
    return logging.getLogger(name)
