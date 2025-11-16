"""
LangGraph workflow for Design Agent.

Defines the 6-phase state machine for design automation.
Week 2: Phases 1-2 (Screen extraction, Layout options)
"""

from langgraph.graph import StateGraph, END

from src.langgraph.checkpointer import get_checkpointer
from src.langgraph.nodes.extract_screens import extract_screens
from src.langgraph.nodes.generate_options import generate_options
from src.langgraph.nodes.create_ascii_ui import create_ascii_ui
from src.langgraph.nodes.refine_design import refine_design, should_continue_refining
from src.langgraph.nodes.generate_design_system import generate_design_system
from src.langgraph.nodes.pause_for_google_ai import pause_for_google_ai, should_pause_or_continue
from src.langgraph.nodes.receive_code import receive_code, has_code_been_uploaded
from src.langgraph.nodes.validate_code import (
    validate_code,
    should_proceed_after_validation,
    handle_validation_failure,
)
from src.langgraph.nodes.generate_documents import generate_documents
from src.langgraph.nodes.package_for_dev import package_for_dev
from src.langgraph.state import DesignAgentState
from src.utils.logger import get_logger
from src.workers.progress_updater import update_progress_from_state

logger = get_logger(__name__)


# ============================================================================
# Node Wrappers with Real-Time Progress Updates
# ============================================================================


async def extract_screens_with_progress(state: DesignAgentState) -> DesignAgentState:
    """
    Wrapper for extract_screens that updates progress in real-time.

    This allows ANYON to see Phase 1 completion separately.
    """
    result = await extract_screens(state)
    # Update progress in database immediately after Phase 1
    await update_progress_from_state(result["job_id"], result)
    return result


async def generate_options_with_progress(state: DesignAgentState) -> DesignAgentState:
    """
    Wrapper for generate_options that updates progress in real-time.

    This allows ANYON to see Phase 2 completion separately.
    """
    result = await generate_options(state)
    # Update progress in database immediately after Phase 2
    await update_progress_from_state(result["job_id"], result)
    return result


async def create_ascii_ui_with_progress(state: DesignAgentState) -> DesignAgentState:
    """
    Wrapper for create_ascii_ui that updates progress in real-time.

    This allows ANYON to see Phase 3 initial creation separately.
    """
    result = await create_ascii_ui(state)
    # Update progress in database immediately after initial ASCII UI creation
    await update_progress_from_state(result["job_id"], result)
    return result


async def refine_design_with_progress(state: DesignAgentState) -> DesignAgentState:
    """
    Wrapper for refine_design that updates progress in real-time.

    This allows ANYON to see refinement progress as each screen is approved.
    """
    result = await refine_design(state)
    # Update progress in database after each refinement iteration
    await update_progress_from_state(result["job_id"], result)
    return result


async def generate_design_system_with_progress(state: DesignAgentState) -> DesignAgentState:
    """
    Wrapper for generate_design_system that updates progress in real-time.

    This allows ANYON to see Phase 4 completion separately.
    """
    result = await generate_design_system(state)
    # Update progress in database immediately after Phase 4
    await update_progress_from_state(result["job_id"], result)
    return result


async def pause_for_google_ai_with_progress(state: DesignAgentState) -> DesignAgentState:
    """
    Wrapper for pause_for_google_ai that updates progress in real-time.

    This allows ANYON to see pause decision point.
    """
    result = await pause_for_google_ai(state)
    # Update progress in database after user choice
    await update_progress_from_state(result["job_id"], result)
    return result


async def receive_code_with_progress(state: DesignAgentState) -> DesignAgentState:
    """
    Wrapper for receive_code that updates progress in real-time.

    This allows ANYON to see code upload status.
    """
    result = await receive_code(state)
    # Update progress in database when code is received
    await update_progress_from_state(result["job_id"], result)
    return result


async def validate_code_with_progress(state: DesignAgentState) -> DesignAgentState:
    """
    Wrapper for validate_code that updates progress in real-time.

    This allows ANYON to see Phase 5 validation completion.
    """
    result = await validate_code(state)
    # Update progress in database after validation
    await update_progress_from_state(result["job_id"], result)
    return result


async def handle_validation_failure_with_progress(state: DesignAgentState) -> DesignAgentState:
    """
    Wrapper for handle_validation_failure that updates progress in real-time.

    This allows ANYON to see validation failure status.
    """
    result = await handle_validation_failure(state)
    # Update progress in database with failure feedback
    await update_progress_from_state(result["job_id"], result)
    return result


async def generate_documents_with_progress(state: DesignAgentState) -> DesignAgentState:
    """
    Wrapper for generate_documents that updates progress in real-time.

    Week 6: Phase 6 document generation with progress tracking.
    """
    result = await generate_documents(state)
    # Update progress in database after document generation
    await update_progress_from_state(result["job_id"], result)
    return result


async def package_for_dev_with_progress(state: DesignAgentState) -> DesignAgentState:
    """
    Wrapper for package_for_dev that updates progress in real-time.

    Week 6: Final packaging with ANYON integration.
    """
    result = await package_for_dev(state)
    # Update progress in database after packaging
    await update_progress_from_state(result["job_id"], result)
    return result


