"""
Unit tests for generate_design_system node (Phase 4).

Tests Design System extraction from approved ASCII UI designs.
"""

import pytest
from unittest.mock import AsyncMock, patch

from src.langgraph.nodes.generate_design_system import (
    generate_design_system,
    _create_default_design_system,
    _validate_design_system,
)
from src.langgraph.state import DesignAgentState


@pytest.mark.asyncio
async def test_generate_design_system_basic():
    """Test basic Design System extraction from approved designs."""
    state: DesignAgentState = {
        "job_id": "test-job-1",
        "selected_designs": {
            "Login": "ASCII UI for Login...",
            "Dashboard": "ASCII UI for Dashboard...",
            "Settings": "ASCII UI for Settings...",
        },
        "design_decisions": [
            {
                "screen_name": "Login",
                "decision_type": "initial_layout",
                "rationale": "Centered card layout",
            }
        ],
        "selected_open_source": [
            {
                "library_name": "TanStack Table",
                "category": "ui_components",
            }
        ],
        "current_phase": 3,
    }

    with patch("src.langgraph.nodes.generate_design_system.llm_client.complete_with_json", new_callable=AsyncMock) as mock_llm:
        # Mock LLM response
        mock_llm.return_value = {
            "colors": {
                "primary": ["#3B82F6", "#2563EB"],
                "secondary": ["#8B5CF6"],
                "semantic": {
                    "success": "#10B981",
                    "error": "#EF4444",
                },
            },
            "typography": {
                "font_families": {
                    "primary": "Inter, sans-serif",
                },
                "sizes": {
                    "base": "16px",
                    "lg": "18px",
                },
            },
            "spacing": {
                "scale": "8pt grid",
                "values": {
                    "2": "8px",
                    "4": "16px",
                },
            },
            "border_radius": {
                "base": "8px",
            },
            "shadows": {
                "sm": "0 1px 2px rgba(0,0,0,0.05)",
            },
            "icons": {
                "style": "outline",
                "size": "24px",
            },
            "component_libraries": ["TanStack Table"],
        }

        result = await generate_design_system(state)

        # Verify phase progression
        assert result["current_phase"] == 4
        assert result["phase_name"] == "Design System Extracted"
        assert result["progress_percent"] == 70.0

        # Verify Design System created
        assert "design_system" in result
        design_system = result["design_system"]

        # Verify structure
        assert "colors" in design_system
        assert "typography" in design_system
        assert "spacing" in design_system
        assert "border_radius" in design_system
        assert "shadows" in design_system
        assert "icons" in design_system
        assert "component_libraries" in design_system

        # Verify colors
        assert len(design_system["colors"]["primary"]) >= 2
        assert design_system["colors"]["semantic"]["success"] == "#10B981"

        # Verify LLM was called
        mock_llm.assert_called_once()


