"""
Unit tests for refine_design node (Phase 3 conversational refinement).

Tests user feedback processing, library discovery integration, and approval flow.
"""

import pytest
from unittest.mock import AsyncMock, patch

from src.langgraph.nodes.refine_design import refine_design, should_continue_refining
from src.langgraph.state import DesignAgentState


SAMPLE_ASCII = """┌──────────────────────────────────────┐
│  📱 Login                    ☰       │
├──────────────────────────────────────┤
│  Email                               │
│  [___________________________]       │
│                                      │
│  Password                            │
│  [___________________________]       │
│                                      │
│         [    Sign In    ]            │
└──────────────────────────────────────┘"""


@pytest.mark.asyncio
async def test_refine_design_approval():
    """Test user approving a screen moves to next screen."""
    state: DesignAgentState = {
        "job_id": "test-job-approval",
        "prd_content": "# Test PRD",
        "trd_content": "# Test TRD",
        "extracted_screens": ["Login", "Dashboard", "Settings"],
        "selected_designs": {
            "Login": SAMPLE_ASCII,
            "Dashboard": "...",
            "Settings": "...",
        },
        "design_decisions": [],
        "current_screen_index": 0,
        "user_feedback": "approve",
    }

    result = await refine_design(state)

    # Should move to next screen
    assert result["current_screen_index"] == 1
    assert result["completed_screens"] == 1
    assert result["user_feedback"] is None
    assert result["awaiting_feedback"] is False

    # Should record approval decision
    assert len(result["design_decisions"]) == 1
    decision = result["design_decisions"][0]
    assert decision["screen_name"] == "Login"
    assert decision["decision_type"] == "approval"
    assert decision["user_feedback"] == "approve"

    # Progress should increase
    assert 50.0 < result["progress_percent"] < 65.0


@pytest.mark.asyncio
async def test_refine_design_approval_variations():
    """Test different approval keywords."""
    for approval_keyword in ["approve", "approved", "looks good", "next"]:
        state: DesignAgentState = {
            "job_id": f"test-job-{approval_keyword}",
            "prd_content": "# Test PRD",
            "trd_content": "# Test TRD",
            "extracted_screens": ["Login"],
            "selected_designs": {"Login": SAMPLE_ASCII},
            "design_decisions": [],
            "current_screen_index": 0,
            "user_feedback": approval_keyword,
        }

        result = await refine_design(state)

        # Should approve and move forward
        assert result["current_screen_index"] == 1
        assert len(result["design_decisions"]) == 1


@pytest.mark.asyncio
async def test_refine_design_last_screen_approval():
    """Test approving the last screen completes refinement."""
    state: DesignAgentState = {
        "job_id": "test-job-last",
        "prd_content": "# Test PRD",
        "trd_content": "# Test TRD",
        "extracted_screens": ["Login", "Dashboard"],
        "selected_designs": {"Login": SAMPLE_ASCII, "Dashboard": "..."},
        "design_decisions": [],
        "current_screen_index": 1,  # Last screen
        "user_feedback": "approve",
    }

    result = await refine_design(state)

    # Should complete refinement
    assert result["current_screen_index"] == 2  # Beyond last screen
    assert result["progress_percent"] == 65.0


