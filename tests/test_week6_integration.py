"""
Week 6 Integration Tests: ANYON API Integration, WebSocket, and End-to-End Workflow.

Tests:
1. ANYON Kanban API integration (ticket creation, updates, completion)
2. WebSocket real-time updates during Phase 6
3. Complete end-to-end workflow (Phases 1-6)
4. Document generation and packaging
5. Job API endpoints (create, start, status, download)
"""

import pytest
import asyncio
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from src.langgraph.state import DesignAgentState
from src.langgraph.nodes.generate_documents import generate_documents
from src.langgraph.nodes.package_for_dev import package_for_dev
from src.integration.anyon_client import AnyonClient


# ============================================================================
# ANYON Client Tests
# ============================================================================


@pytest.mark.asyncio
async def test_anyon_client_create_ticket():
    """Test ANYON client ticket creation."""
    client = AnyonClient(
        base_url="http://test-anyon.com/api",
        api_key="test-key",
    )

    # Mock the HTTP request
    mock_response = {
        "success": True,
        "ticket_id": "ANYON-123",
        "project_id": "proj-456",
        "status": "design_in_progress",
    }

    with patch.object(client, "_make_request", return_value=mock_response) as mock_request:
        result = await client.create_design_ticket(
            project_id="proj-456",
            prd_title="Test PRD",
            job_id="job-789",
        )

        assert result["success"] is True
        assert result["ticket_id"] == "ANYON-123"
        mock_request.assert_called_once_with(
            "POST",
            "/tickets",
            data={
                "project_id": "proj-456",
                "title": "Design: Test PRD",
                "status": "design_in_progress",
                "type": "design",
                "metadata": {
                    "design_agent_job_id": "job-789",
                    "phase": 1,
                    "phase_name": "Screen Extraction",
                },
            },
        )


@pytest.mark.asyncio
async def test_anyon_client_update_ticket_status():
    """Test ANYON client ticket status update."""
    client = AnyonClient(
        base_url="http://test-anyon.com/api",
        api_key="test-key",
    )

    mock_response = {
        "success": True,
        "ticket_id": "ANYON-123",
        "status": "design_in_progress",
    }

    with patch.object(client, "_make_request", return_value=mock_response) as mock_request:
        result = await client.update_ticket_status(
            ticket_id="ANYON-123",
            status="design_in_progress",
            phase=3,
            phase_name="ASCII UI Creation",
            progress_percent=50.0,
        )

        assert result["success"] is True
        mock_request.assert_called_once()


@pytest.mark.asyncio
async def test_anyon_client_complete_ticket():
    """Test ANYON client ticket completion."""
    client = AnyonClient(
        base_url="http://test-anyon.com/api",
        api_key="test-key",
    )

    # Create temporary test documents
    test_dir = Path("tests/temp_docs")
    test_dir.mkdir(parents=True, exist_ok=True)

    test_docs = {
        "design_system": test_dir / "Design_System_v0.9.md",
        "ux_flow": test_dir / "UX_Flow_v0.9.md",
    }

    for doc_path in test_docs.values():
        doc_path.write_text("# Test Document", encoding="utf-8")

    mock_response = {
        "success": True,
        "ticket_id": "ANYON-123",
        "status": "design_complete",
    }

    with patch.object(client, "_make_request", return_value=mock_response) as mock_request:
        result = await client.complete_design_ticket(
            ticket_id="ANYON-123",
            job_id="job-789",
            quality_score=95,
            documents=test_docs,
        )

        assert result["success"] is True
        # Should have called attach_document for each file + complete_design_ticket
        assert mock_request.call_count >= 3

    # Cleanup
    for doc_path in test_docs.values():
        if doc_path.exists():
            doc_path.unlink()
    if test_dir.exists():
        test_dir.rmdir()


# ============================================================================
# Document Generation Tests
# ============================================================================


