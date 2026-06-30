"""
logger_setup.py
===============
Configures rotating file + console logging for DONSS.
Call setup_logging() once at application startup.
"""

from __future__ import annotations

import logging
import os
from logging.handlers import RotatingFileHandler

from core.constants import APP_NAME, LOG_FILE


def setup_logging(level: int = logging.DEBUG) -> logging.Logger:
    """
    Create and configure the root logger.

    Args:
        level: Minimum log level (default DEBUG).

    Returns:
        Configured root logger instance.
    """
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Avoid adding duplicate handlers on repeated calls
    if root_logger.handlers:
        return root_logger

    fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Rotating file handler – max 5 MB, keep 3 backups
    fh = RotatingFileHandler(
        LOG_FILE,
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)

    # Console handler – INFO and above only
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(fmt)

    root_logger.addHandler(fh)
    root_logger.addHandler(ch)

    root_logger.info("=" * 70)
    root_logger.info("  %s — Application Started", APP_NAME)
    root_logger.info("=" * 70)

    return root_logger
