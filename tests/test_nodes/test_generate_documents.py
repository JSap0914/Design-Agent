"""
Unit tests for generate_documents node (Phase 6).

Tests parallel generation of 6 design documentation files.
"""

import pytest
from unittest.mock import AsyncMock, patch, call
from pathlib import Path

from src.langgraph.nodes.generate_documents import (
    generate_documents,
    generate_design_system_document,
    generate_ux_flow_document,
    generate_screen_specifications_document,
    generate_google_ai_prompts_document,
    generate_design_guidelines_document,
    generate_open_source_recommendations_document,
)
from src.langgraph.state import DesignAgentState


@pytest.mark.asyncio
async def test_generate_documents_parallel():
    """Test that all 6 documents are generated in parallel."""
    state: DesignAgentState = {
        "job_id": "test-job-parallel",
        "prd_content": "# Test PRD",
        "trd_content": "# Test TRD",
        "extracted_screens": ["Login", "Dashboard"],
        "selected_designs": {
            "Login": "Login ASCII UI...",
            "Dashboard": "Dashboard ASCII UI...",
        },
        "design_system": {
            "colors": {"primary": ["#3B82F6"]},
            "typography": {"sizes": {"base": "16px"}},
        },
        "design_decisions": [],
        "selected_open_source": [],
        "current_phase": 5,
    }

    with patch("src.langgraph.nodes.generate_documents.generate_text_async", new_callable=AsyncMock) as mock_gen, \
         patch("src.langgraph.nodes.generate_documents.store_all_documents", new_callable=AsyncMock) as mock_store:

        # Mock text generation
        mock_gen.return_value = "# Generated Document\n\nContent here..."

        result = await generate_documents(state)

        # Verify all 6 documents generated
        assert "generated_documents" in result
        docs = result["generated_documents"]

        assert "Design_System_v0.9.md" in docs
        assert "UX_Flow_v0.9.md" in docs
        assert "Screen_Specifications_v0.9.md" in docs
        assert "Google_AI_Studio_Prompts_v0.9.md" in docs
        assert "Design_Guidelines_v0.9.md" in docs
        assert "Open_Source_Recommendations_v0.9.md" in docs

        # Verify phase progression
        assert result["current_phase"] == 6
        assert result["phase_name"] == "Documents Generated"
        assert result["progress_percent"] == 90.0

        # Verify LLM called 6 times (once per document)
        assert mock_gen.call_count == 6

        # Verify documents stored in database
        mock_store.assert_called_once()


@pytest.mark.asyncio
async def test_generate_documents_sequential():
    """Test sequential generation when parallel_document_generation is False."""
    state: DesignAgentState = {
        "job_id": "test-job-sequential",
        "prd_content": "# Test PRD",
        "trd_content": "# Test TRD",
        "extracted_screens": ["Login"],
        "selected_designs": {"Login": "Login UI..."},
        "design_system": {"colors": {"primary": ["#3B82F6"]}},
        "design_decisions": [],
        "selected_open_source": [],
        "current_phase": 5,
    }

    with patch("src.langgraph.nodes.generate_documents.settings") as mock_settings, \
         patch("src.langgraph.nodes.generate_documents.generate_text_async", new_callable=AsyncMock) as mock_gen, \
         patch("src.langgraph.nodes.generate_documents.store_all_documents", new_callable=AsyncMock):

        # Disable parallel generation
        mock_settings.parallel_document_generation = False
        mock_gen.return_value = "# Document Content"

        result = await generate_documents(state)

        # Should still generate all 6 documents
        assert len(result["generated_documents"]) == 6
        assert mock_gen.call_count == 6


@pytest.mark.asyncio
async def test_generate_documents_filesystem_save():
    """Test that documents are saved to filesystem."""
    state: DesignAgentState = {
        "job_id": "test-job-filesystem",
        "prd_content": "# Test PRD",
        "trd_content": "# Test TRD",
        "extracted_screens": ["Login"],
        "selected_designs": {"Login": "Login UI..."},
        "design_system": {"colors": {"primary": ["#3B82F6"]}},
        "design_decisions": [],
        "selected_open_source": [],
        "current_phase": 5,
    }

    with patch("src.langgraph.nodes.generate_documents.generate_text_async", new_callable=AsyncMock) as mock_gen, \
         patch("src.langgraph.nodes.generate_documents.store_all_documents", new_callable=AsyncMock), \
         patch("builtins.open", create=True) as mock_open, \
         patch("pathlib.Path.mkdir") as mock_mkdir:

        mock_gen.return_value = "# Document Content"

        result = await generate_documents(state)

        # Verify directories created
        assert mock_mkdir.call_count > 0

        # Verify files written (6 documents)
        assert mock_open.call_count == 6


