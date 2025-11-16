"""
Real-time progress updater for Design Agent.

Updates the shared.design_progress table after each LangGraph node execution
so ANYON can track progress in real-time.

Also broadcasts WebSocket updates if FastAPI app is running.
"""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.connection import db_manager
from src.database.models import DesignProgress
from src.langgraph.state import DesignAgentState
from src.utils.logger import get_logger

logger = get_logger(__name__)

# WebSocket manager (optional - only if FastAPI app is running)
_websocket_manager = None


def set_websocket_manager(manager):
    """
    Set WebSocket manager for broadcasting updates.

    Called by FastAPI app on startup to enable real-time WebSocket updates.
    If not set, only database updates will occur (e.g., in CLI mode).
    """
    global _websocket_manager
    _websocket_manager = manager
    logger.info("WebSocket manager registered for progress broadcasting")


async def update_progress_from_state(job_id: str, state: DesignAgentState) -> None:
    """
    Update progress table from LangGraph state.

    This function is called after each node executes to provide real-time
    progress updates to ANYON.

    Args:
        job_id: Job ID (UUID as string)
        state: Current LangGraph state with progress information
    """
    try:
        job_uuid = uuid.UUID(job_id)

        async with db_manager.get_async_session() as session:
            # Extract progress from state
            values: dict[str, Any] = {
                "current_phase": state.get("current_phase", 0),
                "phase_name": state.get("phase_name", "Processing"),
                "progress_percent": state.get("progress_percent", 0.0),
                "screen_count": state.get("screen_count", 0),
                "completed_screens": state.get("completed_screens", 0),
                "last_updated": datetime.utcnow(),
            }

            # Update progress record
            await session.execute(
                update(DesignProgress).where(DesignProgress.job_id == job_uuid).values(**values)
            )
            await session.commit()

            logger.info(
                "Progress updated",
                job_id=job_id,
                phase=values["current_phase"],
                phase_name=values["phase_name"],
                progress=values["progress_percent"],
            )

            # Broadcast WebSocket update if manager is available
            if _websocket_manager:
                try:
                    await _websocket_manager.broadcast_progress(job_id, values)
                    logger.debug("WebSocket progress update broadcasted", job_id=job_id)
                except Exception as ws_error:
                    logger.warning("Failed to broadcast WebSocket update", error=str(ws_error))
                    # Don't fail the whole update if WebSocket broadcast fails

    except Exception as e:
        logger.error("Failed to update progress", job_id=job_id, error=str(e))
        # Don't raise - progress update failures shouldn't stop the workflow


async def broadcast_ascii_ui_update(job_id: str, screen_name: str, ascii_ui: str) -> None:
    """
    Broadcast ASCII UI update via WebSocket.

    Called by create_ascii_ui and refine_design nodes to show real-time UI updates.

    Args:
        job_id: Job ID (UUID as string)
        screen_name: Name of screen being updated
        ascii_ui: ASCII UI mockup content
    """
    if _websocket_manager:
        try:
            await _websocket_manager.broadcast_ascii_ui(job_id, screen_name, ascii_ui)
            logger.info(
                "ASCII UI update broadcasted via WebSocket",
                job_id=job_id,
                screen_name=screen_name,
                ascii_ui_length=len(ascii_ui),
            )
        except Exception as e:
            logger.warning("Failed to broadcast ASCII UI update", job_id=job_id, error=str(e))
            # Don't fail if WebSocket broadcast fails
    else:
        logger.debug("WebSocket manager not available, skipping ASCII UI broadcast")


# Export for easy import
__all__ = ["update_progress_from_state", "broadcast_ascii_ui_update", "set_websocket_manager"]
