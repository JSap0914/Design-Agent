"""
Integration tests for workflow phase transitions.

Tests complete workflow execution from Phase 1 through Phase 6.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from pathlib import Path

from src.langgraph.state import DesignAgentState
from src.langgraph.nodes.extract_screens import extract_screens
from src.langgraph.nodes.generate_options import generate_options
from src.langgraph.nodes.create_ascii_ui import create_ascii_ui
from src.langgraph.nodes.refine_design import refine_design, should_continue_refining
from src.langgraph.nodes.generate_design_system import generate_design_system
from src.langgraph.nodes.generate_documents import generate_documents
from src.langgraph.nodes.package_for_dev import package_for_dev


# ============================================================================
# Sequential Phase Transition Tests
# ============================================================================


@pytest.mark.asyncio
async def test_phase_1_to_2_transition():
    """Test transition from Phase 1 (Extract Screens) to Phase 2 (Generate Options)."""
    # Start with Phase 1
    state: DesignAgentState = {
        "job_id": "test-phase-1-2",
        "prd_content": "# Task App\n\nScreens: Login, Dashboard, Settings",
        "trd_content": "# Tech: React + TypeScript",
        "extracted_screens": [],
        "current_phase": 0,
    }

    with patch("src.langgraph.nodes.extract_screens.generate_json_async", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = {
            "screens": ["Login Screen", "Dashboard", "Settings"],
            "rationale": "Three main screens",
        }

        # Execute Phase 1
        phase1_result = await extract_screens(state)

        assert phase1_result["current_phase"] == 1
        assert len(phase1_result["extracted_screens"]) == 3

    # Transition to Phase 2
    with patch("src.langgraph.nodes.generate_options.llm_client.complete_with_json", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = {
            "options": [
                {"option_number": 1, "layout_description": "Layout 1", "key_features": ["F1"], "pros": ["P"], "cons": ["C"], "recommended": True},
                {"option_number": 2, "layout_description": "Layout 2", "key_features": ["F2"], "pros": ["P"], "cons": ["C"], "recommended": False},
            ]
        }

        # Execute Phase 2
        phase2_result = await generate_options(phase1_result)

        assert phase2_result["current_phase"] == 2
        assert "design_options" in phase2_result
        assert len(phase2_result["design_options"]) == 3  # All screens have options


@pytest.mark.asyncio
async def test_phase_2_to_3_transition():
    """Test transition from Phase 2 (Generate Options) to Phase 3 (Create ASCII UI)."""
    state: DesignAgentState = {
        "job_id": "test-phase-2-3",
        "prd_content": "# Test PRD",
        "trd_content": "# Tech: React",
        "extracted_screens": ["Login", "Dashboard"],
        "design_options_metadata": {
            "Login": [
                {"option_number": 1, "layout_description": "Centered card", "key_features": ["Card"]},
            ],
            "Dashboard": [
                {"option_number": 1, "layout_description": "Grid layout", "key_features": ["Grid"]},
            ],
        },
        "current_phase": 2,
    }

    with patch("src.langgraph.nodes.create_ascii_ui.llm_client.complete", new_callable=AsyncMock) as mock_llm, \
         patch("src.langgraph.nodes.create_ascii_ui.broadcast_ascii_ui_update", new_callable=AsyncMock), \
         patch("src.langgraph.nodes.create_ascii_ui.ASCIIUIGenerator") as mock_gen:

        mock_llm.return_value = "┌────┐\n│UI  │\n└────┘"
        mock_generator = MagicMock()
        mock_generator.validate_ascii_ui.return_value = (True, [])
        mock_gen.return_value = mock_generator

        # Execute Phase 3
        phase3_result = await create_ascii_ui(state)

        assert phase3_result["current_phase"] == 3
        assert "selected_designs" in phase3_result
        assert len(phase3_result["selected_designs"]) == 2


@pytest.mark.asyncio
async def test_phase_3_refinement_loop():
    """Test Phase 3 refinement loop with user feedback."""
    state: DesignAgentState = {
        "job_id": "test-phase-3-loop",
        "prd_content": "# Test PRD",
        "trd_content": "# Tech: React",
        "extracted_screens": ["Login", "Dashboard"],
        "selected_designs": {
            "Login": "┌────┐\n│UI  │\n└────┘",
            "Dashboard": "┌────┐\n│Dash│\n└────┘",
        },
        "design_decisions": [],
        "current_phase": 3,
        "current_screen_index": 0,
        "user_feedback": None,
    }

    # First call: No feedback, should wait
    result1 = await refine_design(state)
    assert result1["awaiting_feedback"] is True
    assert should_continue_refining(result1) == "continue"

    # Second call: User provides refinement feedback
    result1["user_feedback"] = "Move button to bottom"

    with patch("src.langgraph.nodes.refine_design.llm_client.complete", new_callable=AsyncMock) as mock_llm, \
         patch("src.langgraph.nodes.refine_design.broadcast_ascii_ui_update", new_callable=AsyncMock), \
         patch("src.langgraph.nodes.refine_design.should_trigger_library_search", return_value=False):

        mock_llm.return_value = "┌────┐\n│UI2 │\n└────┘"

        result2 = await refine_design(result1)
        assert result2["selected_designs"]["Login"] != state["selected_designs"]["Login"]
        assert should_continue_refining(result2) == "continue"

    # Third call: User approves
    result2["user_feedback"] = "approve"
    result3 = await refine_design(result2)
    assert result3["current_screen_index"] == 1  # Moved to next screen
    assert should_continue_refining(result3) == "continue"

    # Fourth call: Approve last screen
    result3["user_feedback"] = "approve"
    result4 = await refine_design(result3)
    assert result4["current_screen_index"] == 2  # Beyond last screen
    assert should_continue_refining(result4) == "complete"


@pytest.mark.asyncio
async def test_phase_4_to_5_transition():
    """Test transition from Phase 4 (Design System) to Phase 5 (not implemented yet)."""
    state: DesignAgentState = {
        "job_id": "test-phase-4-5",
        "selected_designs": {"Login": "UI content"},
        "design_decisions": [],
        "selected_open_source": [],
        "current_phase": 3,
    }

    with patch("src.langgraph.nodes.generate_design_system.llm_client.complete_with_json", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = {
            "colors": {"primary": ["#3B82F6"]},
            "typography": {"sizes": {"base": "16px"}},
            "spacing": {"values": {"2": "8px"}},
            "border_radius": {"base": "8px"},
            "shadows": {"sm": "0 1px 2px"},
            "icons": {"size": "24px"},
            "component_libraries": [],
        }

        result = await generate_design_system(state)

        assert result["current_phase"] == 4
        assert result["progress_percent"] == 70.0
        assert "design_system" in result


@pytest.mark.asyncio
async def test_phase_5_to_6_transition():
    """Test transition from Phase 5 (skipped) to Phase 6 (Generate Documents)."""
    state: DesignAgentState = {
        "job_id": "test-phase-5-6",
        "prd_content": "# Test PRD",
        "trd_content": "# Test TRD",
        "extracted_screens": ["Login"],
        "selected_designs": {"Login": "UI"},
        "design_system": {"colors": {"primary": ["#3B82F6"]}},
        "design_decisions": [],
        "selected_open_source": [],
        "current_phase": 5,
    }

    with patch("src.langgraph.nodes.generate_documents.generate_text_async", new_callable=AsyncMock) as mock_gen, \
         patch("src.langgraph.nodes.generate_documents.store_all_documents", new_callable=AsyncMock):

        mock_gen.return_value = "# Document Content"

        result = await generate_documents(state)

        assert result["current_phase"] == 6
        assert result["progress_percent"] == 90.0
        assert len(result["generated_documents"]) == 6


@pytest.mark.asyncio
async def test_phase_6_completion():
    """Test Phase 6 (Package for Dev) marks workflow as complete."""
    state: DesignAgentState = {
        "job_id": "test-phase-6-complete",
        "generated_documents": {
            "design_system": "docs/Design_System_v0.9.md",
        },
        "uploaded_code": "const App = () => <div />;",
        "validation_results": {"quality_score": 95},
        "extracted_screens": ["Login"],
        "selected_open_source": [],
        "current_phase": 5,
    }

    with patch("pathlib.Path.mkdir"), \
         patch("pathlib.Path.exists", return_value=True), \
         patch("pathlib.Path.read_text", return_value="# Content"), \
         patch("pathlib.Path.write_text"), \
         patch("src.langgraph.nodes.package_for_dev.create_package_zip", new_callable=AsyncMock), \
         patch("src.langgraph.nodes.package_for_dev.upload_to_anyon", new_callable=AsyncMock):

        result = await package_for_dev(state)

        assert result["current_phase"] == 6
        assert result["phase_name"] == "Complete"
        assert result["status"] == "completed"


# ============================================================================
# End-to-End Workflow Tests
# ============================================================================


@pytest.mark.asyncio
async def test_complete_workflow_phases_1_to_6():
    """Test complete workflow execution from Phase 1 to Phase 6."""
    initial_state: DesignAgentState = {
        "job_id": "test-e2e-workflow",
        "prd_content": "# E-commerce App\n\nScreens: Home, Product List, Cart",
        "trd_content": "# Tech: React + TypeScript + Tailwind",
        "extracted_screens": [],
        "current_phase": 0,
    }

    # Mock all LLM calls and external dependencies
    with patch("src.langgraph.nodes.extract_screens.generate_json_async", new_callable=AsyncMock) as mock_extract, \
         patch("src.langgraph.nodes.generate_options.llm_client.complete_with_json", new_callable=AsyncMock) as mock_options, \
         patch("src.langgraph.nodes.create_ascii_ui.llm_client.complete", new_callable=AsyncMock) as mock_ascii, \
         patch("src.langgraph.nodes.create_ascii_ui.broadcast_ascii_ui_update", new_callable=AsyncMock), \
         patch("src.langgraph.nodes.create_ascii_ui.ASCIIUIGenerator") as mock_gen_class, \
         patch("src.langgraph.nodes.generate_design_system.llm_client.complete_with_json", new_callable=AsyncMock) as mock_ds, \
         patch("src.langgraph.nodes.generate_documents.generate_text_async", new_callable=AsyncMock) as mock_docs, \
         patch("src.langgraph.nodes.generate_documents.store_all_documents", new_callable=AsyncMock), \
         patch("pathlib.Path.mkdir"), \
         patch("pathlib.Path.exists", return_value=False), \
         patch("pathlib.Path.write_text"), \
         patch("src.langgraph.nodes.package_for_dev.create_package_zip", new_callable=AsyncMock), \
         patch("src.langgraph.nodes.package_for_dev.upload_to_anyon", new_callable=AsyncMock):

        # Setup mocks
        mock_extract.return_value = {"screens": ["Home", "Product List", "Cart"], "rationale": "Three screens"}
        mock_options.return_value = {
            "options": [
                {"option_number": 1, "layout_description": "Layout", "key_features": ["F"], "pros": ["P"], "cons": ["C"], "recommended": True},
                {"option_number": 2, "layout_description": "Layout 2", "key_features": ["F"], "pros": ["P"], "cons": ["C"], "recommended": False},
            ]
        }
        mock_ascii.return_value = "┌────┐\n│UI  │\n└────┘"
        mock_generator = MagicMock()
        mock_generator.validate_ascii_ui.return_value = (True, [])
        mock_gen_class.return_value = mock_generator
        mock_ds.return_value = {
            "colors": {"primary": ["#3B82F6"]},
            "typography": {"sizes": {"base": "16px"}},
            "spacing": {"values": {"2": "8px"}},
            "border_radius": {"base": "8px"},
            "shadows": {"sm": "0 1px 2px"},
            "icons": {"size": "24px"},
            "component_libraries": [],
        }
        mock_docs.return_value = "# Document"

        # Phase 1: Extract Screens
        state = await extract_screens(initial_state)
        assert state["current_phase"] == 1
        assert len(state["extracted_screens"]) == 3

        # Phase 2: Generate Options
        state = await generate_options(state)
        assert state["current_phase"] == 2
        assert len(state["design_options"]) == 3

        # Phase 3: Create ASCII UI
        state = await create_ascii_ui(state)
        assert state["current_phase"] == 3
        assert len(state["selected_designs"]) == 3

        # Phase 3 Refinement (skip for E2E - simulate approval)
        # In real workflow, this would loop through screens with user approval

        # Phase 4: Generate Design System
        state = await generate_design_system(state)
        assert state["current_phase"] == 4
        assert "design_system" in state

        # Phase 6: Generate Documents (Phase 5 skipped in current implementation)
        state = await generate_documents(state)
        assert state["current_phase"] == 6
        assert len(state["generated_documents"]) == 6

        # Phase 6: Package for Dev
        state = await package_for_dev(state)
        assert state["status"] == "completed"
        assert state["current_phase"] == 6


# ============================================================================
# State Persistence Tests
# ============================================================================


@pytest.mark.asyncio
async def test_state_persistence_across_phases():
    """Test that state fields are preserved across phase transitions."""
    initial_state: DesignAgentState = {
        "job_id": "test-persistence",
        "project_id": "proj-123",
        "user_id": "user-456",
        "prd_content": "# PRD",
        "trd_content": "# TRD",
        "custom_metadata": {"key": "value"},
        "extracted_screens": [],
        "current_phase": 0,
    }

    with patch("src.langgraph.nodes.extract_screens.generate_json_async", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = {"screens": ["Screen1"], "rationale": "One screen"}

        result = await extract_screens(initial_state)

        # Verify original fields preserved
        assert result["job_id"] == "test-persistence"
        assert result["project_id"] == "proj-123"
        assert result["user_id"] == "user-456"
        assert result["custom_metadata"] == {"key": "value"}
        # New fields added
        assert result["current_phase"] == 1
        assert len(result["extracted_screens"]) == 1


@pytest.mark.asyncio
async def test_progress_monotonically_increases():
    """Test that progress_percent increases through phases."""
    state: DesignAgentState = {
        "job_id": "test-progress",
        "prd_content": "# PRD",
        "trd_content": "# TRD",
        "extracted_screens": ["S1", "S2"],
        "current_phase": 0,
        "progress_percent": 0.0,
    }

    progress_values = []

    # Phase 1
    with patch("src.langgraph.nodes.extract_screens.generate_json_async", new_callable=AsyncMock) as mock:
        mock.return_value = {"screens": ["S1", "S2"], "rationale": "Two"}
        state = await extract_screens(state)
        progress_values.append(state.get("progress_percent", 0))

    # Phase 2
    with patch("src.langgraph.nodes.generate_options.llm_client.complete_with_json", new_callable=AsyncMock) as mock:
        mock.return_value = {
            "options": [
                {"option_number": 1, "layout_description": "L", "key_features": ["F"], "pros": ["P"], "cons": ["C"], "recommended": True},
                {"option_number": 2, "layout_description": "L2", "key_features": ["F"], "pros": ["P"], "cons": ["C"], "recommended": False},
            ]
        }
        state["design_options_metadata"] = {}
        state = await generate_options(state)
        progress_values.append(state.get("progress_percent", 0))

    # Verify progress increases
    assert all(progress_values[i] < progress_values[i + 1] for i in range(len(progress_values) - 1))


# ============================================================================
# Error Handling Tests
# ============================================================================


@pytest.mark.asyncio
async def test_phase_error_recovery():
    """Test that errors in one phase don't break workflow."""
    state: DesignAgentState = {
        "job_id": "test-error-recovery",
        "prd_content": "# PRD",
        "trd_content": "# TRD",
        "extracted_screens": [],
        "current_phase": 0,
    }

    with patch("src.langgraph.nodes.extract_screens.generate_json_async", new_callable=AsyncMock) as mock_llm:
        # Simulate LLM failure
        mock_llm.side_effect = Exception("LLM API timeout")

        result = await extract_screens(state)

        # Should have error but state intact
        assert "errors" in result
        assert result["should_retry"] is True
        assert result["retry_count"] == 1
        # Original state preserved
        assert result["job_id"] == "test-error-recovery"


