"""
Checkpointer for LangGraph.

Enables pause/resume functionality for the Design Agent workflow.
Uses MemorySaver for development/testing, PostgresSaver for production.
"""

try:
    from langgraph.checkpoint.postgres import PostgresSaver

    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False
    PostgresSaver = None  # type: ignore

from langgraph.checkpoint.memory import MemorySaver

from src.config import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


def create_checkpointer():
    """
    Create checkpointer for LangGraph.

    Uses PostgreSQL checkpointer in production, MemorySaver for development/testing.

    Returns:
        PostgresSaver or MemorySaver: Configured checkpointer

    Raises:
        Exception: If checkpointer creation fails
    """
    try:
        if POSTGRES_AVAILABLE and hasattr(settings, "database_sync_url"):
            logger.info("Creating PostgreSQL checkpointer for LangGraph")

            # Create checkpointer from connection string
            # Use sync URL for LangGraph checkpointer
            checkpointer = PostgresSaver.from_conn_string(
                settings.database_sync_url,
            )

            logger.info("PostgreSQL checkpointer created successfully")
            return checkpointer
        else:
            logger.warning(
                "PostgreSQL checkpointer not available, using MemorySaver fallback "
                "(state will not persist across restarts)"
            )
            return MemorySaver()

    except Exception as e:
        logger.error("Failed to create PostgreSQL checkpointer, falling back to MemorySaver", error=str(e))
        return MemorySaver()


# Global checkpointer instance (created lazily)
_checkpointer = None


def get_checkpointer():
    """
    Get or create the global checkpointer instance.

    Returns:
        Checkpointer instance (PostgresSaver or MemorySaver)
    """
    global _checkpointer

    if _checkpointer is None:
        _checkpointer = create_checkpointer()

    return _checkpointer


# Export for easy import
__all__ = ["create_checkpointer", "get_checkpointer"]
