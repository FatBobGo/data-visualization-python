"""Modular logging configuration.

Provides a factory function that creates loggers with both console (colored)
and rotating file handlers. Each module should call get_logger(__name__).
"""

import logging
import os
from logging.handlers import RotatingFileHandler

from dataviz.config import get_settings

_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_configured = False


def _setup_log_directory() -> str:
    """Ensure the log directory exists and return its path."""
    settings = get_settings()
    log_dir = settings.log_dir
    os.makedirs(log_dir, exist_ok=True)
    return log_dir


def _get_log_level() -> int:
    """Return the numeric log level from settings."""
    settings = get_settings()
    return getattr(logging, settings.log_level.upper(), logging.INFO)


def get_logger(name: str) -> logging.Logger:
    """Create or retrieve a logger with console and rotating file handlers.

    Args:
        name: Logger name, typically __name__ of the calling module.

    Returns:
        Configured logger instance.
    """
    global _configured

    logger = logging.getLogger(name)
    log_level = _get_log_level()

    # Only add handlers if this is the first call for this logger
    if not logger.handlers:
        logger.setLevel(log_level)
        formatter = logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT)

        # Console handler with colored output
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # Rotating file handler — 10MB per file, 5 backups
        log_dir = _setup_log_directory()
        file_handler = RotatingFileHandler(
            os.path.join(log_dir, "dataviz.log"),
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        # Prevent propagation to root logger to avoid duplicate messages
        logger.propagate = False

    return logger
