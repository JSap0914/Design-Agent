"""
End-to-end workflow integration tests for Phases 1-5.

Tests the complete LangGraph workflow with all nodes connected,
including pause/resume and validation flows.
"""

import pytest

from src.langgraph.state import DesignAgentState


# ============================================================================
# Test: Workflow Graph Structure
# ============================================================================


def test_workflow_has_all_phase_4_5_nodes():
    """Test that workflow includes all Phase 4-5 nodes."""
    from src.langgraph.workflow import create_workflow

    workflow = create_workflow()

    # Check Phase 1-3 nodes
    assert "extract_screens" in workflow.nodes
    assert "generate_options" in workflow.nodes
    assert "create_ascii_ui" in workflow.nodes
    assert "refine_design" in workflow.nodes

    # Check Phase 4-5 nodes (Week 5 additions)
    assert "generate_design_system" in workflow.nodes
    assert "pause_for_google_ai" in workflow.nodes
    assert "receive_code" in workflow.nodes
    assert "validate_code" in workflow.nodes
    assert "handle_validation_failure" in workflow.nodes

    # Total should be 9 nodes
    assert len(workflow.nodes) == 9


def test_workflow_edges_connect_phases():
    """Test that workflow edges correctly connect all phases."""
    from src.langgraph.workflow import create_workflow

    workflow = create_workflow()

    # Check Phase 1 → Phase 2
    assert "generate_options" in workflow.edges.get("extract_screens", [])

    # Check Phase 2 → Phase 3
    assert "create_ascii_ui" in workflow.edges.get("generate_options", [])

    # Check Phase 3 initial → refinement
    assert "refine_design" in workflow.edges.get("create_ascii_ui", [])

    # Check Phase 4 → pause decision
    assert "pause_for_google_ai" in workflow.edges.get("generate_design_system", [])


def test_workflow_has_conditional_edges():
    """Test that workflow has all required conditional edges."""
    from src.langgraph.workflow import create_workflow

    workflow = create_workflow()

    # Check refinement loop conditional edge
    assert "refine_design" in workflow.branches

    # Check pause decision conditional edge
    assert "pause_for_google_ai" in workflow.branches

    # Check code upload conditional edge
    assert "receive_code" in workflow.branches

    # Check validation conditional edge
    assert "validate_code" in workflow.branches


# ============================================================================
# Test: Phase 3 → Phase 4 Flow
# ============================================================================


@pytest.mark.asyncio
async def test_refinement_complete_routes_to_phase_4():
    """Test that completing Phase 3 routes to Phase 4 (generate_design_system)."""
    from src.langgraph.nodes.refine_design import should_continue_refining

    # All screens approved
    state: DesignAgentState = {
        "job_id": "test-123",
        "extracted_screens": ["Screen A", "Screen B"],
        "current_screen_index": 1,  # Last screen
        "current_screen_name": "Screen B",
        "selected_designs": {
            "Screen A": "ascii ui A",
            "Screen B": "ascii ui B",
        },
        "awaiting_feedback": False,
        "user_feedback": "approve",
    }

    result = should_continue_refining(state)
    assert result == "complete"  # Should route to Phase 4


# ============================================================================
# Test: Phase 4 → Phase 5 Pause Flow
# ============================================================================


@pytest.mark.asyncio
async def test_pause_workflow_routes_to_code_upload():
    """Test that choosing 'pause' routes to receive_code node."""
    from src.langgraph.nodes.pause_for_google_ai import (
        pause_for_google_ai,
        should_pause_or_continue,
    )

    # User chooses to pause
    state: DesignAgentState = {
        "job_id": "test-pause",
        "user_feedback": "pause",
    }

    result = await pause_for_google_ai(state)
    assert result["should_pause_for_google_ai"] is True
    assert result["paused"] is True

    # Check routing
    routing = should_pause_or_continue(result)
    assert routing == "pause"  # Should route to receive_code


@pytest.mark.asyncio
async def test_skip_workflow_routes_to_end():
    """Test that choosing 'skip' routes to END (Phase 6 TODO)."""
    from src.langgraph.nodes.pause_for_google_ai import (
        pause_for_google_ai,
        should_pause_or_continue,
    )

    # User chooses to skip
    state: DesignAgentState = {
        "job_id": "test-skip",
        "user_feedback": "skip",
    }

    result = await pause_for_google_ai(state)
    assert result["should_pause_for_google_ai"] is False
    assert result["paused"] is False

    # Check routing
    routing = should_pause_or_continue(result)
    assert routing == "skip_to_phase6"  # Should route to END (Phase 6 later)


# ============================================================================
# Test: Phase 5 Code Upload Flow
# ============================================================================


@pytest.mark.asyncio
async def test_code_upload_routes_to_validation():
    """Test that code upload routes to validate_code node."""
    from src.langgraph.nodes.receive_code import has_code_been_uploaded, receive_code

    # Code uploaded
    state: DesignAgentState = {
        "job_id": "test-upload",
        "uploaded_code": "const App = () => <div>Hello</div>;",
        "uploaded_code_metadata": {"file_extension": ".tsx"},
    }

    result = await receive_code(state)
    assert result["paused"] is False

    # Check routing
    routing = has_code_been_uploaded(result)
    assert routing == "code_uploaded"  # Should route to validate_code