@pytest.mark.asyncio
async def test_refine_design_modification():
    """Test user requesting modifications to ASCII UI."""
    state: DesignAgentState = {
        "job_id": "test-job-modify",
        "prd_content": "# Test PRD",
        "trd_content": "# Test TRD",
        "extracted_screens": ["Login"],
        "selected_designs": {"Login": SAMPLE_ASCII},
        "design_decisions": [],
        "current_screen_index": 0,
        "user_feedback": "Move the Sign In button to the bottom",
    }

    with patch("src.langgraph.nodes.refine_design.llm_client.complete", new_callable=AsyncMock) as mock_llm, \
         patch("src.langgraph.nodes.refine_design.broadcast_ascii_ui_update", new_callable=AsyncMock) as mock_broadcast, \
         patch("src.langgraph.nodes.refine_design.should_trigger_library_search") as mock_trigger:

        # Not a library search
        mock_trigger.return_value = False

        # LLM returns refined ASCII
        refined_ascii = SAMPLE_ASCII.replace("[    Sign In    ]", "")  # Simulate modification
        mock_llm.return_value = refined_ascii

        result = await refine_design(state)

        # Should update selected_designs
        assert result["selected_designs"]["Login"] != SAMPLE_ASCII
        assert result["selected_designs"]["Login"] == refined_ascii

        # Should record refinement decision
        assert len(result["design_decisions"]) == 1
        decision = result["design_decisions"][0]
        assert decision["screen_name"] == "Login"
        assert decision["decision_type"] == "refinement"
        assert "Move the Sign In button" in decision["rationale"]

        # Should remain on same screen awaiting next feedback
        assert result["current_screen_index"] == 0
        assert result["awaiting_feedback"] is True
        assert result["user_feedback"] is None

        # Should broadcast update
        mock_broadcast.assert_called_once()


@pytest.mark.asyncio
async def test_refine_design_no_feedback():
    """Test initial state with no user feedback yet."""
    state: DesignAgentState = {
        "job_id": "test-job-no-feedback",
        "prd_content": "# Test PRD",
        "trd_content": "# Test TRD",
        "extracted_screens": ["Login", "Dashboard"],
        "selected_designs": {"Login": SAMPLE_ASCII, "Dashboard": "..."},
        "design_decisions": [],
        "current_screen_index": 0,
        "user_feedback": None,
    }

    result = await refine_design(state)

    # Should set awaiting_feedback flag
    assert result["awaiting_feedback"] is True
    assert result["current_screen_name"] == "Login"
    assert result["phase_name"] == "Review Login"
    assert result["current_screen_index"] == 0  # Unchanged


@pytest.mark.asyncio
async def test_refine_design_library_discovery():
    """Test triggering library search from user feedback."""
    state: DesignAgentState = {
        "job_id": "test-job-library",
        "prd_content": "# Test PRD",
        "trd_content": "# Test TRD",
        "extracted_screens": ["Dashboard"],
        "selected_designs": {"Dashboard": SAMPLE_ASCII},
        "design_decisions": [],
        "current_screen_index": 0,
        "user_feedback": "Add a data table with sorting",
    }

    with patch("src.langgraph.nodes.refine_design.should_trigger_library_search") as mock_trigger, \
         patch("src.langgraph.nodes.refine_design.extract_search_query") as mock_extract_query, \
         patch("src.langgraph.nodes.refine_design.get_category_from_feedback") as mock_get_category, \
         patch("src.langgraph.nodes.refine_design.discover_libraries", new_callable=AsyncMock) as mock_discover, \
         patch("src.langgraph.nodes.refine_design.create_library_options_message") as mock_create_msg:

        # Trigger library search
        mock_trigger.return_value = True
        mock_extract_query.return_value = "data table"
        mock_get_category.return_value = "ui_components"

        # Mock library discovery result
        mock_discover.return_value = {
            "success": True,
            "libraries": [
                {
                    "library_name": "TanStack Table",
                    "ranking_score": 95.5,
                    "github_url": "https://github.com/TanStack/table",
                    "stars": 22000,
                    "license": "MIT",
                },
                {
                    "library_name": "AG Grid",
                    "ranking_score": 90.0,
                    "github_url": "https://github.com/ag-grid/ag-grid",
                    "stars": 10000,
                    "license": "MIT",
                },
            ],
            "formatted_text": "🔍 Found 2 libraries...",
        }

        mock_create_msg.return_value = {"type": "library_options", "libraries": []}

        result = await refine_design(state)

        # Should enter library selection mode
        assert result["awaiting_library_selection"] is True
        assert len(result["pending_library_options"]) == 2
        assert result["pending_library_query"] == "data table"
        assert result["pending_library_category"] == "ui_components"
        assert result["user_feedback"] is None

        # Should call discovery
        mock_discover.assert_called_once()


