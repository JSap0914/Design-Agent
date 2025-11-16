"""
Phase 3: ASCII UI Refinement Node.

Processes user feedback to iteratively refine ASCII mockups.
Supports conversational modifications like "move button to bottom", "add search bar".
Automatically detects library-related keywords and triggers open-source recommendations.
"""

from src.langgraph.state import DesignAgentState, DesignDecision
from src.llm.client import llm_client
from src.llm.prompts import format_refine_ascii_ui_prompt
from src.workers.progress_updater import broadcast_ascii_ui_update
from src.opensearch.keywords import should_trigger_library_search, extract_search_query, get_category_from_feedback
from src.opensearch.orchestrator import discover_libraries, handle_library_selection
from src.opensearch.selector import create_library_options_message
from src.opensearch.database import store_library_selection
from src.utils.logger import get_logger

logger = get_logger(__name__)


async def refine_design(state: DesignAgentState) -> DesignAgentState:
    """
    Phase 3: Refine ASCII UI based on user feedback.

    This node:
    1. Takes current ASCII UI for a screen
    2. Accepts user feedback (e.g., "move login button to bottom")
    3. Calls LLM to modify ASCII UI based on feedback
    4. Updates selected_designs with refined version
    5. Records feedback and rationale in design_decisions
    6. Sets refinement_complete flag when user approves

    Args:
        state: Current workflow state

    Returns:
        Updated state with refined designs
    """
    logger.info("Phase 3: Processing design refinement", job_id=state.get("job_id"))

    try:
        # Get current refinement context
        current_screen_index = state.get("current_screen_index", 0)
        extracted_screens = state["extracted_screens"]
        selected_designs = state.get("selected_designs", {})
        design_decisions = state.get("design_decisions", [])
        user_feedback = state.get("user_feedback")

        # Check if we're done with all screens
        if current_screen_index >= len(extracted_screens):
            logger.info("All screens refined and approved")
            return {
                **state,
                "refinement_complete": True,
                "phase_name": "All Designs Approved",
                "progress_percent": 65.0,
            }

        screen_name = extracted_screens[current_screen_index]
        current_ascii_ui = selected_designs.get(screen_name, "")

        logger.info(
            f"Refining screen {current_screen_index + 1}/{len(extracted_screens)}",
            screen_name=screen_name,
            has_feedback=bool(user_feedback),
        )

        # Determine platform
        platform = "mobile" if "mobile" in state["trd_content"].lower() else "web"

        # If no feedback, this is the first refinement pass (just created)
        # In production, we'd wait for user input via WebSocket
        # For Week 3, we simulate approval or one round of refinement
        if not user_feedback:
            logger.info(f"No feedback for {screen_name}, marking for user review")
            return {
                **state,
                "awaiting_feedback": True,
                "current_screen_name": screen_name,
                "phase_name": f"Review {screen_name}",
            }

        # ========================================================================
        # LIBRARY DISCOVERY INTEGRATION
        # ========================================================================

        # Check if we're awaiting library selection (user previously triggered search)
        awaiting_library_selection = state.get("awaiting_library_selection", False)
        pending_library_options = state.get("pending_library_options", [])

        if awaiting_library_selection and pending_library_options:
            # User is responding to library options (1, 2, 3, or skip)
            logger.info(f"Processing library selection", user_input=user_feedback)

            query = state.get("pending_library_query", "")
            category = state.get("pending_library_category", "ui_components")

            # Process selection
            selection_result = await handle_library_selection(
                user_input=user_feedback,
                libraries=pending_library_options,
                query=query,
                category=category,
            )

            # Update state with selection
            selected_open_source = state.get("selected_open_source", [])
            if selection_result["state_update"].get("selected_open_source"):
                recommendation = selection_result["state_update"]["selected_open_source"]
                selected_open_source.append(recommendation)

                # Store selection in database
                await store_library_selection(
                    job_id=state.get("job_id", ""),
                    category=recommendation.get("category", category),
                    library_name=recommendation.get("library_name", ""),
                    github_url=recommendation.get("github_url"),
                    npm_url=recommendation.get("npm_url"),
                    stars=recommendation.get("stars"),
                    license_type=recommendation.get("license"),
                    bundle_size=recommendation.get("bundle_size"),
                    version=recommendation.get("version"),
                    ranking_score=recommendation.get("ranking_score"),
                    rationale=recommendation.get("rationale", ""),
                    alternatives=recommendation.get("alternatives"),
                )

            # Broadcast selection result via WebSocket
            websocket_msg = selection_result["websocket_message"]
            # TODO: Broadcast websocket_msg to connected clients

            logger.info(
                f"Library selection processed and stored",
                selected=selection_result["selection_result"]["selected"],
                library=selection_result["selection_result"].get("library", {}).get("library_name"),
            )

            # Clear library selection state, continue with normal refinement
            return {
                **state,
                "selected_open_source": selected_open_source,
                "awaiting_library_selection": False,
                "pending_library_options": [],
                "pending_library_query": None,
                "pending_library_category": None,
                "user_feedback": None,
                "awaiting_feedback": True,
                "phase_name": f"Review {screen_name} (library selected)",
            }

        # Check if user feedback contains library keywords
        if should_trigger_library_search(user_feedback):
            logger.info(f"Library keywords detected in feedback", feedback=user_feedback)

            # Extract search query and category
            query = extract_search_query(user_feedback)
            category = get_category_from_feedback(user_feedback)

            logger.info(f"Triggering library search", query=query, category=category)

            # Discover libraries
            discovery_result = await discover_libraries(
                query=query,
                category=category,
                language="typescript",
                min_stars=500,
                max_days_since_update=365,
                require_typescript=True,
                tech_stack=None,  # TODO: Extract from TRD
                max_options=3,
            )

            if discovery_result["success"] and discovery_result["libraries"]:
                # Found libraries, present options to user
                libraries = discovery_result["libraries"]
                formatted_text = discovery_result["formatted_text"]

                logger.info(
                    f"Library options found",
                    query=query,
                    count=len(libraries),
                    top_score=libraries[0].get("ranking_score") if libraries else 0,
                )

                # Create WebSocket message
                websocket_msg = create_library_options_message(query, libraries, formatted_text)
                # TODO: Broadcast websocket_msg to connected clients

                # Update state to await library selection
                return {
                    **state,
                    "awaiting_library_selection": True,
                    "pending_library_options": libraries,
                    "pending_library_query": query,
                    "pending_library_category": category,
                    "user_feedback": None,
                    "phase_name": f"Library selection: {query}",
                }
            else:
                # No libraries found or search failed
                logger.warning(
                    f"Library search failed or returned no results",
                    query=query,
                    error=discovery_result.get("error"),
                )

                # Continue with normal ASCII refinement
                # (User feedback still contains the original refinement request)

        # ========================================================================
        # END LIBRARY DISCOVERY INTEGRATION
        # ========================================================================

        # Process feedback
        if user_feedback.lower() in ["approve", "approved", "looks good", "next"]:
            # User approved this screen, move to next
            logger.info(f"Screen approved: {screen_name}")

            # Record approval decision
            decision: DesignDecision = {
                "screen_name": screen_name,
                "decision_type": "approval",
                "rationale": "User approved design without changes",
                "alternatives": [],
                "user_feedback": user_feedback,
            }
            design_decisions.append(decision)

            # Calculate progress (Phase 3 is 50-65%)
            completed_screens = current_screen_index + 1
            total_screens = len(extracted_screens)
            progress_percent = 50.0 + (15.0 * (completed_screens / total_screens))

            return {
                **state,
                "design_decisions": design_decisions,
                "current_screen_index": current_screen_index + 1,
                "completed_screens": completed_screens,
                "user_feedback": None,
                "awaiting_feedback": False,
                "progress_percent": progress_percent,
                "phase_name": f"Refined {completed_screens}/{total_screens} screens",
            }

        # User provided refinement feedback
        logger.info(f"Processing refinement feedback for {screen_name}", feedback=user_feedback)

        # Format prompt for refinement
        system_prompt, user_prompt = format_refine_ascii_ui_prompt(
            screen_name=screen_name,
            current_ascii_ui=current_ascii_ui,
            user_feedback=user_feedback,
            platform=platform,
        )

        # Call LLM to refine ASCII UI
        refined_ascii_ui = await llm_client.complete(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.5,  # Medium temperature for consistency
        )

        # Clean up response (remove markdown code blocks if present)
        if "```" in refined_ascii_ui:
            start = refined_ascii_ui.find("```") + 3
            if refined_ascii_ui[start:].startswith("ascii") or refined_ascii_ui[start:].startswith(
                "text"
            ):
                start = refined_ascii_ui.find("\n", start) + 1
            end = refined_ascii_ui.rfind("```")
            refined_ascii_ui = refined_ascii_ui[start:end].strip()

        # Update selected designs
        selected_designs[screen_name] = refined_ascii_ui

        # Broadcast refined ASCII UI via WebSocket (if available)
        await broadcast_ascii_ui_update(
            job_id=state.get("job_id", ""), screen_name=screen_name, ascii_ui=refined_ascii_ui
        )

        # Record refinement decision
        decision: DesignDecision = {
            "screen_name": screen_name,
            "decision_type": "refinement",
            "rationale": f"Modified based on user feedback: {user_feedback}",
            "alternatives": [f"Previous version:\n{current_ascii_ui[:100]}..."],
            "user_feedback": user_feedback,
        }
        design_decisions.append(decision)

        logger.info(
            f"ASCII UI refined for {screen_name}",
            feedback=user_feedback,
            refined_length=len(refined_ascii_ui),
        )

        # Return state with refined design, waiting for next feedback
        return {
            **state,
            "selected_designs": selected_designs,
            "design_decisions": design_decisions,
            "user_feedback": None,
            "awaiting_feedback": True,
            "current_screen_name": screen_name,
            "phase_name": f"Review {screen_name} (updated)",
        }

    except Exception as e:
        logger.error("Error in design refinement", error=str(e), job_id=state.get("job_id"))

        # Update state with error
        errors = state.get("errors", [])
        errors.append(f"Design refinement failed: {str(e)}")

        return {
            **state,
            "errors": errors,
            "should_retry": True,
            "retry_count": state.get("retry_count", 0) + 1,
        }


def should_continue_refining(state: DesignAgentState) -> str:
    """
    Conditional edge function: determine if refinement should continue.

    Returns:
        - "continue": Continue refining current or next screen
        - "complete": All screens approved, move to Phase 4
        - "waiting": Paused, awaiting user input (feedback or library selection)
    """
    refinement_complete = state.get("refinement_complete", False)
    current_screen_index = state.get("current_screen_index", 0)
    total_screens = len(state.get("extracted_screens", []))
    awaiting_feedback = state.get("awaiting_feedback", False)
    awaiting_library = state.get("awaiting_library_selection", False)

    if refinement_complete or current_screen_index >= total_screens:
        logger.info("Refinement complete, proceeding to Phase 4")
        return "complete"
    elif awaiting_feedback or awaiting_library:
        logger.info(
            f"Waiting for user input: screen {current_screen_index + 1}/{total_screens}",
            awaiting_feedback=awaiting_feedback,
            awaiting_library=awaiting_library,
        )
        return "waiting"
    else:
        logger.info(
            f"Continue refinement: screen {current_screen_index + 1}/{total_screens}",
        )
        return "continue"


# Export for easy import
__all__ = ["refine_design", "should_continue_refining"]