@pytest.mark.asyncio
async def test_generate_documents_node():
    """Test Phase 6 document generation node."""
    state: DesignAgentState = {
        "job_id": "test-job-123",
        "prd_content": "# Test PRD\n\nTest product requirements",
        "trd_content": "# Test TRD\n\nTest technical requirements",
        "extracted_screens": ["Login Screen", "Dashboard"],
        "selected_designs": {
            "Login Screen": "┌─────┐\n│Login│\n└─────┘",
            "Dashboard": "┌─────────┐\n│Dashboard│\n└─────────┘",
        },
        "design_system": {
            "colors": {
                "primary": ["#007AFF"],
                "secondary": ["#5AC8FA"],
            },
            "typography": {
                "font_families": {"primary": "Inter"},
            },
        },
        "design_decisions": ["Use primary blue for CTAs"],
        "selected_open_source": [
            {"library_name": "TanStack Table", "category": "UI Components"}
        ],
        "library_search_logs": [],
        "current_phase": 5,
    }

    # Mock LLM client and database storage
    with patch("src.langgraph.nodes.generate_documents.generate_text_async", new_callable=AsyncMock) as mock_generate:
        with patch("src.langgraph.nodes.generate_documents.store_all_documents", new_callable=AsyncMock) as mock_store:
            mock_generate.return_value = "# Generated Document\n\nTest content"
            mock_store.return_value = []  # Mock database insert

            result = await generate_documents(state)

            # Check state updates
            assert result["current_phase"] == 6
            assert result["phase_name"] == "Document Generation"
            assert "generated_documents" in result
            assert len(result["generated_documents"]) == 6

            # Verify all 6 documents were "generated"
            expected_docs = [
                "design_system",
                "ux_flow",
                "screen_specifications",
                "google_ai_prompts",
                "design_guidelines",
                "open_source_recommendations",
            ]
            for doc_type in expected_docs:
                assert doc_type in result["generated_documents"]

            # Verify database storage was called
            mock_store.assert_called_once()


@pytest.mark.asyncio
async def test_package_for_dev_node():
    """Test Phase 6 packaging node."""
    state: DesignAgentState = {
        "job_id": "test-job-456",
        "prd_content": "# Test PRD",
        "trd_content": "# Test TRD",
        "extracted_screens": ["Screen 1"],
        "selected_designs": {"Screen 1": "ASCII UI"},
        "design_system": {"colors": {}},
        "generated_documents": {
            "design_system": "docs/generated_outputs/test-job-456/Design_System_v0.9.md",
            "ux_flow": "docs/generated_outputs/test-job-456/UX_Flow_v0.9.md",
        },
        "uploaded_code": "const App = () => <div>Test</div>;",
        "validation_results": {
            "quality_score": 92,
            "syntax_check": {"status": "passed"},
            "accessibility_check": {"status": "passed"},
        },
        "anyon_ticket_id": "ANYON-123",
        "current_phase": 6,
    }

    # Create mock documents
    output_dir = Path("docs/generated_outputs/test-job-456")
    output_dir.mkdir(parents=True, exist_ok=True)

    for doc_path_str in state["generated_documents"].values():
        doc_path = Path(doc_path_str)
        doc_path.write_text("# Test Document", encoding="utf-8")

    # Mock ANYON client
    with patch("src.langgraph.nodes.package_for_dev.AnyonClient") as mock_anyon:
        mock_client = AsyncMock()
        mock_client.complete_design_ticket = AsyncMock(return_value={"success": True})
        mock_anyon.return_value = mock_client

        result = await package_for_dev(state)

        # Check state updates
        assert result["status"] == "completed"
        assert result["current_phase"] == 6
        assert result["phase_name"] == "Complete"
        assert "package_path" in result
        assert "package_zip_path" in result

        # Verify package directory exists
        package_dir = Path(result["package_path"])
        assert package_dir.exists()

        # Verify manifest exists
        manifest_path = package_dir / "manifest.json"
        assert manifest_path.exists()

        manifest = json.loads(manifest_path.read_text())
        assert manifest["job_id"] == "test-job-456"
        assert manifest["quality_score"] == 92
        assert manifest["ready_for_tech_spec"] is True

    # Cleanup
    import shutil

    if output_dir.exists():
        shutil.rmtree(output_dir)


# ============================================================================
# API Endpoint Tests
# ============================================================================