@pytest.mark.asyncio
async def test_refine_design_library_selection():
    """Test user selecting a library from options."""
    state: DesignAgentState = {
        "job_id": "test-job-lib-select",
        "prd_content": "# Test PRD",
        "trd_content": "# Test TRD",
        "extracted_screens": ["Dashboard"],
        "selected_designs": {"Dashboard": SAMPLE_ASCII},
        "design_decisions": [],
        "current_screen_index": 0,
        "selected_open_source": [],
        "awaiting_library_selection": True,
        "pending_library_options": [
            {
                "library_name": "TanStack Table",
                "ranking_score": 95.5,
                "github_url": "https://github.com/TanStack/table",
                "stars": 22000,
                "license": "MIT",
                "category": "ui_components",
            }
        ],
        "pending_library_query": "data table",
        "pending_library_category": "ui_components",
        "user_feedback": "1",  # Select first option
    }

    with patch("src.langgraph.nodes.refine_design.handle_library_selection", new_callable=AsyncMock) as mock_handle, \
         patch("src.langgraph.nodes.refine_design.store_library_selection", new_callable=AsyncMock) as mock_store:

        # Mock selection handler
        mock_handle.return_value = {
            "selection_result": {
                "selected": True,
                "library": {
                    "library_name": "TanStack Table",
                    "stars": 22000,
                    "license": "MIT",
                },
            },
            "state_update": {
                "selected_open_source": {
                    "library_name": "TanStack Table",
                    "github_url": "https://github.com/TanStack/table",
                    "stars": 22000,
                    "license": "MIT",
                    "category": "ui_components",
                    "ranking_score": 95.5,
                    "rationale": "Selected by user",
                }
            },
            "websocket_message": {"type": "library_selected", "library": "TanStack Table"},
        }

        result = await refine_design(state)

        # Should add library to selected_open_source
        assert len(result["selected_open_source"]) == 1
        assert result["selected_open_source"][0]["library_name"] == "TanStack Table"

        # Should clear library selection state
        assert result["awaiting_library_selection"] is False
        assert result["pending_library_options"] == []
        assert result["awaiting_feedback"] is True

        # Should store in database
        mock_store.assert_called_once()


@pytest.mark.asyncio
async def test_refine_design_library_skip():
    """Test user skipping library selection."""
    state: DesignAgentState = {
        "job_id": "test-job-lib-skip",
        "prd_content": "# Test PRD",
        "trd_content": "# Test TRD",
        "extracted_screens": ["Dashboard"],
        "selected_designs": {"Dashboard": SAMPLE_ASCII},
        "design_decisions": [],
        "current_screen_index": 0,
        "selected_open_source": [],
        "awaiting_library_selection": True,
        "pending_library_options": [{"library_name": "Test Lib"}],
        "pending_library_query": "test",
        "pending_library_category": "ui_components",
        "user_feedback": "skip",
    }

    with patch("src.langgraph.nodes.refine_design.handle_library_selection", new_callable=AsyncMock) as mock_handle, \
         patch("src.langgraph.nodes.refine_design.store_library_selection", new_callable=AsyncMock) as mock_store:

        # Mock skip response
        mock_handle.return_value = {
            "selection_result": {"selected": False, "skipped": True},
            "state_update": {},
            "websocket_message": {"type": "library_skipped"},
        }

        result = await refine_design(state)

        # Should clear library selection state without adding
        assert len(result["selected_open_source"]) == 0
        assert result["awaiting_library_selection"] is False

        # Should NOT store in database
        mock_store.assert_not_called()


@pytest.mark.asyncio
async def test_refine_design_all_screens_complete():
    """Test behavior when current_screen_index >= total screens."""
    state: DesignAgentState = {
        "job_id": "test-job-complete",
        "prd_content": "# Test PRD",
        "trd_content": "# Test TRD",
        "extracted_screens": ["Login", "Dashboard"],
        "selected_designs": {"Login": SAMPLE_ASCII, "Dashboard": "..."},
        "design_decisions": [],
        "current_screen_index": 2,  # >= len(extracted_screens)
        "user_feedback": None,
    }

    result = await refine_design(state)

    # Should mark refinement as complete
    assert result["refinement_complete"] is True
    assert result["phase_name"] == "All Designs Approved"
    assert result["progress_percent"] == 65.0


