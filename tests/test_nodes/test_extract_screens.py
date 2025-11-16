"""
Unit tests for extract_screens node (Phase 1).

Tests screen extraction from PRD/TRD documents.
"""

import pytest
from unittest.mock import AsyncMock, patch

from src.langgraph.nodes.extract_screens import extract_screens
from src.langgraph.state import DesignAgentState


@pytest.mark.asyncio
async def test_extract_screens_basic():
    """Test basic screen extraction with valid PRD."""
    state: DesignAgentState = {
        "job_id": "test-job-1",
        "prd_content": """# Task Management App PRD

## Screens
1. Login Screen - User authentication
2. Task List Screen - Display all tasks
3. Task Detail Screen - View/edit task details
4. Create Task Screen - Add new task
""",
        "trd_content": "# Technical Requirements\n\nReact + TypeScript",
        "extracted_screens": [],
        "current_phase": 0,
    }

    with patch("src.langgraph.nodes.extract_screens.generate_json_async", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = {
            "screens": [
                "Login Screen",
                "Task List Screen",
                "Task Detail Screen",
                "Create Task Screen"
            ],
            "rationale": "Four main screens identified for complete task management workflow"
        }

        result = await extract_screens(state)

        assert result["current_phase"] == 1
        assert result["phase_name"] == "Screen Extraction"
        assert len(result["extracted_screens"]) == 4
        assert "Login Screen" in result["extracted_screens"]
        assert "Task List Screen" in result["extracted_screens"]


@pytest.mark.asyncio
async def test_extract_screens_minimum():
    """Test that at least MIN_SCREENS are extracted."""
    state: DesignAgentState = {
        "job_id": "test-job-min",
        "prd_content": "# Simple App\n\nJust a login screen",
        "trd_content": "# Tech\n\nReact",
        "extracted_screens": [],
        "current_phase": 0,
    }

    with patch("src.langgraph.nodes.extract_screens.generate_json_async", new_callable=AsyncMock) as mock_llm:
        # LLM returns only 1 screen
        mock_llm.return_value = {
            "screens": ["Login Screen"],
            "rationale": "Only one screen mentioned"
        }

        result = await extract_screens(state)

        # Should have at least MIN_SCREENS (3 from config)
        assert len(result["extracted_screens"]) >= 3


@pytest.mark.asyncio
async def test_extract_screens_maximum():
    """Test that no more than MAX_SCREENS are extracted."""
    state: DesignAgentState = {
        "job_id": "test-job-max",
        "prd_content": "# Complex App\n\n" + "\n".join([f"Screen {i}" for i in range(20)]),
        "trd_content": "# Tech\n\nReact",
        "extracted_screens": [],
        "current_phase": 0,
    }

    with patch("src.langgraph.nodes.extract_screens.generate_json_async", new_callable=AsyncMock) as mock_llm:
        # LLM returns 20 screens
        mock_llm.return_value = {
            "screens": [f"Screen {i}" for i in range(20)],
            "rationale": "Many screens identified"
        }

        result = await extract_screens(state)

        # Should have no more than MAX_SCREENS (12 from config)
        assert len(result["extracted_screens"]) <= 12


@pytest.mark.asyncio
async def test_extract_screens_error_handling():
    """Test error handling when LLM fails."""
    state: DesignAgentState = {
        "job_id": "test-job-error",
        "prd_content": "# Test PRD",
        "trd_content": "# Test TRD",
        "extracted_screens": [],
        "current_phase": 0,
    }

    with patch("src.langgraph.nodes.extract_screens.generate_json_async", new_callable=AsyncMock) as mock_llm:
        mock_llm.side_effect = Exception("LLM API error")

        result = await extract_screens(state)

        assert "error" in result
        assert "LLM API error" in result["error"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
