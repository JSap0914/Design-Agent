"""
Unit tests for generate_options node (Phase 2).

Tests layout options generation with BMAD multiple-options principle.
"""

import pytest
from unittest.mock import AsyncMock, patch

from src.langgraph.nodes.generate_options import generate_options
from src.langgraph.state import DesignAgentState


@pytest.mark.asyncio
async def test_generate_options_basic():
    """Test basic layout options generation for multiple screens."""
    state: DesignAgentState = {
        "job_id": "test-job-1",
        "prd_content": "# Task Management App PRD\n\nUser authentication and task management",
        "trd_content": "# Technical Requirements\n\nReact + TypeScript",
        "extracted_screens": ["Login Screen", "Task List Screen", "Task Detail Screen"],
        "design_options": {},
        "current_phase": 1,
    }

    with patch("src.langgraph.nodes.generate_options.llm_client.complete_with_json", new_callable=AsyncMock) as mock_llm:
        # Mock LLM to return 3 options per screen
        mock_llm.return_value = {
            "options": [
                {
                    "option_number": 1,
                    "layout_description": "Centered card layout",
                    "key_features": ["Centered form", "Logo at top", "Social login buttons"],
                    "pros": ["Clean focus", "Mobile-friendly"],
                    "cons": ["Less content space"],
                    "recommended": True,
                },
                {
                    "option_number": 2,
                    "layout_description": "Split-screen layout",
                    "key_features": ["Left image panel", "Right form", "Brand messaging"],
                    "pros": ["Visual appeal", "Brand showcase"],
                    "cons": ["Not mobile-friendly"],
                    "recommended": False,
                },
                {
                    "option_number": 3,
                    "layout_description": "Full-width minimalist",
                    "key_features": ["Full-width form", "Minimal chrome", "Focus on inputs"],
                    "pros": ["Maximum screen use", "Distraction-free"],
                    "cons": ["May feel empty"],
                    "recommended": False,
                },
            ]
        }

        result = await generate_options(state)

        # Verify phase progression
        assert result["current_phase"] == 2
        assert result["phase_name"] == "Layout Options Generated"
        assert result["progress_percent"] > 15.0  # Should be around 35%

        # Verify options generated for all screens
        assert "design_options" in result
        assert len(result["design_options"]) == 3
        assert "Login Screen" in result["design_options"]
        assert "Task List Screen" in result["design_options"]
        assert "Task Detail Screen" in result["design_options"]

        # Verify each screen has 3 options
        for screen_name, options in result["design_options"].items():
            assert len(options) == 3
            assert all("Option" in opt for opt in options)

        # Verify metadata stored
        assert "design_options_metadata" in result
        assert len(result["design_options_metadata"]) == 3

        # Verify total options count
        assert result["options_provided_count"] == 9  # 3 screens × 3 options

        # Verify LLM called 3 times (once per screen)
        assert mock_llm.call_count == 3


@pytest.mark.asyncio
async def test_generate_options_minimum_enforcement():
    """Test that minimum 2 options are enforced (BMAD principle)."""
    state: DesignAgentState = {
        "job_id": "test-job-min",
        "prd_content": "# Test PRD",
        "trd_content": "# Test TRD",
        "extracted_screens": ["Login Screen"],
        "design_options": {},
        "current_phase": 1,
    }

    with patch("src.langgraph.nodes.generate_options.llm_client.complete_with_json", new_callable=AsyncMock) as mock_llm:
        # LLM returns only 1 option (violates BMAD)
        mock_llm.return_value = {
            "options": [
                {
                    "option_number": 1,
                    "layout_description": "Single option layout",
                    "key_features": ["Header", "Content"],
                    "pros": ["Simple"],
                    "cons": ["Not enough variety"],
                    "recommended": True,
                }
            ]
        }

        result = await generate_options(state)

        # Should have added a fallback option to reach minimum of 2
        assert len(result["design_options"]["Login Screen"]) >= 2
        assert "Standard layout" in result["design_options"]["Login Screen"][1]


@pytest.mark.asyncio
async def test_generate_options_maximum_enforcement():
    """Test that maximum 3 options are enforced."""
    state: DesignAgentState = {
        "job_id": "test-job-max",
        "prd_content": "# Test PRD",
        "trd_content": "# Test TRD",
        "extracted_screens": ["Dashboard"],
        "design_options": {},
        "current_phase": 1,
    }

    with patch("src.langgraph.nodes.generate_options.llm_client.complete_with_json", new_callable=AsyncMock) as mock_llm:
        # LLM returns 5 options (exceeds max)
        mock_llm.return_value = {
            "options": [
                {
                    "option_number": i,
                    "layout_description": f"Layout option {i}",
                    "key_features": ["Feature"],
                    "pros": ["Pro"],
                    "cons": ["Con"],
                    "recommended": i == 1,
                }
                for i in range(1, 6)  # 5 options
            ]
        }

        result = await generate_options(state)

        # Should have limited to max of 3
        assert len(result["design_options"]["Dashboard"]) == 3