@pytest.mark.asyncio
async def test_retry_mechanism():
    """Test retry mechanism after failure."""
    state: DesignAgentState = {
        "job_id": "test-retry",
        "prd_content": "# PRD",
        "trd_content": "# TRD",
        "extracted_screens": [],
        "current_phase": 0,
        "retry_count": 0,
    }

    with patch("src.langgraph.nodes.extract_screens.generate_json_async", new_callable=AsyncMock) as mock_llm:
        # First attempt fails
        mock_llm.side_effect = Exception("Timeout")
        result1 = await extract_screens(state)
        assert result1["retry_count"] == 1

        # Second attempt succeeds
        mock_llm.side_effect = None
        mock_llm.return_value = {"screens": ["Screen1"], "rationale": "Success"}
        result2 = await extract_screens(result1)
        assert result2["current_phase"] == 1
        assert len(result2["extracted_screens"]) == 1


# ============================================================================
# Conditional Routing Tests
# ============================================================================


@pytest.mark.asyncio
async def test_refinement_conditional_routing():
    """Test conditional routing in refinement loop."""
    # Test: Should continue when screens remain
    state_continue: DesignAgentState = {
        "extracted_screens": ["S1", "S2", "S3"],
        "current_screen_index": 1,
        "refinement_complete": False,
    }
    assert should_continue_refining(state_continue) == "continue"

    # Test: Should complete when all screens done
    state_complete: DesignAgentState = {
        "extracted_screens": ["S1", "S2"],
        "current_screen_index": 2,
        "refinement_complete": False,
    }
    assert should_continue_refining(state_complete) == "complete"

    # Test: Should complete when refinement_complete flag set
    state_flag: DesignAgentState = {
        "extracted_screens": ["S1"],
        "current_screen_index": 0,
        "refinement_complete": True,
    }
    assert should_continue_refining(state_flag) == "complete"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
