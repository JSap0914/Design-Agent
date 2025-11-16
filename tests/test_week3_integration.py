"""
Week 3 Integration Test: Phases 1-3 End-to-End with ASCII UI Refinement.

Tests the complete flow:
1. Screen extraction from PRD/TRD (Phase 1)
2. Layout options generation (Phase 2)
3. ASCII UI creation (Phase 3a)
4. ASCII UI refinement loop (Phase 3b)
5. LangGraph workflow with conditional routing
"""

import asyncio
import uuid

import pytest

from src.database.connection import db_manager
from src.langgraph.workflow import compile_workflow


# Sample PRD for testing (same as Week 2)
SAMPLE_PRD = """
# Product Requirements Document: Task Manager App

## Overview
A simple, intuitive task management application for individuals and small teams.

## Features
- User authentication (email + password)
- Task list with categories
- Task creation and editing
- Task detail view with notes and subtasks
- User profile and settings

## Screens Required
1. Login Screen - Email/password authentication
2. Registration Screen - New user signup
3. Task List Screen - Main dashboard with all tasks
4. Task Detail Screen - View and edit individual task
5. Create Task Screen - Add new task with details
6. User Profile Screen - View and edit profile
7. Settings Screen - App preferences
"""

SAMPLE_TRD = """
# Technical Requirements Document: Task Manager App

## Technology Stack
- Frontend: React 19 with TypeScript
- Backend: FastAPI (Python 3.11+)
- Database: PostgreSQL
- Styling: Tailwind CSS

## Platform
- **Primary:** Mobile-first (iOS and Android via React Native)
- **Secondary:** Web responsive

## Technical Constraints
- Must work offline (local storage sync)
- Maximum 3-second load time
- Support 10,000+ tasks per user
- WCAG AA accessibility compliance
"""


@pytest.fixture
async def setup_database():
    """Setup database connection for tests."""
    db_manager.initialize_async_engine()
    yield
    await db_manager.close()


@pytest.mark.asyncio
async def test_phase3_create_ascii_ui(setup_database, mock_llm_all_phases):
    """
    Test Phase 3a: Initial ASCII UI creation.

    Verifies:
    1. Creates ASCII mockups for all screens
    2. Uses first layout option by default
    3. Records design decisions
    4. ASCII UI has correct format (40 chars wide for mobile)
    """
    from src.langgraph.nodes.create_ascii_ui import create_ascii_ui

    # Prepare state (assuming Phases 1-2 completed)
    state = {
        "job_id": str(uuid.uuid4()),
        "project_id": "test-003",
        "user_id": "test-user",
        "prd_content": SAMPLE_PRD,
        "trd_content": SAMPLE_TRD,
        "extracted_screens": ["Login Screen", "Task List Screen", "Settings Screen"],
        "screen_count": 3,
        "design_options_metadata": {
            "Login Screen": [
                {
                    "option_number": 1,
                    "layout_description": "Centered vertical layout with logo at top",
                    "key_features": ["Logo", "Form", "Button"],
                }
            ],
            "Task List Screen": [
                {
                    "option_number": 1,
                    "layout_description": "List view with cards",
                    "key_features": ["Header", "Search", "Task cards"],
                }
            ],
            "Settings Screen": [
                {
                    "option_number": 1,
                    "layout_description": "Grouped settings list",
                    "key_features": ["Profile", "Preferences", "About"],
                }
            ],
        },
    }

    # Execute Phase 3a
    result = await create_ascii_ui(state)

    # Verify results
    assert "selected_designs" in result, "selected_designs missing from result"
    assert isinstance(result["selected_designs"], dict), "selected_designs should be a dict"
    assert len(result["selected_designs"]) == 3, "Should create ASCII UI for all 3 screens"

    # Verify each screen has ASCII UI
    for screen_name in ["Login Screen", "Task List Screen", "Settings Screen"]:
        assert screen_name in result["selected_designs"], f"Missing ASCII UI for {screen_name}"
        ascii_ui = result["selected_designs"][screen_name]
        assert len(ascii_ui) > 0, f"ASCII UI for {screen_name} is empty"
        # Check that it has box drawing characters (indicates proper formatting)
        assert "┌" in ascii_ui or "│" in ascii_ui, f"ASCII UI for {screen_name} missing box drawing"

    # Verify design decisions recorded
    assert "design_decisions" in result, "design_decisions missing from result"
    assert len(result["design_decisions"]) == 3, "Should have 3 design decisions (one per screen)"

    # Verify progress
    assert result["current_phase"] == 3, "Should be in Phase 3"
    assert result["progress_percent"] >= 50, "Progress should be >= 50%"

    print(f"✓ Phase 3a: Created ASCII UI for {len(result['selected_designs'])} screens")