def create_workflow() -> StateGraph:
    """
    Create the Design Agent LangGraph workflow.

    Current implementation (Week 2): Phases 1-2
    - Phase 1: Screen extraction
    - Phase 2: Layout options generation

    Future (Weeks 3-6): Phases 3-6
    - Phase 3: ASCII UI creation and refinement
    - Phase 4: Design System extraction
    - Phase 5: Optional pause/resume with validation
    - Phase 6: Document generation

    Returns:
        Compiled StateGraph with checkpointer
    """
    logger.info("Creating Design Agent workflow")

    # Create state graph
    workflow = StateGraph(DesignAgentState)

    # ========================================================================
    # Phase 1: Screen Extraction (with real-time progress)
    # ========================================================================
    workflow.add_node("extract_screens", extract_screens_with_progress)

    # ========================================================================
    # Phase 2: Layout Options (with real-time progress)
    # ========================================================================
    workflow.add_node("generate_options", generate_options_with_progress)

    # ========================================================================
    # Phase 3: ASCII UI Creation & Refinement (with real-time progress)
    # ========================================================================
    workflow.add_node("create_ascii_ui", create_ascii_ui_with_progress)
    workflow.add_node("refine_design", refine_design_with_progress)

    # ========================================================================
    # Week 4: Open-Source Discovery (integrated into Phase 3)
    # ========================================================================
    # Triggered during refine_design when keywords detected (already implemented)

    # ========================================================================
    # Week 5: Phase 4 - Design System Extraction
    # ========================================================================
    workflow.add_node("generate_design_system", generate_design_system_with_progress)

    # ========================================================================
    # Week 5: Phase 5 - Optional Pause/Resume & Validation
    # ========================================================================
    workflow.add_node("pause_for_google_ai", pause_for_google_ai_with_progress)
    workflow.add_node("receive_code", receive_code_with_progress)
    workflow.add_node("validate_code", validate_code_with_progress)
    workflow.add_node("handle_validation_failure", handle_validation_failure_with_progress)

    # ========================================================================
    # Week 6: Phase 6 - Document Generation & Packaging
    # ========================================================================
    workflow.add_node("generate_documents", generate_documents_with_progress)
    workflow.add_node("package_for_dev", package_for_dev_with_progress)

    # ========================================================================
    # Error Handling
    # ========================================================================
    # TODO: Add general error_handler node

    # ========================================================================
    # Define Edges (Week 5: Complete flow Phases 1-5 with pause/resume)
    # ========================================================================

    # Set entry point
    workflow.set_entry_point("extract_screens")

    # Phase 1 → Phase 2
    workflow.add_edge("extract_screens", "generate_options")

    # Phase 2 → Phase 3 (initial ASCII UI creation)
    workflow.add_edge("generate_options", "create_ascii_ui")

    # Phase 3: Initial creation → Refinement loop
    workflow.add_edge("create_ascii_ui", "refine_design")

    # Phase 3: Refinement loop with conditional edge
    workflow.add_conditional_edges(
        "refine_design",
        should_continue_refining,
        {
            "continue": "refine_design",  # Loop: continue refining current/next screen
            "complete": "generate_design_system",  # All screens approved → Phase 4
            "waiting": END,  # Paused: awaiting user input (resume with user_feedback)
        },
    )

    # Phase 4: Design System extraction → Ask user about pause
    workflow.add_edge("generate_design_system", "pause_for_google_ai")

    # Phase 4.5: Pause decision point (conditional)
    workflow.add_conditional_edges(
        "pause_for_google_ai",
        should_pause_or_continue,
        {
            "wait_for_choice": END,  # Paused, awaiting user choice (resume later)
            "pause": "receive_code",  # User chose pause → wait for code upload
            "skip_to_phase6": "generate_documents",  # User chose skip → directly to Phase 6
        },
    )

    # Phase 5: Code upload (conditional)
    workflow.add_conditional_edges(
        "receive_code",
        has_code_been_uploaded,
        {
            "waiting": END,  # Still waiting for code upload (resume later)
            "code_uploaded": "validate_code",  # Code received → validate
        },
    )

    # Phase 5: Code validation (conditional)
    workflow.add_conditional_edges(
        "validate_code",
        should_proceed_after_validation,
        {
            "validation_passed": "generate_documents",  # Score ≥ 90/100 → Phase 6
            "validation_failed": "handle_validation_failure",  # Score < 90 → feedback
            "retry": "validate_code",  # Validation error → retry
        },
    )

    # Phase 5: Validation failure handling
    workflow.add_edge("handle_validation_failure", END)  # Awaiting user fix/override

    # ========================================================================
    # Week 6: Phase 6 Edges - Document Generation & Packaging
    # ========================================================================

    # Phase 6: Document generation → Packaging
    workflow.add_edge("generate_documents", "package_for_dev")

    # Phase 6: Packaging → Complete (END)
    workflow.add_edge("package_for_dev", END)

    logger.info("Workflow graph created (Week 6: Complete Phases 1-6 with ANYON integration)")

    return workflow


def compile_workflow() -> StateGraph:
    """
    Compile the workflow with PostgreSQL checkpointer.

    Returns:
        Compiled workflow ready for execution
    """
    workflow = create_workflow()

    # Get PostgreSQL checkpointer
    checkpointer = get_checkpointer()

    # Compile with checkpointer
    compiled = workflow.compile(checkpointer=checkpointer)

    logger.info("Workflow compiled with PostgreSQL checkpointer")

    return compiled


# Export for easy import
__all__ = ["create_workflow", "compile_workflow"]