@pytest.mark.asyncio
async def test_generate_documents_database_storage():
    """Test that documents are stored in database."""
    state: DesignAgentState = {
        "job_id": "test-job-db",
        "prd_content": "# Test PRD",
        "trd_content": "# Test TRD",
        "extracted_screens": ["Login"],
        "selected_designs": {"Login": "Login UI..."},
        "design_system": {"colors": {"primary": ["#3B82F6"]}},
        "design_decisions": [],
        "selected_open_source": [],
        "current_phase": 5,
    }

    with patch("src.langgraph.nodes.generate_documents.generate_text_async", new_callable=AsyncMock) as mock_gen, \
         patch("src.langgraph.nodes.generate_documents.store_all_documents", new_callable=AsyncMock) as mock_store:

        mock_gen.return_value = "# Document Content"

        result = await generate_documents(state)

        # Verify store_all_documents called with correct structure
        mock_store.assert_called_once()

        call_args = mock_store.call_args
        job_id_arg = call_args[0][0]
        documents_arg = call_args[0][1]
        version_arg = call_args[0][2]

        assert job_id_arg == "test-job-db"
        assert version_arg == "0.9"

        # Verify all 6 document types present
        assert "design_system" in documents_arg
        assert "ux_flow" in documents_arg
        assert "screen_specifications" in documents_arg
        assert "google_ai_prompts" in documents_arg
        assert "design_guidelines" in documents_arg
        assert "open_source_recommendations" in documents_arg