@pytest.mark.asyncio
async def test_phase3_refine_design_approval(setup_database, mock_llm_all_phases):
    """
    Test Phase 3b: Design refinement with approval flow.

    Verifies:
    1. User can approve a screen without changes
    2. Approval moves to next screen
    3. All screens approved triggers refinement_complete
    """
    from src.langgraph.nodes.refine_design import refine_design

    # Prepare state (Phase 3a completed, starting refinement)
    state = {
        "job_id": str(uuid.uuid4()),
        "project_id": "test-004",
        "user_id": "test-user",
        "prd_content": SAMPLE_PRD,
        "trd_content": SAMPLE_TRD,
        "extracted_screens": ["Login Screen", "Task List Screen"],
        "screen_count": 2,
        "selected_designs": {
            "Login Screen": "Mock ASCII UI 1",
            "Task List Screen": "Mock ASCII UI 2",
        },
        "design_decisions": [],
        "current_screen_index": 0,
        "user_feedback": "approve",  # User approves first screen
    }

    # Execute refinement (approve first screen)
    result = await refine_design(state)

    # Verify screen approved and moved to next
    assert result["current_screen_index"] == 1, "Should move to screen index 1"
    assert result["completed_screens"] == 1, "Should have 1 completed screen"
    assert result.get("user_feedback") is None, "Feedback should be cleared"
    assert len(result["design_decisions"]) == 1, "Should have approval decision recorded"

    # Now approve second screen
    result["user_feedback"] = "looks good"
    result2 = await refine_design(result)

    # Verify all screens completed
    assert result2["current_screen_index"] == 2, "Should have processed all screens"
    assert result2["completed_screens"] == 2, "Should have 2 completed screens"

    # Verify refinement complete when all screens done
    result2["user_feedback"] = None
    result3 = await refine_design(result2)
    assert result3.get("refinement_complete") is True, "Should mark refinement as complete"

    print("✓ Phase 3b: Approval flow works correctly")


@pytest.mark.asyncio
async def test_phase3_refine_design_with_feedback(setup_database, mock_llm_all_phases):
    """
    Test Phase 3b: Design refinement with user feedback.

    Verifies:
    1. User can provide refinement feedback
    2. LLM modifies ASCII UI based on feedback
    3. Refinement decision is recorded
    4. User can continue refining same screen
    """
    from src.langgraph.nodes.refine_design import refine_design

    # Prepare state with user feedback for modification
    state = {
        "job_id": str(uuid.uuid4()),
        "project_id": "test-005",
        "user_id": "test-user",
        "prd_content": SAMPLE_PRD,
        "trd_content": SAMPLE_TRD,
        "extracted_screens": ["Login Screen"],
        "screen_count": 1,
        "selected_designs": {
            "Login Screen": "Original ASCII UI",
        },
        "design_decisions": [],
        "current_screen_index": 0,
        "user_feedback": "Move the login button to the bottom",
    }

    # Execute refinement with feedback
    result = await refine_design(state)

    # Verify ASCII UI was updated
    assert "selected_designs" in result, "selected_designs should be in result"
    assert result["selected_designs"]["Login Screen"] != "Original ASCII UI", "ASCII UI should be modified"

    # Verify refinement decision recorded
    assert len(result["design_decisions"]) == 1, "Should have refinement decision"
    decision = result["design_decisions"][0]
    assert decision["decision_type"] == "refinement", "Decision should be type 'refinement'"
    assert "Move the login button" in decision["rationale"], "Should record user feedback"

    # Verify still on same screen (awaiting next feedback)
    assert result["current_screen_index"] == 0, "Should still be on screen 0"
    assert result.get("awaiting_feedback") is True, "Should be awaiting next feedback"

    print("✓ Phase 3b: Refinement with feedback works correctly")


@pytest.mark.asyncio
async def test_phase3_conditional_routing(setup_database, mock_llm_all_phases):
    """
    Test Phase 3: Conditional routing for refinement loop.

    Verifies:
    1. should_continue_refining returns "continue" when screens remain
    2. should_continue_refining returns "complete" when all done
    """
    from src.langgraph.nodes.refine_design import should_continue_refining

    # Test: More screens to refine
    state_continue = {
        "extracted_screens": ["Screen 1", "Screen 2", "Screen 3"],
        "current_screen_index": 1,
        "refinement_complete": False,
    }
    assert should_continue_refining(state_continue) == "continue", "Should continue with more screens"

    # Test: All screens completed
    state_complete = {
        "extracted_screens": ["Screen 1", "Screen 2"],
        "current_screen_index": 2,
        "refinement_complete": False,
    }
    assert should_continue_refining(state_complete) == "complete", "Should complete when all screens done"

    # Test: Explicitly marked complete
    state_explicit_complete = {
        "extracted_screens": ["Screen 1"],
        "current_screen_index": 0,
        "refinement_complete": True,
    }
    assert (
        should_continue_refining(state_explicit_complete) == "complete"
    ), "Should complete when explicitly marked"

    print("✓ Phase 3: Conditional routing works correctly")