@pytest.mark.asyncio
async def test_generate_options_multiple_screens():
    """Test options generation for multiple screens in sequence."""
    state: DesignAgentState = {
        "job_id": "test-job-multi",
        "prd_content": "# E-commerce App PRD",
        "trd_content": "# Tech Stack: React + TypeScript",
        "extracted_screens": [
            "Home Screen",
            "Product Listing",
            "Product Detail",
            "Shopping Cart",
            "Checkout",
        ],
        "design_options": {},
        "current_phase": 1,
    }

    with patch("src.langgraph.nodes.generate_options.llm_client.complete_with_json", new_callable=AsyncMock) as mock_llm:
        # Return different options for each screen
        def mock_response(*args, **kwargs):
            return {
                "options": [
                    {
                        "option_number": i,
                        "layout_description": f"Option {i}",
                        "key_features": [f"Feature {i}"],
                        "pros": [f"Pro {i}"],
                        "cons": [f"Con {i}"],
                        "recommended": i == 1,
                    }
                    for i in range(1, 4)  # 3 options per screen
                ]
            }

        mock_llm.side_effect = mock_response

        result = await generate_options(state)

        # Verify all 5 screens have options
        assert len(result["design_options"]) == 5
        assert all(len(opts) == 3 for opts in result["design_options"].values())

        # Verify LLM called 5 times
        assert mock_llm.call_count == 5

        # Verify total options count
        assert result["options_provided_count"] == 15  # 5 screens × 3 options


@pytest.mark.asyncio
async def test_generate_options_error_handling():
    """Test error handling when LLM fails."""
    state: DesignAgentState = {
        "job_id": "test-job-error",
        "prd_content": "# Test PRD",
        "trd_content": "# Test TRD",
        "extracted_screens": ["Login Screen"],
        "design_options": {},
        "current_phase": 1,
    }

    with patch("src.langgraph.nodes.generate_options.llm_client.complete_with_json", new_callable=AsyncMock) as mock_llm:
        mock_llm.side_effect = Exception("LLM API timeout")

        result = await generate_options(state)

        # Should have error in state
        assert "errors" in result
        assert len(result["errors"]) > 0
        assert "Layout options generation failed" in result["errors"][0]
        assert "should_retry" in result
        assert result["should_retry"] is True
        assert result["retry_count"] == 1


@pytest.mark.asyncio
async def test_generate_options_preserves_state():
    """Test that generate_options preserves other state fields."""
    state: DesignAgentState = {
        "job_id": "test-job-preserve",
        "prd_content": "# Test PRD",
        "trd_content": "# Test TRD",
        "extracted_screens": ["Screen 1"],
        "design_options": {},
        "current_phase": 1,
        # Additional fields that should be preserved
        "project_id": "proj-123",
        "user_id": "user-456",
        "created_at": "2025-01-13T10:00:00Z",
        "custom_field": "should_be_preserved",
    }

    with patch("src.langgraph.nodes.generate_options.llm_client.complete_with_json", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = {
            "options": [
                {
                    "option_number": 1,
                    "layout_description": "Test layout",
                    "key_features": ["Feature"],
                    "pros": ["Pro"],
                    "cons": ["Con"],
                    "recommended": True,
                },
                {
                    "option_number": 2,
                    "layout_description": "Test layout 2",
                    "key_features": ["Feature"],
                    "pros": ["Pro"],
                    "cons": ["Con"],
                    "recommended": False,
                },
            ]
        }

        result = await generate_options(state)

        # Verify original fields preserved
        assert result["job_id"] == "test-job-preserve"
        assert result["project_id"] == "proj-123"
        assert result["user_id"] == "user-456"
        assert result["created_at"] == "2025-01-13T10:00:00Z"
        assert result["custom_field"] == "should_be_preserved"


@pytest.mark.asyncio
async def test_generate_options_progress_calculation():
    """Test progress percent calculation."""
    # Test with different screen counts
    for screen_count in [3, 5, 8, 12]:
        state: DesignAgentState = {
            "job_id": f"test-job-progress-{screen_count}",
            "prd_content": "# Test PRD",
            "trd_content": "# Test TRD",
            "extracted_screens": [f"Screen {i}" for i in range(screen_count)],
            "design_options": {},
            "current_phase": 1,
        }

        with patch("src.langgraph.nodes.generate_options.llm_client.complete_with_json", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = {
                "options": [
                    {
                        "option_number": 1,
                        "layout_description": "Test",
                        "key_features": ["F"],
                        "pros": ["P"],
                        "cons": ["C"],
                        "recommended": True,
                    },
                    {
                        "option_number": 2,
                        "layout_description": "Test 2",
                        "key_features": ["F"],
                        "pros": ["P"],
                        "cons": ["C"],
                        "recommended": False,
                    },
                ]
            }

            result = await generate_options(state)

            # Progress should be between 15% (start of Phase 2) and 35% (end of Phase 2)
            assert 15.0 < result["progress_percent"] <= 35.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