@pytest.mark.asyncio
async def test_refine_design_error_handling():
    """Test error handling when LLM fails."""
    state: DesignAgentState = {
        "job_id": "test-job-error",
        "prd_content": "# Test PRD",
        "trd_content": "# Test TRD",
        "extracted_screens": ["Login"],
        "selected_designs": {"Login": SAMPLE_ASCII},
        "design_decisions": [],
        "current_screen_index": 0,
        "user_feedback": "Change button color",
    }

    with patch("src.langgraph.nodes.refine_design.llm_client.complete", new_callable=AsyncMock) as mock_llm, \
         patch("src.langgraph.nodes.refine_design.should_trigger_library_search") as mock_trigger:

        mock_trigger.return_value = False
        mock_llm.side_effect = Exception("LLM timeout")

        result = await refine_design(state)

        # Should have error in state
        assert "errors" in result
        assert len(result["errors"]) > 0
        assert "Design refinement failed" in result["errors"][0]
        assert result["should_retry"] is True


@pytest.mark.asyncio
async def test_should_continue_refining_complete():
    """Test conditional edge when refinement is complete."""
    state: DesignAgentState = {
        "extracted_screens": ["Login", "Dashboard"],
        "current_screen_index": 2,
        "refinement_complete": True,
    }

    result = should_continue_refining(state)
    assert result == "complete"


@pytest.mark.asyncio
async def test_should_continue_refining_continue():
    """Test conditional edge when refinement should continue."""
    state: DesignAgentState = {
        "extracted_screens": ["Login", "Dashboard", "Settings"],
        "current_screen_index": 1,
        "refinement_complete": False,
    }

    result = should_continue_refining(state)
    assert result == "continue"


@pytest.mark.asyncio
async def test_refine_design_markdown_cleanup():
    """Test that markdown code blocks are removed from LLM refinement output."""
    state: DesignAgentState = {
        "job_id": "test-job-markdown",
        "prd_content": "# Test PRD",
        "trd_content": "# Test TRD",
        "extracted_screens": ["Login"],
        "selected_designs": {"Login": SAMPLE_ASCII},
        "design_decisions": [],
        "current_screen_index": 0,
        "user_feedback": "Add a logo at the top",
    }

    with patch("src.langgraph.nodes.refine_design.llm_client.complete", new_callable=AsyncMock) as mock_llm, \
         patch("src.langgraph.nodes.refine_design.broadcast_ascii_ui_update", new_callable=AsyncMock), \
         patch("src.langgraph.nodes.refine_design.should_trigger_library_search") as mock_trigger:

        mock_trigger.return_value = False

        # LLM returns ASCII wrapped in markdown
        mock_llm.return_value = f"```ascii\n{SAMPLE_ASCII}\n```"

        result = await refine_design(state)

        # Verify code block markers removed
        refined_ui = result["selected_designs"]["Login"]
        assert "```" not in refined_ui


@pytest.mark.asyncio
async def test_refine_design_progress_calculation():
    """Test progress calculation during refinement."""
    for screen_index in [0, 1, 2, 3]:
        state: DesignAgentState = {
            "job_id": f"test-job-progress-{screen_index}",
            "prd_content": "# Test PRD",
            "trd_content": "# Test TRD",
            "extracted_screens": ["S1", "S2", "S3", "S4"],
            "selected_designs": {f"S{i+1}": "..." for i in range(4)},
            "design_decisions": [],
            "current_screen_index": screen_index,
            "user_feedback": "approve",
        }

        result = await refine_design(state)

        # Progress should be between 50% and 65%
        assert 50.0 <= result["progress_percent"] <= 65.0

        # Progress should increase with each screen
        expected_progress = 50.0 + (15.0 * (screen_index + 1) / 4)
        assert abs(result["progress_percent"] - expected_progress) < 0.1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