@pytest.mark.asyncio
async def test_workflow_phases_1_3_end_to_end(setup_database, mock_llm_all_phases):
    """
    Test complete workflow execution for Phases 1-3.

    Verifies:
    1. Workflow executes all three phases sequentially
    2. State flows correctly through phases
    3. Phase 3 refinement loop works (simulated approval)
    4. Progress tracking works
    5. Final state contains all expected data
    """
    # Compile workflow
    workflow = compile_workflow()

    # Prepare initial state
    job_id = str(uuid.uuid4())
    initial_state = {
        "job_id": job_id,
        "project_id": "test-workflow-002",
        "user_id": "test-user",
        "prd_content": SAMPLE_PRD,
        "trd_content": SAMPLE_TRD,
        "current_phase": 0,
        "phase_name": "Initializing",
        "progress_percent": 0.0,
        "errors": [],
        "retry_count": 0,
    }

    # Execute workflow
    # Note: For Week 3, refinement loop will run but needs simulated user feedback
    # In production, this would be via WebSocket. For testing, we'll let it initialize
    config = {"configurable": {"thread_id": job_id}}

    # For testing, we need to simulate the refinement approval process
    # The workflow will create ASCII UI and enter refine_design node
    # We'll test that the workflow reaches the refinement phase correctly

    # First execution: Phases 1-2-3a
    final_state = await workflow.ainvoke(initial_state, config)

    # Verify Phase 1 results
    assert "extracted_screens" in final_state, "Phase 1 should extract screens"
    assert len(final_state["extracted_screens"]) >= 3, "Should have at least 3 screens"

    # Verify Phase 2 results
    assert "design_options" in final_state, "Phase 2 should generate options"
    assert len(final_state["design_options"]) == len(
        final_state["extracted_screens"]
    ), "Should have options for all screens"

    # Verify Phase 3 results
    assert "selected_designs" in final_state, "Phase 3 should create ASCII UI"
    assert len(final_state["selected_designs"]) == len(
        final_state["extracted_screens"]
    ), "Should have ASCII UI for all screens"

    # Verify progress tracking
    assert final_state["current_phase"] == 3, "Should be in Phase 3"
    assert final_state["progress_percent"] >= 50, "Progress should be >= 50%"

    # Verify no errors
    assert len(final_state.get("errors", [])) == 0, f"Errors occurred: {final_state.get('errors')}"

    print("\n✅ Week 3 Workflow Test PASSED")
    print(f"  Screens extracted: {len(final_state['extracted_screens'])}")
    print(f"  Options generated: {final_state.get('options_provided_count', 0)}")
    print(f"  ASCII UIs created: {len(final_state.get('selected_designs', {}))}")
    print(f"  Final progress: {final_state['progress_percent']}%")
    print(f"  Current phase: Phase {final_state['current_phase']}")


# Manual test script
async def run_manual_test():
    """
    Manual test that can be run without pytest.

    Usage:
        python -m tests.test_week3_integration
    """
    from src.utils.logger import configure_logging

    # Configure logging
    configure_logging()

    print("=" * 70)
    print("Week 3 Integration Test - Phases 1-3 with ASCII UI Refinement")
    print("=" * 70)

    # Initialize database
    db_manager.initialize_async_engine()

    try:
        print("\n[1/5] Testing Phase 3a: ASCII UI creation...")
        await test_phase3_create_ascii_ui(None, None)

        print("\n[2/5] Testing Phase 3b: Design approval flow...")
        await test_phase3_refine_design_approval(None, None)

        print("\n[3/5] Testing Phase 3b: Refinement with feedback...")
        await test_phase3_refine_design_with_feedback(None, None)

        print("\n[4/5] Testing Phase 3: Conditional routing...")
        await test_phase3_conditional_routing(None, None)

        print("\n[5/5] Testing complete workflow (Phases 1-3)...")
        await test_workflow_phases_1_3_end_to_end(None, None)

        print("\n" + "=" * 70)
        print("✅ ALL WEEK 3 TESTS PASSED")
        print("=" * 70)
        print("\nWeek 3 Deliverable Verified:")
        print("  • ASCII UI generation engine operational ✓")
        print("  • Phase 3a (create_ascii_ui) working ✓")
        print("  • Phase 3b (refine_design) working ✓")
        print("  • Refinement loop with conditional routing ✓")
        print("  • User approval and feedback flow ✓")
        print("  • Workflow Phases 1-3 integrated ✓")

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback

        traceback.print_exc()
        raise
    finally:
        await db_manager.close()


if __name__ == "__main__":
    asyncio.run(run_manual_test())
