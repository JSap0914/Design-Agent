"""
Phase 1: Screen Extraction Node.

Analyzes PRD and TRD to extract complete list of screens needed.
"""

from src.config import settings
from src.langgraph.state import DesignAgentState
from src.llm.client import llm_client
from src.llm.prompts import format_extract_screens_prompt
from src.utils.logger import get_logger

logger = get_logger(__name__)


async def extract_screens(state: DesignAgentState) -> DesignAgentState:
    """
    Phase 1: Extract screens from PRD and TRD.

    This node:
    1. Analyzes PRD and TRD content
    2. Uses Claude Sonnet 4.5 to identify all required screens
    3. Validates screen count (3-12 screens)
    4. Updates state with extracted screens

    Args:
        state: Current workflow state

    Returns:
        Updated state with extracted_screens and screen_count
    """
    logger.info("Phase 1: Starting screen extraction", job_id=state.get("job_id"))

    try:
        # Get PRD and TRD content
        prd_content = state["prd_content"]
        trd_content = state["trd_content"]

        # Format prompt
        system_prompt, user_prompt = format_extract_screens_prompt(prd_content, trd_content)

        # Call LLM
        logger.info("Calling LLM for screen extraction")
        response = await llm_client.complete_with_json(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.3,  # Lower temperature for more consistent extraction
        )

        # Extract screens from response
        extracted_screens = response.get("screens", [])
        rationale = response.get("rationale", "")

        # Validate screen count
        if len(extracted_screens) < settings.min_screens:
            logger.warning(
                f"Too few screens extracted ({len(extracted_screens)}), minimum is {settings.min_screens}"
            )
            # Add a generic screen if needed
            while len(extracted_screens) < settings.min_screens:
                extracted_screens.append(f"Additional Screen {len(extracted_screens) + 1}")

        if len(extracted_screens) > settings.max_screens:
            logger.warning(
                f"Too many screens extracted ({len(extracted_screens)}), limiting to {settings.max_screens}"
            )
            extracted_screens = extracted_screens[: settings.max_screens]

        logger.info(
            "Screen extraction completed",
            screen_count=len(extracted_screens),
            screens=extracted_screens,
            rationale=rationale,
        )

        # Update state
        return {
            **state,
            "extracted_screens": extracted_screens,
            "screen_count": len(extracted_screens),
            "current_phase": 1,
            "phase_name": "Screen Extraction Complete",
            "progress_percent": 15.0,  # Phase 1 complete = ~15%
        }

    except Exception as e:
        logger.error("Error in screen extraction", error=str(e), job_id=state.get("job_id"))

        # Update state with error
        errors = state.get("errors", [])
        errors.append(f"Screen extraction failed: {str(e)}")

        return {
            **state,
            "errors": errors,
            "should_retry": True,
            "retry_count": state.get("retry_count", 0) + 1,
        }


# Export for easy import
__all__ = ["extract_screens"]
