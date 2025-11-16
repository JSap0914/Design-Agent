"""
Unit tests for package_for_dev node (Phase 6).

Tests packaging all deliverables for Tech Spec Agent handoff.
"""

import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock, mock_open
from pathlib import Path

from src.langgraph.nodes.package_for_dev import (
    package_for_dev,
    create_validation_report,
    create_package_manifest,
    create_package_zip,
    upload_to_anyon,
)
from src.langgraph.state import DesignAgentState


@pytest.mark.asyncio
async def test_package_for_dev_complete():
    """Test complete packaging with all deliverables."""
    state: DesignAgentState = {
        "job_id": "test-job-complete",
        "created_at": "2025-01-13T10:00:00Z",
        "generated_documents": {
            "design_system": "docs/generated_outputs/test-job-complete/Design_System_v0.9.md",
            "ux_flow": "docs/generated_outputs/test-job-complete/UX_Flow_v0.9.md",
            "screen_specifications": "docs/generated_outputs/test-job-complete/Screen_Specifications_v0.9.md",
            "google_ai_prompts": "docs/generated_outputs/test-job-complete/Google_AI_Studio_Prompts_v0.9.md",
            "design_guidelines": "docs/generated_outputs/test-job-complete/Design_Guidelines_v0.9.md",
            "open_source_recommendations": "docs/generated_outputs/test-job-complete/Open_Source_Recommendations_v0.9.md",
        },
        "uploaded_code": "const LoginScreen = () => { return <div>Login</div>; };",
        "validation_results": {
            "quality_score": 95,
            "syntax_check": {"status": "passed"},
            "typescript_check": {"status": "passed"},
        },
        "extracted_screens": ["Login", "Dashboard"],
        "selected_open_source": [{"library_name": "TanStack Table"}],
        "current_phase": 5,
    }

    with patch("pathlib.Path.mkdir") as mock_mkdir, \
         patch("pathlib.Path.exists", return_value=True), \
         patch("pathlib.Path.read_text", return_value="# Document Content"), \
         patch("pathlib.Path.write_text") as mock_write, \
         patch("src.langgraph.nodes.package_for_dev.create_package_zip", new_callable=AsyncMock) as mock_zip, \
         patch("src.langgraph.nodes.package_for_dev.upload_to_anyon", new_callable=AsyncMock) as mock_upload:

        mock_zip.return_value = Path("docs/generated_outputs/test-job-complete/design_package_test-job-complete.zip")
        mock_upload.return_value = {"status": "success", "ticket_id": "ANYON-123"}

        result = await package_for_dev(state)

        # Verify phase completion
        assert result["current_phase"] == 6
        assert result["phase_name"] == "Complete"
        assert result["status"] == "completed"

        # Verify package paths set
        assert "package_path" in result
        assert "package_zip_path" in result
        assert "test-job-complete" in result["package_path"]
        assert "design_package" in result["package_zip_path"]

        # Verify files written (6 docs + code + validation report + manifest)
        assert mock_write.call_count >= 9

        # Verify ZIP created
        mock_zip.assert_called_once()


@pytest.mark.asyncio
async def test_package_for_dev_without_code():
    """Test packaging when no code uploaded."""
    state: DesignAgentState = {
        "job_id": "test-job-no-code",
        "generated_documents": {
            "design_system": "docs/generated_outputs/test-job-no-code/Design_System_v0.9.md",
        },
        "uploaded_code": None,  # No code
        "validation_results": {"quality_score": 90},
        "extracted_screens": ["Login"],
        "selected_open_source": [],
        "current_phase": 5,
    }

    with patch("pathlib.Path.mkdir"), \
         patch("pathlib.Path.exists", return_value=True), \
         patch("pathlib.Path.read_text", return_value="# Content"), \
         patch("pathlib.Path.write_text") as mock_write, \
         patch("src.langgraph.nodes.package_for_dev.create_package_zip", new_callable=AsyncMock), \
         patch("src.langgraph.nodes.package_for_dev.upload_to_anyon", new_callable=AsyncMock):

        result = await package_for_dev(state)

        # Should complete successfully
        assert result["status"] == "completed"

        # Verify no code file written
        written_content = [call.args[0] for call in mock_write.call_args_list]
        assert not any("const" in str(content) or "LoginScreen" in str(content) for content in written_content)


@pytest.mark.asyncio
async def test_create_validation_report():
    """Test validation report generation."""
    state: DesignAgentState = {
        "job_id": "test-job-report",
        "created_at": "2025-01-13T10:00:00Z",
        "validation_results": {
            "quality_score": 92,
            "syntax_check": {"status": "passed", "error_count": 0},
            "typescript_check": {"status": "passed", "error_count": 0},
            "tailwind_check": {"status": "passed", "has_custom_css": False},
            "accessibility_check": {
                "status": "passed",
                "issue_count": 0,
                "min_contrast_ratio": "4.8:1",
                "touch_target_violations": 0,
            },
            "design_system_check": {
                "status": "passed",
                "color_matches": "100%",
                "typography_matches": "100%",
            },
            "performance": {
                "bundle_size_kb": 245,
                "estimated_load_time_ms": 850,
            },
            "recommendations": [
                "Consider lazy loading images",
                "Optimize bundle size",
            ],
        },
    }

    report = await create_validation_report(state)

    # Verify report structure
    assert "# Design Validation Report" in report
    assert "test-job-report" in report
    assert "92/100" in report

    # Verify sections
    assert "Syntax Validation" in report
    assert "TypeScript Validation" in report
    assert "Tailwind CSS Validation" in report
    assert "Accessibility (WCAG AA)" in report
    assert "Design System Compliance" in report
    assert "Performance Metrics" in report
    assert "Recommendations" in report

    # Verify specific values
    assert "passed" in report
    assert "4.8:1" in report
    assert "245 KB" in report
    assert "lazy loading" in report


