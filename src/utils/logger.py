"""Structured logging configuration for PR Agent."""

import logging
import sys
from typing import Optional


def setup_logger(name: str = "pr-agent", level: Optional[str] = None) -> logging.Logger:
    """
    Configure and return a structured logger.

    Args:
        name: Logger name
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
               Falls back to LOG_LEVEL env var, defaults to INFO

    Returns:
        Configured logger instance
    """
    import os

    log_level = level or os.getenv("LOG_LEVEL", "INFO").upper()

    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level, logging.INFO))

    # Avoid duplicate handlers if logger already configured
    if logger.handlers:
        return logger

    # Create console handler with structured format
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(getattr(logging, log_level, logging.INFO))

    # Format: timestamp - level - module - message
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)

    logger.addHandler(handler)

    return logger


# Default logger instance
logger = setup_logger()