@pytest.mark.asyncio
async def test_no_code_upload_stays_paused():
    """Test that no code upload keeps workflow paused."""
    from src.langgraph.nodes.receive_code import has_code_been_uploaded, receive_code

    # No code uploaded
    state: DesignAgentState = {
        "job_id": "test-waiting",
        "uploaded_code": None,
    }

    result = await receive_code(state)
    assert result["paused"] is True

    # Check routing
    routing = has_code_been_uploaded(result)
    assert routing == "waiting"  # Should stay at END (paused)


# ============================================================================
# Test: Phase 5 Validation Flow
# ============================================================================


@pytest.mark.asyncio
async def test_validation_passed_routes_to_end():
    """Test that validation passing routes to END (Phase 6 TODO)."""
    from src.langgraph.nodes.validate_code import should_proceed_after_validation

    # High quality score
    state: DesignAgentState = {
        "validation_passed": True,
        "quality_score": 95.0,
    }

    routing = should_proceed_after_validation(state)
    assert routing == "validation_passed"  # Should route to END (Phase 6 later)


@pytest.mark.asyncio
async def test_validation_failed_routes_to_failure_handler():
    """Test that validation failure routes to handle_validation_failure."""
    from src.langgraph.nodes.validate_code import should_proceed_after_validation

    # Low quality score
    state: DesignAgentState = {
        "validation_passed": False,
        "quality_score": 65.0,
    }

    routing = should_proceed_after_validation(state)
    assert routing == "validation_failed"  # Should route to handle_validation_failure


# ============================================================================
# Test: Complete Workflows (Mocked)
# ============================================================================


@pytest.mark.asyncio
async def test_complete_pause_workflow():
    """
    Test complete workflow: Phases 1-3 → Phase 4 → Pause → Upload → Validate → END.

    This is a simplified test that verifies the node connections work.
    Full end-to-end test with actual LLM calls would be in separate integration suite.
    """
    from src.langgraph.nodes.generate_design_system import generate_design_system
    from src.langgraph.nodes.pause_for_google_ai import pause_for_google_ai
    from src.langgraph.nodes.receive_code import receive_code
    from src.langgraph.nodes.validate_code import validate_code

    # Start with approved designs from Phase 3
    state: DesignAgentState = {
        "job_id": "test-complete-pause",
        "prd_content": "Test PRD",
        "trd_content": "Test TRD",
        "extracted_screens": ["Screen A"],
        "selected_designs": {"Screen A": "ascii ui A"},
        "design_decisions": [],
        "selected_open_source": [],
    }

    # Phase 4: Generate Design System
    state = await generate_design_system(state)
    assert "design_system" in state
    assert state["current_phase"] == 4

    # Phase 4.5: User chooses to pause
    state["user_feedback"] = "pause"
    state = await pause_for_google_ai(state)
    assert state["paused"] is True

    # Phase 5: User uploads code
    state["uploaded_code"] = """
import React from 'react';

interface Props { title: string; }

export const App: React.FC<Props> = ({ title }) => {
  return (
    <main className="min-h-screen bg-gray-50">
      <h1 className="text-3xl font-bold">{title}</h1>
    </main>
  );
};
"""
    state["uploaded_code_metadata"] = {"file_extension": ".tsx"}

    state = await receive_code(state)
    assert state["paused"] is False

    # Phase 5: Validate code
    state = await validate_code(state)
    assert "validation_results" in state
    assert "quality_score" in state


@pytest.mark.asyncio
async def test_complete_skip_workflow():
    """
    Test complete workflow: Phases 1-3 → Phase 4 → Skip → END.

    Verifies skip path bypasses code upload and validation.
    """
    from src.langgraph.nodes.generate_design_system import generate_design_system
    from src.langgraph.nodes.pause_for_google_ai import pause_for_google_ai

    # Start with approved designs from Phase 3
    state: DesignAgentState = {
        "job_id": "test-complete-skip",
        "prd_content": "Test PRD",
        "trd_content": "Test TRD",
        "extracted_screens": ["Screen A"],
        "selected_designs": {"Screen A": "ascii ui A"},
        "design_decisions": [],
        "selected_open_source": [],
    }

    # Phase 4: Generate Design System
    state = await generate_design_system(state)
    assert "design_system" in state

    # Phase 4.5: User chooses to skip
    state["user_feedback"] = "skip"
    state = await pause_for_google_ai(state)
    assert state["paused"] is False
    assert state["should_pause_for_google_ai"] is False
    assert state["uploaded_code"] is None

    # Should proceed directly to Phase 6 (END for now)


# ============================================================================
# Summary
# ============================================================================


def test_workflow_summary():
    """Print workflow summary for documentation."""
    from src.langgraph.workflow import create_workflow

    workflow = create_workflow()

    print("\n" + "=" * 70)
    print("WORKFLOW INTEGRATION TEST SUMMARY")
    print("=" * 70)
    print(f"\nTotal nodes: {len(workflow.nodes)}")
    print("\nPhases 1-3 (Weeks 1-3):")
    print("  ✓ extract_screens")
    print("  ✓ generate_options")
    print("  ✓ create_ascii_ui")
    print("  ✓ refine_design")

    print("\nPhases 4-5 (Week 5):")
    print("  ✓ generate_design_system")
    print("  ✓ pause_for_google_ai")
    print("  ✓ receive_code")
    print("  ✓ validate_code")
    print("  ✓ handle_validation_failure")

    print("\nConditional edges:")
    print(f"  ✓ {len(workflow.branches)} conditional routing points")

    print("\nWorkflow ready for Phases 1-5 execution!")
    print("=" * 70 + "\n")
