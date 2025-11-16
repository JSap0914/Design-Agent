"""
Structured logging configuration for Design Agent.

Uses structlog for structured, context-rich logging.
"""

import logging
import sys
from typing import Any

import structlog
from structlog.types import Processor

from src.config import settings


def get_logger(name: str) -> structlog.BoundLogger:
    """
    Get a structured logger instance.

    Args:
        name: Logger name (usually __name__)

    Returns:
        structlog.BoundLogger: Structured logger instance
    """
    return structlog.get_logger(name)


def configure_logging() -> None:
    """
    Configure global logging settings.

    Sets up structlog with appropriate processors for the environment.
    """
    # Determine if we should use colored output
    use_colors = settings.is_development and sys.stderr.isatty()

    # Configure structlog processors
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]

    if settings.is_development:
        # Development: Human-readable console output
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(colors=use_colors)
            if use_colors
            else structlog.processors.JSONRenderer()
        ]
    else:
        # Production: JSON output for log aggregation
        processors = shared_processors + [
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ]

    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelName(settings.log_level)
        ),
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.getLevelName(settings.log_level),
    )

    # Silence noisy loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("asyncpg").setLevel(logging.WARNING)


# Export for easy import
__all__ = ["get_logger", "configure_logging"]
