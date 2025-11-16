"""
Phase 2: Layout Options Generation Node.

Generates 2-3 layout options for each screen following BMAD methodology.
"""

from src.config import settings
from src.langgraph.state import DesignAgentState
from src.llm.client import llm_client
from src.llm.prompts import format_generate_options_prompt
from src.utils.logger import get_logger

logger = get_logger(__name__)


async def generate_options(state: DesignAgentState) -> DesignAgentState:
    """
    Phase 2: Generate layout options for all screens.

    This node:
    1. Iterates through all extracted screens
    2. For each screen, generates 2-3 layout options using Claude
    3. Follows BMAD principle: ALWAYS provide multiple options
    4. Updates state with design_options

    Args:
        state: Current workflow state

    Returns:
        Updated state with design_options and metadata
    """
    logger.info("Phase 2: Starting layout options generation", job_id=state.get("job_id"))

    try:
        extracted_screens = state["extracted_screens"]
        prd_content = state["prd_content"]
        trd_content = state["trd_content"]

        design_options: dict[str, list[str]] = {}
        design_options_metadata: dict[str, list[dict]] = {}

        # Generate options for each screen
        for i, screen_name in enumerate(extracted_screens):
            logger.info(
                f"Generating options for screen {i+1}/{len(extracted_screens)}",
                screen_name=screen_name,
            )

            # Format prompt
            system_prompt, user_prompt = format_generate_options_prompt(
                screen_name=screen_name,
                prd_content=prd_content,
                trd_content=trd_content,
                all_screens=extracted_screens,
            )

            # Call LLM
            response = await llm_client.complete_with_json(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.7,  # Higher temperature for creative variety
            )

            # Extract options
            options = response.get("options", [])

            # Validate: must have 2-3 options (BMAD principle)
            if len(options) < settings.min_layout_options:
                logger.warning(
                    f"Only {len(options)} options generated, minimum is {settings.min_layout_options}"
                )
                # This violates BMAD - retry or add generic option
                if len(options) < settings.min_layout_options:
                    # Add a simple option
                    options.append(
                        {
                            "option_number": len(options) + 1,
                            "layout_description": "Standard layout with top navigation",
                            "key_features": ["Header", "Main content", "Footer"],
                            "pros": ["Familiar pattern"],
                            "cons": ["Less innovative"],
                            "recommended": False,
                        }
                    )

            if len(options) > settings.max_layout_options:
                logger.warning(
                    f"{len(options)} options generated, limiting to {settings.max_layout_options}"
                )
                options = options[: settings.max_layout_options]

            # Store options (simplified for now - just descriptions)
            option_descriptions = [
                f"Option {opt['option_number']}: {opt['layout_description']}" for opt in options
            ]

            design_options[screen_name] = option_descriptions
            design_options_metadata[screen_name] = options

            logger.info(
                f"Generated {len(options)} options for screen",
                screen_name=screen_name,
                options_count=len(options),
            )

        # Calculate progress
        total_screens = len(extracted_screens)
        progress_percent = 15.0 + (20.0 / total_screens) * total_screens  # 15% + up to 20% = 35%

        logger.info(
            "Layout options generation completed",
            total_screens=total_screens,
            total_options=sum(len(opts) for opts in design_options.values()),
        )

        # Update state
        return {
            **state,
            "design_options": design_options,
            "design_options_metadata": design_options_metadata,
            "current_phase": 2,
            "phase_name": "Layout Options Generated",
            "progress_percent": progress_percent,
            "options_provided_count": sum(len(opts) for opts in design_options.values()),
        }

    except Exception as e:
        logger.error("Error in layout options generation", error=str(e), job_id=state.get("job_id"))

        # Update state with error
        errors = state.get("errors", [])
        errors.append(f"Layout options generation failed: {str(e)}")

        return {
            **state,
            "errors": errors,
            "should_retry": True,
            "retry_count": state.get("retry_count", 0) + 1,
        }


# Export for easy import
__all__ = ["generate_options"]