@pytest.mark.asyncio
async def test_create_validation_report_with_failures():
    """Test validation report with failing checks."""
    state: DesignAgentState = {
        "job_id": "test-job-failures",
        "validation_results": {
            "quality_score": 65,
            "syntax_check": {"status": "failed", "error_count": 3},
            "typescript_check": {"status": "failed", "error_count": 5},
            "accessibility_check": {
                "status": "failed",
                "issue_count": 7,
                "touch_target_violations": 2,
            },
        },
    }

    report = await create_validation_report(state)

    assert "65/100" in report
    assert "failed" in report
    assert "3" in report  # Syntax errors
    assert "5" in report  # TypeScript errors
    assert "7" in report  # Accessibility issues


@pytest.mark.asyncio
async def test_create_package_manifest():
    """Test manifest file creation."""
    state: DesignAgentState = {
        "job_id": "test-job-manifest",
        "created_at": "2025-01-13T10:00:00Z",
        "validation_results": {"quality_score": 88},
        "uploaded_code": "const App = () => <div />;",
        "extracted_screens": ["Login", "Dashboard", "Settings"],
        "selected_open_source": [
            {"library_name": "TanStack Table"},
            {"library_name": "React Hook Form"},
        ],
    }

    package_path = Path("/tmp/package")
    manifest = await create_package_manifest(state, package_path)

    # Verify structure
    assert manifest["job_id"] == "test-job-manifest"
    assert manifest["created_at"] == "2025-01-13T10:00:00Z"
    assert manifest["quality_score"] == 88
    assert manifest["screens_count"] == 3
    assert manifest["selected_libraries_count"] == 2
    assert manifest["ready_for_tech_spec"] is True

    # Verify documents section
    assert "documents" in manifest
    docs = manifest["documents"]
    assert "design_system" in docs
    assert "ux_flow" in docs
    assert "screen_specifications" in docs
    assert "google_ai_prompts" in docs
    assert "design_guidelines" in docs
    assert "open_source_recommendations" in docs

    # Verify validated code included
    assert manifest["validated_code"] == "validated_code.tsx"
    assert manifest["validation_report"] == "validation_report.md"


@pytest.mark.asyncio
async def test_create_package_manifest_no_code():
    """Test manifest creation when no code uploaded."""
    state: DesignAgentState = {
        "job_id": "test-job-no-code",
        "validation_results": {"quality_score": 85},
        "uploaded_code": None,  # No code
        "extracted_screens": ["Login"],
        "selected_open_source": [],
    }

    manifest = await create_package_manifest(state, Path("/tmp"))

    # Should not include validated_code
    assert manifest["validated_code"] is None


@pytest.mark.asyncio
async def test_create_package_zip():
    """Test ZIP archive creation."""
    package_dir = Path("/tmp/test_package")
    output_path = Path("/tmp/test_package.zip")

    with patch("zipfile.ZipFile") as mock_zipfile, \
         patch("pathlib.Path.rglob", return_value=[
             Path("/tmp/test_package/doc1.md"),
             Path("/tmp/test_package/doc2.md"),
             Path("/tmp/test_package/manifest.json"),
         ]), \
         patch("pathlib.Path.is_file", return_value=True):

        mock_zip_instance = MagicMock()
        mock_zipfile.return_value.__enter__.return_value = mock_zip_instance

        result = await create_package_zip(package_dir, output_path)

        # Verify ZIP created
        assert result == output_path
        mock_zipfile.assert_called_once()

        # Verify files added to ZIP
        assert mock_zip_instance.write.call_count == 3


@pytest.mark.asyncio
async def test_upload_to_anyon_enabled():
    """Test ANYON upload when integration enabled."""
    state: DesignAgentState = {
        "job_id": "test-job-anyon",
        "anyon_ticket_id": "ANYON-456",
        "generated_documents": {
            "design_system": "docs/Design_System_v0.9.md",
        },
        "validation_results": {"quality_score": 93},
    }

    package_dir = Path("/tmp/package")

    with patch("src.langgraph.nodes.package_for_dev.settings") as mock_settings, \
         patch("src.langgraph.nodes.package_for_dev.AnyonClient") as mock_client_class, \
         patch("pathlib.Path.exists", return_value=True):

        # Enable ANYON integration
        mock_settings.anyon_enable_integration = True

        # Mock ANYON client
        mock_client = MagicMock()
        mock_client.complete_design_ticket = AsyncMock(return_value={"status": "success"})
        mock_client_class.return_value = mock_client

        result = await upload_to_anyon(state, package_dir)

        # Verify upload succeeded
        assert result["status"] == "success"

        # Verify complete_design_ticket called
        mock_client.complete_design_ticket.assert_called_once()
        call_kwargs = mock_client.complete_design_ticket.call_args.kwargs
        assert call_kwargs["ticket_id"] == "ANYON-456"
        assert call_kwargs["job_id"] == "test-job-anyon"
        assert call_kwargs["quality_score"] == 93


