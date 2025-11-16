"""
Unit tests for create_ascii_ui node (Phase 3).

Tests ASCII mockup generation with validation and WebSocket broadcasting.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from src.langgraph.nodes.create_ascii_ui import create_ascii_ui
from src.langgraph.state import DesignAgentState


SAMPLE_ASCII_MOBILE = """┌──────────────────────────────────────┐
│  📱 MyApp                    ☰       │
├──────────────────────────────────────┤
│                                      │
│  Welcome back!                       │
│                                      │
│  Email                               │
│  [___________________________]       │
│                                      │
│  Password                            │
│  [___________________________]       │
│                                      │
│         [    Sign In    ]            │
│                                      │
└──────────────────────────────────────┘"""

SAMPLE_ASCII_WEB = """┌──────────────────────────────────────────────────────────────────────────────┐
│  🏠 Home    📋 Tasks    👤 Profile    ⚙️ Settings                             │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Dashboard                                                                   │
│                                                                              │
│  ┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐ │
│  │  📊 Active Tasks    │  │  ✅ Completed       │  │  ⏳ In Progress     │ │
│  │                     │  │                     │  │                     │ │
│  │       42            │  │       128           │  │       15            │ │
│  └─────────────────────┘  └─────────────────────┘  └─────────────────────┘ │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘"""


@pytest.mark.asyncio
async def test_create_ascii_ui_basic():
    """Test basic ASCII UI creation for multiple screens."""
    state: DesignAgentState = {
        "job_id": "test-job-1",
        "prd_content": "# Task Management App PRD",
        "trd_content": "# Technical Requirements\n\nMobile app for iOS and Android",
        "extracted_screens": ["Login Screen", "Dashboard", "Task List"],
        "design_options_metadata": {
            "Login Screen": [
                {
                    "option_number": 1,
                    "layout_description": "Centered card layout with social login",
                    "key_features": ["Centered form", "Logo", "Social buttons"],
                },
                {
                    "option_number": 2,
                    "layout_description": "Split-screen layout",
                    "key_features": ["Image", "Form"],
                },
            ],
            "Dashboard": [
                {
                    "option_number": 1,
                    "layout_description": "Grid dashboard with metrics cards",
                    "key_features": ["Metric cards", "Charts"],
                }
            ],
            "Task List": [
                {
                    "option_number": 1,
                    "layout_description": "List view with filters",
                    "key_features": ["Search bar", "Task cards", "Filters"],
                }
            ],
        },
        "current_phase": 2,
    }

    with patch("src.langgraph.nodes.create_ascii_ui.llm_client.complete", new_callable=AsyncMock) as mock_llm, \
         patch("src.langgraph.nodes.create_ascii_ui.broadcast_ascii_ui_update", new_callable=AsyncMock) as mock_broadcast, \
         patch("src.langgraph.nodes.create_ascii_ui.ASCIIUIGenerator") as mock_generator_class:

        # Mock LLM to return sample ASCII
        mock_llm.return_value = SAMPLE_ASCII_MOBILE

        # Mock ASCII validator
        mock_generator = MagicMock()
        mock_generator.validate_ascii_ui.return_value = (True, [])
        mock_generator_class.return_value = mock_generator

        result = await create_ascii_ui(state)

        # Verify phase progression
        assert result["current_phase"] == 3
        assert result["phase_name"] == "ASCII UI Created (Ready for Refinement)"
        assert 35.0 < result["progress_percent"] <= 50.0

        # Verify ASCII UIs created for all screens
        assert "selected_designs" in result
        assert len(result["selected_designs"]) == 3
        assert "Login Screen" in result["selected_designs"]
        assert "Dashboard" in result["selected_designs"]
        assert "Task List" in result["selected_designs"]

        # Verify design decisions recorded
        assert "design_decisions" in result
        assert len(result["design_decisions"]) == 3
        assert all(d["decision_type"] == "initial_layout" for d in result["design_decisions"])

        # Verify completed screens count
        assert result["completed_screens"] == 3

        # Verify LLM called 3 times
        assert mock_llm.call_count == 3

        # Verify WebSocket broadcasts
        assert mock_broadcast.call_count == 3

        # Verify validator called
        assert mock_generator.validate_ascii_ui.call_count == 3


@pytest.mark.asyncio
async def test_create_ascii_ui_platform_detection():
    """Test platform detection from TRD (mobile vs web)."""
    # Test mobile detection
    mobile_state: DesignAgentState = {
        "job_id": "test-job-mobile",
        "prd_content": "# App PRD",
        "trd_content": "# Technical Requirements\n\nMobile app for iOS",
        "extracted_screens": ["Home"],
        "design_options_metadata": {
            "Home": [
                {
                    "option_number": 1,
                    "layout_description": "Mobile home layout",
                    "key_features": ["Navigation"],
                }
            ]
        },
        "current_phase": 2,
    }

    with patch("src.langgraph.nodes.create_ascii_ui.llm_client.complete", new_callable=AsyncMock) as mock_llm, \
         patch("src.langgraph.nodes.create_ascii_ui.broadcast_ascii_ui_update", new_callable=AsyncMock), \
         patch("src.langgraph.nodes.create_ascii_ui.ASCIIUIGenerator") as mock_generator_class:

        mock_llm.return_value = SAMPLE_ASCII_MOBILE
        mock_generator = MagicMock()
        mock_generator.validate_ascii_ui.return_value = (True, [])
        mock_generator_class.return_value = mock_generator

        result = await create_ascii_ui(mobile_state)

        # Verify mobile platform was used
        mock_generator_class.assert_called_with(platform="mobile")
        assert "selected_designs" in result

    # Test web detection
    web_state: DesignAgentState = {
        "job_id": "test-job-web",
        "prd_content": "# Web App PRD",
        "trd_content": "# Technical Requirements\n\nReact web application",
        "extracted_screens": ["Dashboard"],
        "design_options_metadata": {
            "Dashboard": [
                {
                    "option_number": 1,
                    "layout_description": "Web dashboard layout",
                    "key_features": ["Charts"],
                }
            ]
        },
        "current_phase": 2,
    }

    with patch("src.langgraph.nodes.create_ascii_ui.llm_client.complete", new_callable=AsyncMock) as mock_llm, \
         patch("src.langgraph.nodes.create_ascii_ui.broadcast_ascii_ui_update", new_callable=AsyncMock), \
         patch("src.langgraph.nodes.create_ascii_ui.ASCIIUIGenerator") as mock_generator_class:

        mock_llm.return_value = SAMPLE_ASCII_WEB
        mock_generator = MagicMock()
        mock_generator.validate_ascii_ui.return_value = (True, [])
        mock_generator_class.return_value = mock_generator

        result = await create_ascii_ui(web_state)

        # Verify web platform was used (default)
        mock_generator_class.assert_called_with(platform="web")


@pytest.mark.asyncio
async def test_create_ascii_ui_markdown_cleanup():
    """Test that markdown code blocks are removed from LLM output."""
    state: DesignAgentState = {
        "job_id": "test-job-markdown",
        "prd_content": "# Test PRD",
        "trd_content": "# Test TRD",
        "extracted_screens": ["Login"],
        "design_options_metadata": {
            "Login": [
                {
                    "option_number": 1,
                    "layout_description": "Simple login",
                    "key_features": ["Form"],
                }
            ]
        },
        "current_phase": 2,
    }

    with patch("src.langgraph.nodes.create_ascii_ui.llm_client.complete", new_callable=AsyncMock) as mock_llm, \
         patch("src.langgraph.nodes.create_ascii_ui.broadcast_ascii_ui_update", new_callable=AsyncMock), \
         patch("src.langgraph.nodes.create_ascii_ui.ASCIIUIGenerator") as mock_generator_class:

        # LLM returns ASCII wrapped in markdown code block
        mock_llm.return_value = f"```ascii\n{SAMPLE_ASCII_MOBILE}\n```"

        mock_generator = MagicMock()
        mock_generator.validate_ascii_ui.return_value = (True, [])
        mock_generator_class.return_value = mock_generator

        result = await create_ascii_ui(state)

        # Verify code block markers removed
        ascii_ui = result["selected_designs"]["Login"]
        assert "```" not in ascii_ui
        assert "ascii" not in ascii_ui or ascii_ui.count("ascii") < 2  # May contain "ascii" in content


@pytest.mark.asyncio
async def test_create_ascii_ui_validation_failure():
    """Test handling of ASCII UI validation failures."""
    state: DesignAgentState = {
        "job_id": "test-job-validation",
        "prd_content": "# Test PRD",
        "trd_content": "# Test TRD",
        "extracted_screens": ["Screen1"],
        "design_options_metadata": {
            "Screen1": [
                {
                    "option_number": 1,
                    "layout_description": "Test layout",
                    "key_features": ["Test"],
                }
            ]
        },
        "current_phase": 2,
    }

    with patch("src.langgraph.nodes.create_ascii_ui.llm_client.complete", new_callable=AsyncMock) as mock_llm, \
         patch("src.langgraph.nodes.create_ascii_ui.broadcast_ascii_ui_update", new_callable=AsyncMock), \
         patch("src.langgraph.nodes.create_ascii_ui.ASCIIUIGenerator") as mock_generator_class:

        # LLM returns invalid ASCII (too narrow)
        mock_llm.return_value = "┌─┐\n│X│\n└─┘"

        # Mock validator to return failure
        mock_generator = MagicMock()
        mock_generator.validate_ascii_ui.return_value = (False, ["Width must be 40 or 80 characters"])
        mock_generator_class.return_value = mock_generator

        result = await create_ascii_ui(state)

        # Should still create design (best effort), but log warning
        assert "selected_designs" in result
        assert "Screen1" in result["selected_designs"]


@pytest.mark.asyncio
async def test_create_ascii_ui_missing_options():
    """Test handling when screen has no layout options."""
    state: DesignAgentState = {
        "job_id": "test-job-missing",
        "prd_content": "# Test PRD",
        "trd_content": "# Test TRD",
        "extracted_screens": ["Screen1", "Screen2"],
        "design_options_metadata": {
            "Screen1": [
                {
                    "option_number": 1,
                    "layout_description": "Valid layout",
                    "key_features": ["Test"],
                }
            ],
            # Screen2 missing
        },
        "current_phase": 2,
    }

    with patch("src.langgraph.nodes.create_ascii_ui.llm_client.complete", new_callable=AsyncMock) as mock_llm, \
         patch("src.langgraph.nodes.create_ascii_ui.broadcast_ascii_ui_update", new_callable=AsyncMock), \
         patch("src.langgraph.nodes.create_ascii_ui.ASCIIUIGenerator") as mock_generator_class:

        mock_llm.return_value = SAMPLE_ASCII_MOBILE
        mock_generator = MagicMock()
        mock_generator.validate_ascii_ui.return_value = (True, [])
        mock_generator_class.return_value = mock_generator

        result = await create_ascii_ui(state)

        # Should only create ASCII for Screen1
        assert len(result["selected_designs"]) == 1
        assert "Screen1" in result["selected_designs"]
        assert "Screen2" not in result["selected_designs"]


@pytest.mark.asyncio
async def test_create_ascii_ui_error_handling():
    """Test error handling when LLM fails."""
    state: DesignAgentState = {
        "job_id": "test-job-error",
        "prd_content": "# Test PRD",
        "trd_content": "# Test TRD",
        "extracted_screens": ["Login"],
        "design_options_metadata": {
            "Login": [
                {
                    "option_number": 1,
                    "layout_description": "Test layout",
                    "key_features": ["Test"],
                }
            ]
        },
        "current_phase": 2,
    }

    with patch("src.langgraph.nodes.create_ascii_ui.llm_client.complete", new_callable=AsyncMock) as mock_llm, \
         patch("src.langgraph.nodes.create_ascii_ui.broadcast_ascii_ui_update", new_callable=AsyncMock):

        mock_llm.side_effect = Exception("LLM timeout")

        result = await create_ascii_ui(state)

        # Should have error in state
        assert "errors" in result
        assert len(result["errors"]) > 0
        assert "ASCII UI creation failed" in result["errors"][0]
        assert result["should_retry"] is True
        assert result["retry_count"] == 1


@pytest.mark.asyncio
async def test_create_ascii_ui_design_decisions():
    """Test that design decisions are properly recorded."""
    state: DesignAgentState = {
        "job_id": "test-job-decisions",
        "prd_content": "# Test PRD",
        "trd_content": "# Test TRD",
        "extracted_screens": ["Login"],
        "design_options_metadata": {
            "Login": [
                {
                    "option_number": 1,
                    "layout_description": "Centered card layout",
                    "key_features": ["Card", "Center"],
                },
                {
                    "option_number": 2,
                    "layout_description": "Split-screen layout",
                    "key_features": ["Split", "Image"],
                },
                {
                    "option_number": 3,
                    "layout_description": "Full-width layout",
                    "key_features": ["Full-width"],
                },
            ]
        },
        "design_decisions": [],
        "current_phase": 2,
    }

    with patch("src.langgraph.nodes.create_ascii_ui.llm_client.complete", new_callable=AsyncMock) as mock_llm, \
         patch("src.langgraph.nodes.create_ascii_ui.broadcast_ascii_ui_update", new_callable=AsyncMock), \
         patch("src.langgraph.nodes.create_ascii_ui.ASCIIUIGenerator") as mock_generator_class:

        mock_llm.return_value = SAMPLE_ASCII_MOBILE
        mock_generator = MagicMock()
        mock_generator.validate_ascii_ui.return_value = (True, [])
        mock_generator_class.return_value = mock_generator

        result = await create_ascii_ui(state)

        # Verify decision recorded
        decisions = result["design_decisions"]
        assert len(decisions) == 1

        decision = decisions[0]
        assert decision["screen_name"] == "Login"
        assert decision["decision_type"] == "initial_layout"
        assert "Centered card layout" in decision["rationale"]
        assert decision["user_feedback"] is None

        # Verify alternatives recorded
        assert len(decision["alternatives"]) == 3
        assert any("Centered card" in alt for alt in decision["alternatives"])
        assert any("Split-screen" in alt for alt in decision["alternatives"])


@pytest.mark.asyncio
async def test_create_ascii_ui_progress_calculation():
    """Test progress percent calculation."""
    for screen_count in [3, 5, 8]:
        state: DesignAgentState = {
            "job_id": f"test-job-progress-{screen_count}",
            "prd_content": "# Test PRD",
            "trd_content": "# Test TRD",
            "extracted_screens": [f"Screen {i}" for i in range(screen_count)],
            "design_options_metadata": {
                f"Screen {i}": [
                    {
                        "option_number": 1,
                        "layout_description": f"Layout {i}",
                        "key_features": ["Test"],
                    }
                ]
                for i in range(screen_count)
            },
            "current_phase": 2,
        }

        with patch("src.langgraph.nodes.create_ascii_ui.llm_client.complete", new_callable=AsyncMock) as mock_llm, \
             patch("src.langgraph.nodes.create_ascii_ui.broadcast_ascii_ui_update", new_callable=AsyncMock), \
             patch("src.langgraph.nodes.create_ascii_ui.ASCIIUIGenerator") as mock_generator_class:

            mock_llm.return_value = SAMPLE_ASCII_MOBILE
            mock_generator = MagicMock()
            mock_generator.validate_ascii_ui.return_value = (True, [])
            mock_generator_class.return_value = mock_generator

            result = await create_ascii_ui(state)

            # Progress should be between 35% (start) and 50% (end)
            assert 35.0 < result["progress_percent"] <= 50.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
