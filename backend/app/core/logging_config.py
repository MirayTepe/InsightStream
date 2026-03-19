"""Structured logging configuration."""

import logging
import sys
from typing import Any

from app.core.config import settings

# JSON-like structure for production; human-readable for dev
LOG_FORMAT_DEV = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
LOG_FORMAT_PROD = '{"time":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","msg":"%(message)s"}'


def get_log_format() -> str:
    """Return format string based on environment."""
    return LOG_FORMAT_PROD if settings.environment == "prod" else LOG_FORMAT_DEV


def configure_logging() -> None:
    """Configure application logging."""
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    format_str = get_log_format()

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    handler.setFormatter(logging.Formatter(format_str))

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers = [handler]

    # Reduce noise from third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a module."""
    return logging.getLogger(name)
