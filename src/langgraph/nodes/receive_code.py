"""
Phase 5: Receive Code Node.

Accepts code uploaded by user after they manually create designs in Google AI Studio.
This node waits for code upload and prepares it for validation.
"""

from src.langgraph.state import DesignAgentState
from src.utils.logger import get_logger

logger = get_logger(__name__)


async def receive_code(state: DesignAgentState) -> DesignAgentState:
    """
    Phase 5: Receive uploaded code from user.

    This node:
    1. Waits for user to upload code via WebSocket/API
    2. Stores uploaded code and metadata in state
    3. Un-pauses the job to proceed to validation
    4. Updates progress to 80%

    Args:
        state: Current workflow state (should be paused)

    Returns:
        Updated state with uploaded_code
    """
    logger.info("Phase 5: Waiting for code upload", job_id=state.get("job_id"))

    try:
        uploaded_code = state.get("uploaded_code")
        uploaded_code_metadata = state.get("uploaded_code_metadata", {})

        # If no code uploaded yet, remain paused
        if not uploaded_code:
            logger.info("No code uploaded yet, remaining in pause state")
            return {
                **state,
                "paused": True,
                "phase_name": "Waiting for Design Code Upload",
                "progress_percent": 77.0,
            }

        # Code received, unpause and proceed to validation
        logger.info(
            "Code uploaded successfully",
            file_count=len(uploaded_code_metadata.get("files", [])),
            total_size=uploaded_code_metadata.get("total_size_bytes", 0),
        )

        return {
            **state,
            "paused": False,
            "uploaded_code": uploaded_code,
            "uploaded_code_metadata": uploaded_code_metadata,
            "phase_name": "Code Received - Ready for Validation",
            "progress_percent": 80.0,
        }

    except Exception as e:
        logger.error("Error receiving code", error=str(e), job_id=state.get("job_id"))

        errors = state.get("errors", [])
        errors.append(f"Code upload failed: {str(e)}")

        return {
            **state,
            "errors": errors,
            "should_retry": True,
            "retry_count": state.get("retry_count", 0) + 1,
        }


def has_code_been_uploaded(state: DesignAgentState) -> str:
    """
    Conditional routing function for receive_code node.

    Returns:
        - "code_uploaded" if code has been uploaded
        - "waiting" if still waiting for upload
    """
    if state.get("uploaded_code"):
        logger.info("Code upload detected, proceeding to validation")
        return "code_uploaded"
    else:
        logger.debug("Still waiting for code upload")
        return "waiting"


__all__ = ["receive_code", "has_code_been_uploaded"]