@pytest.mark.asyncio
async def test_upload_to_anyon_disabled():
    """Test ANYON upload skipped when integration disabled."""
    state: DesignAgentState = {
        "job_id": "test-job-no-anyon",
        "generated_documents": {},
    }

    with patch("src.langgraph.nodes.package_for_dev.settings") as mock_settings:
        # Disable ANYON integration
        mock_settings.anyon_enable_integration = False

        result = await upload_to_anyon(state, Path("/tmp"))

        # Should return None (skipped)
        assert result is None


@pytest.mark.asyncio
async def test_upload_to_anyon_no_ticket_id():
    """Test ANYON upload when no ticket_id in state."""
    state: DesignAgentState = {
        "job_id": "test-job-no-ticket",
        "anyon_ticket_id": None,  # No ticket ID
        "generated_documents": {},
    }

    with patch("src.langgraph.nodes.package_for_dev.settings") as mock_settings:
        mock_settings.anyon_enable_integration = True

        result = await upload_to_anyon(state, Path("/tmp"))

        # Should return None (cannot upload without ticket)
        assert result is None


@pytest.mark.asyncio
async def test_upload_to_anyon_error():
    """Test ANYON upload error handling."""
    state: DesignAgentState = {
        "job_id": "test-job-error",
        "anyon_ticket_id": "ANYON-789",
        "generated_documents": {},
        "validation_results": {"quality_score": 90},
    }

    with patch("src.langgraph.nodes.package_for_dev.settings") as mock_settings, \
         patch("src.langgraph.nodes.package_for_dev.AnyonClient") as mock_client_class:

        mock_settings.anyon_enable_integration = True

        # Mock client to raise exception
        mock_client = MagicMock()
        mock_client.complete_design_ticket = AsyncMock(side_effect=Exception("API timeout"))
        mock_client_class.return_value = mock_client

        result = await upload_to_anyon(state, Path("/tmp"))

        # Should return error dict
        assert "error" in result
        assert "API timeout" in result["error"]


@pytest.mark.asyncio
async def test_package_for_dev_error_handling():
    """Test error handling when packaging fails."""
    state: DesignAgentState = {
        "job_id": "test-job-error",
        "generated_documents": {},
        "validation_results": {},
        "extracted_screens": [],
        "selected_open_source": [],
    }

    with patch("pathlib.Path.mkdir", side_effect=Exception("Disk full")):
        result = await package_for_dev(state)

        # Should mark as failed
        assert result["status"] == "failed"
        assert "error" in result
        assert "Disk full" in result["error"]
        assert result["phase_name"] == "Packaging (Failed)"


@pytest.mark.asyncio
async def test_package_for_dev_anyon_integration():
    """Test full packaging with ANYON integration."""
    state: DesignAgentState = {
        "job_id": "test-job-anyon-full",
        "anyon_ticket_id": "ANYON-999",
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
         patch("src.langgraph.nodes.package_for_dev.create_package_zip", new_callable=AsyncMock) as mock_zip, \
         patch("src.langgraph.nodes.package_for_dev.upload_to_anyon", new_callable=AsyncMock) as mock_upload:

        mock_zip.return_value = Path("package.zip")
        mock_upload.return_value = {"status": "success", "ticket_url": "https://anyon.app/tickets/999"}

        result = await package_for_dev(state)

        # Verify ANYON upload status included
        assert "anyon_upload_status" in result
        assert result["anyon_upload_status"]["status"] == "success"
        assert result["status"] == "completed"


@pytest.mark.asyncio
async def test_package_for_dev_preserves_state():
    """Test that package_for_dev preserves other state fields."""
    state: DesignAgentState = {
        "job_id": "test-job-preserve",
        "project_id": "proj-123",
        "user_id": "user-456",
        "generated_documents": {},
        "validation_results": {},
        "extracted_screens": [],
        "selected_open_source": [],
        "current_phase": 5,
        "custom_field": "should_be_preserved",
    }

    with patch("pathlib.Path.mkdir"), \
         patch("pathlib.Path.exists", return_value=False), \
         patch("pathlib.Path.write_text"), \
         patch("src.langgraph.nodes.package_for_dev.create_package_zip", new_callable=AsyncMock), \
         patch("src.langgraph.nodes.package_for_dev.upload_to_anyon", new_callable=AsyncMock):

        result = await package_for_dev(state)

        # Verify original fields preserved
        assert result["job_id"] == "test-job-preserve"
        assert result["project_id"] == "proj-123"
        assert result["user_id"] == "user-456"
        assert result["custom_field"] == "should_be_preserved"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
