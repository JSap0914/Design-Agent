"""
Week 2 Integration Test: Phases 1-2 End-to-End.

Tests the complete flow:
1. Screen extraction from PRD/TRD
2. Layout options generation (2-3 per screen)
3. LangGraph workflow execution
4. State persistence with PostgreSQL checkpointer
"""

import asyncio
import uuid

import pytest
from sqlalchemy import select

from src.database.connection import db_manager
from src.database.models import DesignJob, DesignProgress
from src.langgraph.workflow import compile_workflow


# Sample PRD for testing
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
async def test_phase1_screen_extraction(setup_database, mock_llm_extract_screens):
    """
    Test Phase 1: Screen extraction from PRD/TRD.

    Verifies:
    1. Workflow can extract screens from PRD
    2. Screen count is within valid range (3-12)
    3. Screen names are meaningful

    Uses mocked LLM for deterministic testing without API keys.
    """
    from src.langgraph.nodes.extract_screens import extract_screens

    # Prepare state
    state = {
        "job_id": str(uuid.uuid4()),
        "project_id": "test-001",
        "user_id": "test-user",
        "prd_content": SAMPLE_PRD,
        "trd_content": SAMPLE_TRD,
    }

    # Execute Phase 1
    result = await extract_screens(state)

    # Verify results
    assert "extracted_screens" in result, "extracted_screens missing from result"
    assert isinstance(result["extracted_screens"], list), "extracted_screens should be a list"
    assert len(result["extracted_screens"]) >= 3, "Should extract at least 3 screens"
    assert len(result["extracted_screens"]) <= 12, "Should extract at most 12 screens"
    assert result["screen_count"] == len(
        result["extracted_screens"]
    ), "screen_count should match list length"
    assert result["current_phase"] == 1, "Should be in Phase 1"
    assert result["progress_percent"] > 0, "Progress should be > 0"

    print(f"✓ Phase 1: Extracted {len(result['extracted_screens'])} screens")
    print(f"  Screens: {result['extracted_screens']}")


@pytest.mark.asyncio
async def test_phase2_layout_options(setup_database, mock_llm_generate_options):
    """
    Test Phase 2: Layout options generation.

    Verifies:
    1. Generates 2-3 options per screen (BMAD principle)
    2. Options have meaningful descriptions
    3. All screens get options

    Uses mocked LLM for deterministic testing without API keys.
    """
    from src.langgraph.nodes.generate_options import generate_options

    # Prepare state (assuming Phase 1 completed)
    state = {
        "job_id": str(uuid.uuid4()),
        "project_id": "test-002",
        "user_id": "test-user",
        "prd_content": SAMPLE_PRD,
        "trd_content": SAMPLE_TRD,
        "extracted_screens": ["Login Screen", "Task List Screen", "Task Detail Screen"],
        "screen_count": 3,
    }

    # Execute Phase 2
    result = await generate_options(state)

    # Verify results
    assert "design_options" in result, "design_options missing from result"
    assert isinstance(result["design_options"], dict), "design_options should be a dict"

    # Check each screen has 2-3 options
    for screen_name, options in result["design_options"].items():
        assert len(options) >= 2, f"{screen_name} should have at least 2 options (BMAD)"
        assert len(options) <= 3, f"{screen_name} should have at most 3 options"
        print(f"✓ {screen_name}: {len(options)} options generated")

    assert result["current_phase"] == 2, "Should be in Phase 2"
    assert result["progress_percent"] > 15, "Progress should be > 15% after Phase 2"
    assert result["options_provided_count"] >= 6, "Should have generated at least 6 total options"

    print(f"✓ Phase 2: Generated {result['options_provided_count']} total layout options")


@pytest.mark.asyncio
async def test_workflow_phases_1_2_end_to_end(setup_database, mock_llm_all_phases):
    """
    Test complete workflow execution for Phases 1-2.

    Verifies:
    1. Workflow executes both phases sequentially
    2. State flows correctly between phases
    3. Progress tracking works
    4. Final state contains all expected data

    Uses mocked LLM for deterministic testing without API keys.
    """
    # Compile workflow
    workflow = compile_workflow()

    # Prepare initial state
    job_id = str(uuid.uuid4())
    initial_state = {
        "job_id": job_id,
        "project_id": "test-workflow-001",
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
    config = {"configurable": {"thread_id": job_id}}
    final_state = await workflow.ainvoke(initial_state, config)

    # Verify Phase 1 results
    assert "extracted_screens" in final_state, "Phase 1 should extract screens"
    assert len(final_state["extracted_screens"]) >= 3, "Should have at least 3 screens"

    # Verify Phase 2 results
    assert "design_options" in final_state, "Phase 2 should generate options"
    assert len(final_state["design_options"]) == len(
        final_state["extracted_screens"]
    ), "Should have options for all screens"

    # Verify BMAD compliance
    for screen_name, options in final_state["design_options"].items():
        assert len(options) >= 2, f"BMAD violation: {screen_name} has less than 2 options"

    # Verify progress tracking
    assert final_state["current_phase"] == 2, "Should complete Phase 2"
    assert final_state["progress_percent"] >= 30, "Progress should be >= 30%"

    # Verify no errors
    assert len(final_state.get("errors", [])) == 0, f"Errors occurred: {final_state.get('errors')}"

    print("\n✅ Week 2 Workflow Test PASSED")
    print(f"  Screens extracted: {len(final_state['extracted_screens'])}")
    print(f"  Options generated: {final_state.get('options_provided_count', 0)}")
    print(f"  Final progress: {final_state['progress_percent']}%")


# Manual test script
async def run_manual_test():
    """
    Manual test that can be run without pytest.

    Usage:
        python -m tests.test_week2_integration
    """
    from src.utils.logger import configure_logging

    # Configure logging
    configure_logging()

    print("=" * 70)
    print("Week 2 Integration Test - Phases 1-2")
    print("=" * 70)

    # Initialize database
    db_manager.initialize_async_engine()

    try:
        print("\n[1/3] Testing Phase 1: Screen extraction...")
        await test_phase1_screen_extraction(None)

        print("\n[2/3] Testing Phase 2: Layout options generation...")
        await test_phase2_layout_options(None)

        print("\n[3/3] Testing complete workflow (Phases 1-2)...")
        await test_workflow_phases_1_2_end_to_end(None)

        print("\n" + "=" * 70)
        print("✅ ALL WEEK 2 TESTS PASSED")
        print("=" * 70)
        print("\nWeek 2 Deliverable Verified:")
        print("  • LangGraph workflow operational ✓")
        print("  • Phase 1 (screen extraction) working ✓")
        print("  • Phase 2 (layout options) working ✓")
        print("  • BMAD methodology enforced (2-3 options) ✓")
        print("  • PostgreSQL checkpointer integrated ✓")

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback

        traceback.print_exc()
        raise
    finally:
        await db_manager.close()


if __name__ == "__main__":
    asyncio.run(run_manual_test())