@pytest.mark.asyncio
async def test_generate_design_system_with_library_integration():
    """Test Design System includes selected open-source libraries."""
    state: DesignAgentState = {
        "job_id": "test-job-libs",
        "selected_designs": {
            "Dashboard": "Dashboard with data table...",
        },
        "design_decisions": [],
        "selected_open_source": [
            {
                "library_name": "TanStack Table",
                "category": "ui_components",
                "github_url": "https://github.com/TanStack/table",
            },
            {
                "library_name": "React Hook Form",
                "category": "forms",
                "github_url": "https://github.com/react-hook-form/react-hook-form",
            },
        ],
        "current_phase": 3,
    }

    with patch("src.langgraph.nodes.generate_design_system.llm_client.complete_with_json", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = {
            "colors": {"primary": ["#3B82F6"]},
            "typography": {"sizes": {"base": "16px"}},
            "spacing": {"values": {"2": "8px"}},
            "border_radius": {"base": "8px"},
            "shadows": {"sm": "0 1px 2px rgba(0,0,0,0.05)"},
            "icons": {"style": "outline"},
            "component_libraries": ["TanStack Table", "React Hook Form"],
        }

        result = await generate_design_system(state)

        design_system = result["design_system"]
        assert len(design_system["component_libraries"]) == 2
        assert "TanStack Table" in design_system["component_libraries"]
        assert "React Hook Form" in design_system["component_libraries"]


@pytest.mark.asyncio
async def test_generate_design_system_empty_designs():
    """Test fallback to default Design System when no designs provided."""
    state: DesignAgentState = {
        "job_id": "test-job-empty",
        "selected_designs": {},  # No designs
        "design_decisions": [],
        "selected_open_source": [],
        "current_phase": 3,
    }

    result = await generate_design_system(state)

    # Should use default Design System
    assert "design_system" in result
    design_system = result["design_system"]

    # Verify default values
    assert design_system["colors"]["primary"] == ["#3B82F6", "#2563EB", "#1D4ED8"]
    assert design_system["typography"]["font_families"]["primary"] == "Inter, system-ui, -apple-system, sans-serif"
    assert design_system["spacing"]["scale"] == "8pt grid"


@pytest.mark.asyncio
async def test_generate_design_system_validation():
    """Test Design System validation with missing fields."""
    state: DesignAgentState = {
        "job_id": "test-job-validation",
        "selected_designs": {"Login": "Login UI..."},
        "design_decisions": [],
        "selected_open_source": [],
        "current_phase": 3,
    }

    with patch("src.langgraph.nodes.generate_design_system.llm_client.complete_with_json", new_callable=AsyncMock) as mock_llm:
        # LLM returns incomplete Design System (missing some fields)
        mock_llm.return_value = {
            "colors": {
                "primary": ["#FF0000"],
            },
            # Missing: typography, spacing, border_radius, shadows, icons
        }

        result = await generate_design_system(state)

        design_system = result["design_system"]

        # Should have all required fields (filled with defaults)
        assert "colors" in design_system
        assert "typography" in design_system  # Should be filled with defaults
        assert "spacing" in design_system
        assert "border_radius" in design_system
        assert "shadows" in design_system
        assert "icons" in design_system

        # Custom colors preserved
        assert design_system["colors"]["primary"] == ["#FF0000"]


@pytest.mark.asyncio
async def test_generate_design_system_error_handling():
    """Test error handling when LLM fails."""
    state: DesignAgentState = {
        "job_id": "test-job-error",
        "selected_designs": {"Login": "Login UI..."},
        "design_decisions": [],
        "selected_open_source": [],
        "current_phase": 3,
    }

    with patch("src.langgraph.nodes.generate_design_system.llm_client.complete_with_json", new_callable=AsyncMock) as mock_llm:
        mock_llm.side_effect = Exception("LLM API timeout")

        result = await generate_design_system(state)

        # Should have error in state
        assert "errors" in result
        assert len(result["errors"]) > 0
        assert "Design System extraction failed" in result["errors"][0]
        assert result["should_retry"] is True
        assert result["retry_count"] == 1


def test_create_default_design_system():
    """Test default Design System creation."""
    design_system = _create_default_design_system()

    # Verify structure
    assert "colors" in design_system
    assert "typography" in design_system
    assert "spacing" in design_system
    assert "border_radius" in design_system
    assert "shadows" in design_system
    assert "icons" in design_system
    assert "component_libraries" in design_system

    # Verify colors
    assert len(design_system["colors"]["primary"]) == 3
    assert len(design_system["colors"]["secondary"]) == 3
    assert "success" in design_system["colors"]["semantic"]
    assert "error" in design_system["colors"]["semantic"]
    assert "warning" in design_system["colors"]["semantic"]
    assert "gray" in design_system["colors"]["neutrals"]

    # Verify typography
    assert "Inter" in design_system["typography"]["font_families"]["primary"]
    assert design_system["typography"]["sizes"]["base"] == "16px"
    assert design_system["typography"]["weights"]["bold"] == "700"

    # Verify spacing
    assert design_system["spacing"]["scale"] == "8pt grid"
    assert design_system["spacing"]["values"]["4"] == "16px"

    # Verify border radius
    assert design_system["border_radius"]["base"] == "8px"
    assert design_system["border_radius"]["full"] == "9999px"

    # Verify shadows
    assert "sm" in design_system["shadows"]
    assert "lg" in design_system["shadows"]

    # Verify icons
    assert design_system["icons"]["size"] == "24px"
    assert design_system["icons"]["style"] == "outline"


def test_validate_design_system_complete():
    """Test validation with complete Design System."""
    input_json = {
        "colors": {"primary": ["#FF0000"]},
        "typography": {"sizes": {"base": "14px"}},
        "spacing": {"values": {"2": "8px"}},
        "border_radius": {"base": "4px"},
        "shadows": {"sm": "0 1px 2px rgba(0,0,0,0.1)"},
        "icons": {"size": "20px"},
        "component_libraries": ["Test Lib"],
    }

    validated = _validate_design_system(input_json)

    # Should preserve all fields
    assert validated["colors"]["primary"] == ["#FF0000"]
    assert validated["typography"]["sizes"]["base"] == "14px"
    assert validated["spacing"]["values"]["2"] == "8px"
    assert validated["border_radius"]["base"] == "4px"
    assert validated["component_libraries"] == ["Test Lib"]


def test_validate_design_system_partial():
    """Test validation with partial Design System (missing fields)."""
    input_json = {
        "colors": {"primary": ["#00FF00"]},
        # Missing all other fields
    }

    validated = _validate_design_system(input_json)

    # Should have custom colors
    assert validated["colors"]["primary"] == ["#00FF00"]

    # Should have default values for missing fields
    assert "typography" in validated
    assert "spacing" in validated
    assert "border_radius" in validated
    assert "shadows" in validated
    assert "icons" in validated

    # Default typography should be present
    assert "Inter" in validated["typography"]["font_families"]["primary"]


def test_validate_design_system_empty():
    """Test validation with empty Design System."""
    input_json = {}

    validated = _validate_design_system(input_json)

    # Should be identical to default Design System
    default = _create_default_design_system()

    assert validated["colors"] == default["colors"]
    assert validated["typography"] == default["typography"]
    assert validated["spacing"] == default["spacing"]


@pytest.mark.asyncio
async def test_generate_design_system_preserves_state():
    """Test that generate_design_system preserves other state fields."""
    state: DesignAgentState = {
        "job_id": "test-job-preserve",
        "project_id": "proj-123",
        "user_id": "user-456",
        "selected_designs": {"Login": "Login UI..."},
        "design_decisions": [],
        "selected_open_source": [],
        "current_phase": 3,
        "custom_field": "should_be_preserved",
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

        # Verify original fields preserved
        assert result["job_id"] == "test-job-preserve"
        assert result["project_id"] == "proj-123"
        assert result["user_id"] == "user-456"
        assert result["custom_field"] == "should_be_preserved"


@pytest.mark.asyncio
async def test_generate_design_system_temperature():
    """Test that LLM is called with low temperature for consistency."""
    state: DesignAgentState = {
        "job_id": "test-job-temp",
        "selected_designs": {"Login": "Login UI..."},
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

        await generate_design_system(state)

        # Verify temperature parameter
        call_kwargs = mock_llm.call_args.kwargs
        assert call_kwargs["temperature"] == 0.3


@pytest.mark.asyncio
async def test_generate_design_system_multiple_screens():
    """Test Design System extraction from multiple diverse screens."""
    state: DesignAgentState = {
        "job_id": "test-job-multi",
        "selected_designs": {
            "Login": "Centered form with blue button...",
            "Dashboard": "Grid layout with cards...",
            "Profile": "Avatar and form fields...",
            "Settings": "List of toggle switches...",
            "Notifications": "List of notification cards...",
        },
        "design_decisions": [],
        "selected_open_source": [],
        "current_phase": 3,
    }

    with patch("src.langgraph.nodes.generate_design_system.llm_client.complete_with_json", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = {
            "colors": {
                "primary": ["#3B82F6", "#2563EB", "#1D4ED8"],
                "secondary": ["#10B981"],
            },
            "typography": {
                "font_families": {"primary": "Inter, sans-serif"},
                "sizes": {"base": "16px", "lg": "20px"},
            },
            "spacing": {"values": {"2": "8px", "4": "16px", "8": "32px"}},
            "border_radius": {"base": "8px", "lg": "16px"},
            "shadows": {"sm": "0 1px 2px", "md": "0 4px 6px"},
            "icons": {"style": "outline", "size": "24px"},
            "component_libraries": [],
        }

        result = await generate_design_system(state)

        # Verify Design System extracted
        assert "design_system" in result
        design_system = result["design_system"]

        # Should have comprehensive design system
        assert len(design_system["colors"]["primary"]) >= 3
        assert len(design_system["typography"]["sizes"]) >= 2
        assert len(design_system["spacing"]["values"]) >= 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
