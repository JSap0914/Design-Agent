"""
Unit tests for job processor.

Tests job processing logic, status updates, and error handling.
"""

import pytest
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, patch, MagicMock

from src.workers.job_processor import (
    process_job,
    _get_job,
    _update_job_status,
    _create_progress_record,
    _update_progress,
)
from src.database.models import DesignJob, DesignProgress


# ============================================================================
# Test Fixtures
# ============================================================================


async def create_pending_job(async_session):
    """Create a pending design job for testing."""
    job = DesignJob(
        job_id=uuid.uuid4(),
        project_id="test-project-processor",
        user_id="test-user-processor",
        prd_content="# PRD\n\nTest PRD for processor",
        trd_content="# TRD\n\nTest TRD for processor",
        status="pending",
        )
    async_session.add(job)
    await async_session.commit()
    await async_session.refresh(job)
    return job


# ============================================================================
# Helper Function Tests
# ============================================================================


@pytest.mark.asyncio
async def test_get_job_existing(async_session, pending_job):
    """Test _get_job retrieves an existing job."""
    job = await _get_job(async_session, pending_job.job_id)

    assert job is not None
    assert job.job_id == pending_job.job_id
    assert job.project_id == pending_job.project_id
    assert job.user_id == pending_job.user_id


@pytest.mark.asyncio
async def test_get_job_nonexistent():
    """Test _get_job returns None for non-existent job."""
    from src.database.connection import db_manager
    
    async with db_manager.get_async_session() as async_session:
        fake_job_id = uuid.uuid4()
        job = await _get_job(async_session, fake_job_id)

        assert job is None


@pytest.mark.asyncio
async def test_update_job_status_to_running(async_session, pending_job):
    """Test updating job status to running sets started_at."""
    await _update_job_status(async_session, pending_job.job_id, "running")

    await async_session.refresh(pending_job)

    assert pending_job.status == "running"
    assert pending_job.started_at is not None
    assert isinstance(pending_job.started_at, datetime)


@pytest.mark.asyncio
async def test_update_job_status_to_completed(async_session, pending_job):
    """Test updating job status to completed sets completed_at."""
    # First set to running
    await _update_job_status(async_session, pending_job.job_id, "running")
    await async_session.refresh(pending_job)

    # Then set to completed
    await _update_job_status(async_session, pending_job.job_id, "completed")
    await async_session.refresh(pending_job)

    assert pending_job.status == "completed"
    assert pending_job.completed_at is not None
    assert isinstance(pending_job.completed_at, datetime)


@pytest.mark.asyncio
async def test_update_job_status_to_failed_with_error(async_session, pending_job):
    """Test updating job status to failed with error message."""
    error_msg = "Test error: workflow crashed"

    await _update_job_status(
        async_session, pending_job.job_id, "failed", error_message=error_msg
    )
    await async_session.refresh(pending_job)

    assert pending_job.status == "failed"
    assert pending_job.error_message == error_msg
    assert pending_job.completed_at is not None


@pytest.mark.asyncio
async def test_create_progress_record(async_session, pending_job):
    """Test creating initial progress record."""
    await _create_progress_record(async_session, pending_job.job_id)

    # Query progress record
    from sqlalchemy import select

    result = await async_session.execute(
        select(DesignProgress).where(DesignProgress.job_id == pending_job.job_id)
    )
    progress = result.scalar_one_or_none()

    assert progress is not None
    assert progress.job_id == pending_job.job_id
    assert progress.current_phase == 1
    assert progress.phase_name == "Initializing"
    assert progress.progress_percent == 0.0
    assert progress.screen_count == 0
    assert progress.completed_screens == 0


@pytest.mark.asyncio
async def test_update_progress(async_session, pending_job):
    """Test updating job progress."""
    # Create progress record first
    await _create_progress_record(async_session, pending_job.job_id)

    # Update progress
    await _update_progress(
        async_session,
        pending_job.job_id,
        phase=2,
        progress=35.0,
        phase_name="Phase 2: Option Generation",
    )

    # Query updated progress
    from sqlalchemy import select

    result = await async_session.execute(
        select(DesignProgress).where(DesignProgress.job_id == pending_job.job_id)
    )
    progress = result.scalar_one_or_none()

    assert progress.current_phase == 2
    assert progress.progress_percent == 35.0
    assert progress.phase_name == "Phase 2: Option Generation"
    assert progress.last_updated is not None


# ============================================================================
# Job Processing Tests (Mocked Workflow)
# ============================================================================


