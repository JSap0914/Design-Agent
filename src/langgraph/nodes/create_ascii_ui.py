"""
Phase 3: ASCII UI Creation Node.

Creates initial ASCII mockups for all screens based on selected layout options.
"""

from src.langgraph.state import DesignAgentState, DesignDecision
from src.llm.client import llm_client
from src.llm.prompts import format_create_ascii_ui_prompt
from src.workers.progress_updater import broadcast_ascii_ui_update
from src.generators.ascii_ui import ASCIIUIGenerator
from src.utils.logger import get_logger

logger = get_logger(__name__)


async def create_ascii_ui(state: DesignAgentState) -> DesignAgentState:
    """
    Phase 3: Create initial ASCII UI mockups for all screens.

    This node:
    1. For each screen, takes the first layout option (default)
    2. Generates ASCII mockup using Claude
    3. Validates mockup dimensions (40 or 80 chars wide)
    4. Stores in selected_designs for refinement

    Args:
        state: Current workflow state

    Returns:
        Updated state with selected_designs
    """
    logger.info("Phase 3: Starting ASCII UI creation", job_id=state.get("job_id"))

    try:
        extracted_screens = state["extracted_screens"]
        design_options_metadata = state["design_options_metadata"]
        trd_content = state["trd_content"]

        # Determine platform from TRD
        platform = "mobile" if "mobile" in trd_content.lower() else "web"

        selected_designs: dict[str, str] = {}
        design_decisions: list[DesignDecision] = state.get("design_decisions", [])

        # Create ASCII UI for each screen
        for i, screen_name in enumerate(extracted_screens):
            logger.info(
                f"Creating ASCII UI for screen {i+1}/{len(extracted_screens)}",
                screen_name=screen_name,
            )

            # Get first layout option (default selection)
            options = design_options_metadata.get(screen_name, [])
            if not options:
                logger.warning(f"No layout options found for {screen_name}, skipping")
                continue

            selected_option = options[0]  # Use first option by default
            layout_description = selected_option["layout_description"]

            # Format prompt for ASCII UI generation
            system_prompt, user_prompt = format_create_ascii_ui_prompt(
                screen_name=screen_name,
                selected_option=1,
                layout_description=layout_description,
                platform=platform,
            )

            # Call LLM to generate ASCII UI
            ascii_ui = await llm_client.complete(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.5,  # Medium temperature for creativity with consistency
            )

            # Clean up response (remove markdown code blocks if present)
            if "```" in ascii_ui:
                # Extract content between code blocks
                start = ascii_ui.find("```") + 3
                if ascii_ui[start:].startswith("ascii") or ascii_ui[start:].startswith("text"):
                    start = ascii_ui.find("\n", start) + 1
                end = ascii_ui.rfind("```")
                ascii_ui = ascii_ui[start:end].strip()

            # Validate ASCII UI using ASCIIUIGenerator
            generator = ASCIIUIGenerator(platform=platform)
            is_valid, errors = generator.validate_ascii_ui(ascii_ui)

            if not is_valid:
                logger.warning(
                    f"LLM-generated ASCII UI failed validation for {screen_name}",
                    errors=errors,
                )
                # Log validation errors but continue (LLM output is best effort)
                # In production, could retry or use fallback

            # Store ASCII UI
            selected_designs[screen_name] = ascii_ui

            # Broadcast ASCII UI update via WebSocket (if available)
            await broadcast_ascii_ui_update(
                job_id=state.get("job_id", ""), screen_name=screen_name, ascii_ui=ascii_ui
            )

            # Record design decision
            decision: DesignDecision = {
                "screen_name": screen_name,
                "decision_type": "initial_layout",
                "rationale": f"Selected Option 1: {selected_option.get('layout_description', 'N/A')}",
                "alternatives": [
                    f"Option {opt['option_number']}: {opt.get('layout_description', 'N/A')}"
                    for opt in options
                ],
                "user_feedback": None,
            }
            design_decisions.append(decision)

            logger.info(
                f"ASCII UI created for {screen_name}",
                platform=platform,
                length=len(ascii_ui),
            )

        # Calculate progress
        total_screens = len(extracted_screens)
        completed_screens = len(selected_designs)
        progress_percent = 35.0 + (15.0 * (completed_screens / total_screens))  # 35% + up to 15% = 50%

        logger.info(
            "ASCII UI creation completed",
            total_screens=total_screens,
            completed_screens=completed_screens,
        )

        # Update state
        return {
            **state,
            "selected_designs": selected_designs,
            "design_decisions": design_decisions,
            "completed_screens": completed_screens,
            "current_phase": 3,
            "phase_name": "ASCII UI Created (Ready for Refinement)",
            "progress_percent": progress_percent,
        }

    except Exception as e:
        logger.error("Error in ASCII UI creation", error=str(e), job_id=state.get("job_id"))

        # Update state with error
        errors = state.get("errors", [])
        errors.append(f"ASCII UI creation failed: {str(e)}")

        return {
            **state,
            "errors": errors,
            "should_retry": True,
            "retry_count": state.get("retry_count", 0) + 1,
        }


# Export for easy import
__all__ = ["create_ascii_ui"]