@pytest.mark.asyncio
async def test_generate_design_system_document():
    """Test Design System document generation."""
    state: DesignAgentState = {
        "design_system": {
            "colors": {
                "primary": ["#3B82F6", "#2563EB"],
                "semantic": {"success": "#10B981"},
            },
            "typography": {
                "font_families": {"primary": "Inter, sans-serif"},
                "sizes": {"base": "16px"},
            },
            "spacing": {"scale": "8pt grid"},
            "component_libraries": ["TanStack Table"],
        },
        "selected_open_source": [
            {
                "library_name": "TanStack Table",
                "category": "ui_components",
            }
        ],
    }

    with patch("src.langgraph.nodes.generate_documents.generate_text_async", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = """# Design System v0.9

## Color Palette
- Primary: #3B82F6, #2563EB

## Typography
- Font Family: Inter, sans-serif
"""

        content = await generate_design_system_document(state)

        assert "# Design System v0.9" in content
        assert "#3B82F6" in content
        assert mock_gen.called


@pytest.mark.asyncio
async def test_generate_ux_flow_document():
    """Test UX Flow document generation."""
    state: DesignAgentState = {
        "prd_content": "# E-commerce App PRD",
        "extracted_screens": ["Home", "Product List", "Product Detail", "Cart"],
        "design_decisions": [
            {
                "screen_name": "Home",
                "decision_type": "initial_layout",
                "rationale": "Hero section with featured products",
            }
        ],
    }

    with patch("src.langgraph.nodes.generate_documents.generate_text_async", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = """# UX Flow v0.9

## Navigation Flow
Home → Product List → Product Detail → Cart → Checkout
"""

        content = await generate_ux_flow_document(state)

        assert "# UX Flow v0.9" in content
        assert mock_gen.called


@pytest.mark.asyncio
async def test_generate_screen_specifications_document():
    """Test Screen Specifications document generation."""
    state: DesignAgentState = {
        "extracted_screens": ["Login", "Dashboard"],
        "selected_designs": {
            "Login": "┌────────────┐\n│  Login UI  │\n└────────────┘",
            "Dashboard": "┌────────────┐\n│ Dashboard  │\n└────────────┘",
        },
        "design_decisions": [],
    }

    with patch("src.langgraph.nodes.generate_documents.generate_text_async", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = """# Screen Specifications v0.9

## Login Screen
ASCII UI:
```
┌────────────┐
│  Login UI  │
└────────────┘
```
"""

        content = await generate_screen_specifications_document(state)

        assert "# Screen Specifications v0.9" in content
        assert "Login Screen" in content
        assert mock_gen.called


@pytest.mark.asyncio
async def test_generate_google_ai_prompts_document():
    """Test Google AI Studio Prompts document generation."""
    state: DesignAgentState = {
        "extracted_screens": ["Home", "Profile"],
        "selected_designs": {
            "Home": "Home ASCII UI...",
            "Profile": "Profile ASCII UI...",
        },
        "design_system": {
            "colors": {"primary": ["#3B82F6"]},
        },
    }

    with patch("src.langgraph.nodes.generate_documents.generate_text_async", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = """# Google AI Studio Prompts v0.9

## Home Screen Prompt
Create a modern home screen with:
- Blue primary color (#3B82F6)
- Clean layout based on ASCII mockup
"""

        content = await generate_google_ai_prompts_document(state)

        assert "# Google AI Studio Prompts v0.9" in content
        assert mock_gen.called


@pytest.mark.asyncio
async def test_generate_design_guidelines_document():
    """Test Design Guidelines document generation."""
    state: DesignAgentState = {
        "design_system": {
            "colors": {"primary": ["#3B82F6"]},
            "typography": {"sizes": {"base": "16px"}},
        },
        "selected_open_source": [
            {
                "library_name": "TanStack Table",
                "license": "MIT",
            }
        ],
    }

    with patch("src.langgraph.nodes.generate_documents.generate_text_async", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = """# Design Guidelines v0.9

## Accessibility
- WCAG AA compliance
- Minimum 4.5:1 contrast ratio

## Open-Source Libraries
- TanStack Table (MIT)
"""

        content = await generate_design_guidelines_document(state)

        assert "# Design Guidelines v0.9" in content
        assert "WCAG AA" in content or "Accessibility" in content
        assert mock_gen.called


@pytest.mark.asyncio
async def test_generate_open_source_recommendations_document():
    """Test Open-Source Recommendations document generation."""
    state: DesignAgentState = {
        "selected_open_source": [
            {
                "library_name": "TanStack Table",
                "category": "ui_components",
                "github_url": "https://github.com/TanStack/table",
                "stars": 22000,
                "license": "MIT",
                "bundle_size": "15KB",
                "ranking_score": 95.5,
                "rationale": "Headless UI, perfect for customization",
            },
            {
                "library_name": "React Hook Form",
                "category": "forms",
                "github_url": "https://github.com/react-hook-form/react-hook-form",
                "stars": 35000,
                "license": "MIT",
                "bundle_size": "8KB",
                "ranking_score": 98.0,
                "rationale": "Lightweight form validation",
            },
        ],
    }

    with patch("src.langgraph.nodes.generate_documents.generate_text_async", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = """# Open-Source Recommendations v0.9

## UI Components
### TanStack Table
- GitHub: https://github.com/TanStack/table
- Stars: 22,000+
- License: MIT
- Bundle Size: 15KB

## Forms
### React Hook Form
- Stars: 35,000+
- Bundle Size: 8KB
"""

        content = await generate_open_source_recommendations_document(state)

        assert "# Open-Source Recommendations v0.9" in content
        assert "TanStack Table" in content
        assert "React Hook Form" in content
        assert mock_gen.called


@pytest.mark.asyncio
async def test_generate_documents_error_handling():
    """Test error handling when document generation fails."""
    state: DesignAgentState = {
        "job_id": "test-job-error",
        "prd_content": "# Test PRD",
        "trd_content": "# Test TRD",
        "extracted_screens": ["Login"],
        "selected_designs": {"Login": "Login UI..."},
        "design_system": {"colors": {"primary": ["#3B82F6"]}},
        "design_decisions": [],
        "selected_open_source": [],
        "current_phase": 5,
    }

    with patch("src.langgraph.nodes.generate_documents.generate_text_async", new_callable=AsyncMock) as mock_gen, \
         patch("src.langgraph.nodes.generate_documents.store_all_documents", new_callable=AsyncMock):

        # Simulate LLM failure
        mock_gen.side_effect = Exception("LLM API timeout")

        result = await generate_documents(state)

        # Should have error in state
        assert "errors" in result
        assert len(result["errors"]) > 0
        assert "Document generation failed" in result["errors"][0]
        assert result["should_retry"] is True


@pytest.mark.asyncio
async def test_generate_documents_preserves_state():
    """Test that generate_documents preserves other state fields."""
    state: DesignAgentState = {
        "job_id": "test-job-preserve",
        "project_id": "proj-123",
        "user_id": "user-456",
        "prd_content": "# Test PRD",
        "trd_content": "# Test TRD",
        "extracted_screens": ["Login"],
        "selected_designs": {"Login": "Login UI..."},
        "design_system": {"colors": {"primary": ["#3B82F6"]}},
        "design_decisions": [],
        "selected_open_source": [],
        "current_phase": 5,
        "custom_field": "should_be_preserved",
    }

    with patch("src.langgraph.nodes.generate_documents.generate_text_async", new_callable=AsyncMock) as mock_gen, \
         patch("src.langgraph.nodes.generate_documents.store_all_documents", new_callable=AsyncMock):

        mock_gen.return_value = "# Document Content"

        result = await generate_documents(state)

        # Verify original fields preserved
        assert result["job_id"] == "test-job-preserve"
        assert result["project_id"] == "proj-123"
        assert result["user_id"] == "user-456"
        assert result["custom_field"] == "should_be_preserved"


@pytest.mark.asyncio
async def test_generate_documents_with_no_libraries():
    """Test document generation when no open-source libraries selected."""
    state: DesignAgentState = {
        "job_id": "test-job-no-libs",
        "prd_content": "# Test PRD",
        "trd_content": "# Test TRD",
        "extracted_screens": ["Login"],
        "selected_designs": {"Login": "Login UI..."},
        "design_system": {"colors": {"primary": ["#3B82F6"]}},
        "design_decisions": [],
        "selected_open_source": [],  # No libraries
        "current_phase": 5,
    }

    with patch("src.langgraph.nodes.generate_documents.generate_text_async", new_callable=AsyncMock) as mock_gen, \
         patch("src.langgraph.nodes.generate_documents.store_all_documents", new_callable=AsyncMock):

        mock_gen.return_value = "# Document Content"

        result = await generate_documents(state)

        # Should still generate all 6 documents
        assert len(result["generated_documents"]) == 6
        assert "Open_Source_Recommendations_v0.9.md" in result["generated_documents"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