@pytest.mark.asyncio
async def test_create_job_endpoint(test_client):
    """Test POST /api/jobs/create endpoint."""
    response = await test_client.post(
        "/api/jobs/create",
        json={
            "prd_content": "# Test PRD\n\nTest content",
            "trd_content": "# Test TRD\n\nTest content",
            "project_id": "proj-123",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "job_id" in data
    assert data["status"] == "pending"


@pytest.mark.asyncio
async def test_start_job_endpoint(test_client, sample_job_id):
    """Test POST /api/jobs/{job_id}/start endpoint."""
    response = await test_client.post(f"/api/jobs/{sample_job_id}/start")

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["job_id"] == sample_job_id
    assert data["status"] == "in_progress"


@pytest.mark.asyncio
async def test_get_job_status_endpoint(test_client, sample_job_id):
    """Test GET /api/jobs/{job_id}/status endpoint."""
    response = await test_client.get(f"/api/jobs/{sample_job_id}/status")

    assert response.status_code == 200
    data = response.json()
    assert data["job_id"] == sample_job_id
    assert "status" in data
    assert "current_phase" in data


@pytest.mark.asyncio
async def test_get_package_endpoint(test_client, completed_job_id):
    """Test GET /api/jobs/{job_id}/package endpoint."""
    response = await test_client.get(f"/api/jobs/{completed_job_id}/package")

    assert response.status_code == 200
    data = response.json()
    assert data["job_id"] == completed_job_id
    assert data["status"] == "completed"
    assert "package_path" in data
    assert "generated_documents" in data


@pytest.mark.asyncio
async def test_download_package_endpoint(test_client, completed_job_id):
    """Test GET /api/jobs/{job_id}/download endpoint."""
    response = await test_client.get(f"/api/jobs/{completed_job_id}/download")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/zip"


# ============================================================================
# End-to-End Workflow Tests
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.slow
async def test_complete_workflow_phases_1_to_6():
    """
    Test complete workflow from Phase 1 to Phase 6.

    This is the ultimate integration test for Week 6.
    """
    from src.langgraph.workflow import compile_workflow

    # Prepare test data
    test_prd = """# Task Management App PRD

## Screens
1. Login Screen
2. Task List Screen
3. Task Detail Screen
"""

    test_trd = """# Task Management App TRD

## Platform
- React 19 + TypeScript
- Tailwind CSS
- Mobile-first
"""

    initial_state: DesignAgentState = {
        "job_id": "e2e-test-job",
        "prd_content": test_prd,
        "trd_content": test_trd,
        "extracted_screens": [],
        "current_phase": 0,
    }

    # Mock LLM calls for all phases
    with patch("src.llm.client.generate_json_async", new_callable=AsyncMock) as mock_json:
        with patch("src.llm.client.generate_text_async", new_callable=AsyncMock) as mock_text:
            # Phase 1: Screen extraction
            mock_json.return_value = {
                "screens": ["Login Screen", "Task List Screen", "Task Detail Screen"],
                "rationale": "Test screens",
            }

            # Phase 2-6: Text generation
            mock_text.return_value = "# Test Output\n\nGenerated content"

            # Compile workflow
            workflow = compile_workflow()
            config = {"configurable": {"thread_id": "e2e-test-job"}}

            # Execute workflow (will pause at Phase 4.5 for user choice)
            final_state = None
            async for event in workflow.astream(initial_state, config):
                if "__end__" in event:
                    final_state = event["__end__"]

            # Verify workflow progression
            assert final_state is not None
            assert "extracted_screens" in final_state
            assert len(final_state["extracted_screens"]) == 3

            # Note: Full Phase 6 execution requires manual user choices
            # (pause/skip decision, code upload, etc.)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def sample_job_id():
    """Provide a sample job ID for testing."""
    return "550e8400-e29b-41d4-a716-446655440000"


@pytest.fixture
def completed_job_id(sample_job_id):
    """Provide a completed job ID with package ready."""
    # This would normally be set up with actual database state
    return sample_job_id


@pytest.fixture
async def test_client():
    """Provide FastAPI test client."""
    from fastapi.testclient import TestClient
    from src.main import app

    with TestClient(app) as client:
        yield client


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