@pytest.mark.asyncio
async def test_process_job_success(async_session, pending_job):
    """Test successful job processing with mocked workflow."""
    # Mock the workflow execution
    mock_final_state = {
        "job_id": str(pending_job.job_id),
        "current_phase": 2,
        "progress_percent": 35.0,
        "phase_name": "Phases 1-2 Complete",
        "screen_count": 5,
        "options_provided_count": 15,
        "awaiting_feedback": False,
    }

    with patch("src.workers.job_processor.compile_workflow") as mock_compile:
        # Mock workflow ainvoke
        mock_workflow = AsyncMock()
        mock_workflow.ainvoke = AsyncMock(return_value=mock_final_state)
        mock_compile.return_value = mock_workflow

        # Process job
        await process_job(str(pending_job.job_id))

        # Verify workflow was called
        mock_compile.assert_called_once()
        mock_workflow.ainvoke.assert_called_once()

    # Verify job status updated to completed
    await async_session.refresh(pending_job)
    assert pending_job.status == "completed"

    # Verify progress record exists
    from sqlalchemy import select

    result = await async_session.execute(
        select(DesignProgress).where(DesignProgress.job_id == pending_job.job_id)
    )
    progress = result.scalar_one_or_none()
    assert progress is not None
    assert progress.current_phase == 2
    assert progress.progress_percent == 35.0


@pytest.mark.asyncio
async def test_process_job_awaiting_feedback(async_session, pending_job):
    """Test job processing pauses when awaiting user feedback."""
    mock_final_state = {
        "job_id": str(pending_job.job_id),
        "current_phase": 3,
        "progress_percent": 50.0,
        "phase_name": "Phase 3: Interactive Refinement",
        "awaiting_feedback": True,
        "current_screen_name": "Login Screen",
    }

    with patch("src.workers.job_processor.compile_workflow") as mock_compile:
        mock_workflow = AsyncMock()
        mock_workflow.ainvoke = AsyncMock(return_value=mock_final_state)
        mock_compile.return_value = mock_workflow

        await process_job(str(pending_job.job_id))

    # Verify job status is awaiting_feedback, not completed
    await async_session.refresh(pending_job)
    assert pending_job.status == "awaiting_feedback"


@pytest.mark.asyncio
async def test_process_job_workflow_failure(async_session, pending_job):
    """Test job processing handles workflow failures gracefully."""
    with patch("src.workers.job_processor.compile_workflow") as mock_compile:
        # Mock workflow to raise exception
        mock_workflow = AsyncMock()
        mock_workflow.ainvoke = AsyncMock(
            side_effect=Exception("Workflow execution failed")
        )
        mock_compile.return_value = mock_workflow

        # Process job (should not raise exception)
        await process_job(str(pending_job.job_id))

    # Verify job status updated to failed
    await async_session.refresh(pending_job)
    assert pending_job.status == "failed"
    assert "Workflow execution failed" in pending_job.error_message


@pytest.mark.asyncio
async def test_process_job_nonexistent_job():
    """Test processing non-existent job logs error and returns gracefully."""
    from src.database.connection import db_manager
    
    async with db_manager.get_async_session() as async_session:
        fake_job_id = str(uuid.uuid4())

        # Should not raise exception
        await process_job(fake_job_id)

        # Just verify no exception raised (already handled in function)


# ============================================================================
# Edge Case Tests
# ============================================================================


@pytest.mark.asyncio
async def test_process_job_invalid_uuid():
    """Test processing job with invalid UUID format."""
    with pytest.raises(ValueError):
        await process_job("not-a-valid-uuid")


@pytest.mark.asyncio
async def test_update_progress_without_phase_name(async_session, pending_job):
    """Test updating progress without optional phase_name."""
    await _create_progress_record(async_session, pending_job.job_id)

    # Update without phase_name
    await _update_progress(
        async_session, pending_job.job_id, phase=3, progress=50.0, phase_name=None
    )

    # Query progress
    from sqlalchemy import select

    result = await async_session.execute(
        select(DesignProgress).where(DesignProgress.job_id == pending_job.job_id)
    )
    progress = result.scalar_one_or_none()

    assert progress.current_phase == 3
    assert progress.progress_percent == 50.0
    # phase_name should still be "Initializing" from creation
    assert progress.phase_name == "Initializing"


@pytest.mark.asyncio
async def test_multiple_status_transitions(async_session, pending_job):
    """Test multiple job status transitions."""
    # pending -> running
    await _update_job_status(async_session, pending_job.job_id, "running")
    await async_session.refresh(pending_job)
    assert pending_job.status == "running"

    # running -> awaiting_feedback
    await _update_job_status(async_session, pending_job.job_id, "awaiting_feedback")
    await async_session.refresh(pending_job)
    assert pending_job.status == "awaiting_feedback"

    # awaiting_feedback -> running (resume)
    await _update_job_status(async_session, pending_job.job_id, "running")
    await async_session.refresh(pending_job)
    assert pending_job.status == "running"

    # running -> completed
    await _update_job_status(async_session, pending_job.job_id, "completed")
    await async_session.refresh(pending_job)
    assert pending_job.status == "completed"


# ============================================================================
# Integration Test with Real Workflow (Optional)
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.slow
@pytest.mark.skipif(
    True, reason="Skip real workflow test by default - requires full LangGraph setup"
)
async def test_process_job_real_workflow(async_session, pending_job):
    """
    Test job processing with real LangGraph workflow.

    This test is skipped by default. Run with: pytest -m slow
    """
    await process_job(str(pending_job.job_id))

    # Verify job completed (or awaiting feedback)
    await async_session.refresh(pending_job)
    assert pending_job.status in ["completed", "awaiting_feedback", "running"]
