"""
Phase 4 Optional: Pause for Google AI Studio Node.

After Design System extraction, asks user if they want to:
- Option A: Pause and use Google AI Studio to create actual designs (manual)
- Option B: Skip directly to Phase 6 (document generation)
"""

from src.langgraph.state import DesignAgentState
from src.utils.logger import get_logger

logger = get_logger(__name__)


async def pause_for_google_ai(state: DesignAgentState) -> DesignAgentState:
    """
    Phase 4 Optional: Ask user if they want to pause for Google AI Studio.

    This node:
    1. Checks if user has already made a choice
    2. If not, sets awaiting_feedback flag for user to respond
    3. User can choose:
       - "pause" → Sets paused=True, job status="paused_waiting_for_upload"
       - "skip" → Proceeds directly to Phase 6 (document generation)

    Args:
        state: Current workflow state

    Returns:
        Updated state with pause choice or awaiting feedback
    """
    logger.info("Phase 4: Asking user about Google AI Studio pause", job_id=state.get("job_id"))

    try:
        user_feedback = state.get("user_feedback")

        # If no feedback yet, wait for user choice
        if not user_feedback:
            logger.info("Waiting for user choice: pause or skip to documents")
            return {
                **state,
                "awaiting_feedback": True,
                "phase_name": "Choose: Pause for Google AI Studio or Skip to Documents",
                "progress_percent": 72.0,
            }

        # Process user choice
        user_choice = user_feedback.lower().strip()

        if user_choice in ["pause", "pause_for_google_ai", "use google ai", "manual design"]:
            # User wants to pause for manual design work
            logger.info("User chose to pause for Google AI Studio")

            return {
                **state,
                "should_pause_for_google_ai": True,
                "paused": True,
                "user_feedback": None,
                "awaiting_feedback": False,
                "phase_name": "Paused - Waiting for Design Upload",
                "progress_percent": 75.0,
            }

        elif user_choice in ["skip", "skip to documents", "no pause", "continue", "auto"]:
            # User wants to skip directly to document generation
            logger.info("User chose to skip Google AI Studio pause")

            return {
                **state,
                "should_pause_for_google_ai": False,
                "paused": False,
                "uploaded_code": None,
                "validation_results": None,
                "user_feedback": None,
                "awaiting_feedback": False,
                "phase_name": "Skipping to Document Generation",
                "progress_percent": 75.0,
            }

        else:
            # Invalid choice, ask again
            logger.warning(f"Invalid choice from user: {user_choice}")
            return {
                **state,
                "awaiting_feedback": True,
                "user_feedback": None,
                "phase_name": "Invalid choice - Please choose: pause or skip",
            }

    except Exception as e:
        logger.error("Error in pause_for_google_ai node", error=str(e), job_id=state.get("job_id"))

        errors = state.get("errors", [])
        errors.append(f"Pause choice failed: {str(e)}")

        return {
            **state,
            "errors": errors,
            "should_retry": True,
            "retry_count": state.get("retry_count", 0) + 1,
        }


def should_pause_or_continue(state: DesignAgentState) -> str:
    """
    Conditional routing function for pause_for_google_ai node.

    Returns:
        - "pause" if user chose to pause for Google AI Studio
        - "skip_to_phase6" if user chose to skip directly to documents
        - "wait_for_choice" if still waiting for user feedback
    """
    # Check if waiting for user choice
    if state.get("awaiting_feedback") and not state.get("user_feedback"):
        logger.debug("Waiting for user to choose pause or skip")
        return "wait_for_choice"

    # Check if user chose to pause
    if state.get("should_pause_for_google_ai") and state.get("paused"):
        logger.info("Routing to pause (waiting for code upload)")
        return "pause"

    # User chose to skip
    logger.info("Routing to skip (directly to Phase 6)")
    return "skip_to_phase6"


__all__ = ["pause_for_google_ai", "should_pause_or_continue"]
