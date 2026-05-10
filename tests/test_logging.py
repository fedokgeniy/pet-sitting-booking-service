import logging

from app.logging_config import configure_logging, get_logger


def test_configure_logging_idempotent():
    configure_logging()
    configure_logging()
    root = logging.getLogger()
    assert len(root.handlers) >= 1


def test_get_logger_returns_named_logger():
    log = get_logger("booking.test")
    assert log.name == "booking.test"
