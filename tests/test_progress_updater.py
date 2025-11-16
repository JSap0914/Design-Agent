"""
Unit tests for progress updater.

Tests real-time progress updates, WebSocket broadcasting, and error handling.
"""

import pytest
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from src.workers.progress_updater import (
    update_progress_from_state,
    broadcast_ascii_ui_update,
    set_websocket_manager,
    _websocket_manager,
)
from src.database.models import DesignJob, DesignProgress


# ============================================================================
# Test Fixtures
# ============================================================================


async def create_job_with_progress(async_session):
    """Create a job with initial progress record."""
    job = DesignJob(
        job_id=uuid.uuid4(),
        project_id="test-project-updater",
        user_id="test-user-updater",
        prd_content="# PRD\n\nTest PRD",
        trd_content="# TRD\n\nTest TRD",
        status="running",
        current_phase=1,
    )
    async_session.add(job)
    await async_session.flush()

    progress = DesignProgress(
        job_id=job.job_id,
        current_phase=1,
        phase_name="Initializing",
        progress_percent=0.0,
        screen_count=0,
        completed_screens=0,
    )
    async_session.add(progress)
    await async_session.commit()
    await async_session.refresh(job)
    await async_session.refresh(progress)

    return job, progress


@pytest.fixture
def mock_langgraph_state():
    """Create a mock LangGraph state."""
    return {
        "current_phase": 2,
        "phase_name": "Phase 2: Option Generation",
        "progress_percent": 35.0,
        "screen_count": 5,
        "completed_screens": 2,
    }


@pytest.fixture
def mock_websocket_manager():
    """Create a mock WebSocket manager."""
    manager = MagicMock()
    manager.broadcast_progress = AsyncMock()
    manager.broadcast_ascii_ui = AsyncMock()
    return manager


# ============================================================================
# WebSocket Manager Tests
# ============================================================================


def test_set_websocket_manager(mock_websocket_manager):
    """Test setting WebSocket manager."""
    set_websocket_manager(mock_websocket_manager)

    # Verify manager is set
    from src.workers import progress_updater

    assert progress_updater._websocket_manager is not None


def test_set_websocket_manager_none():
    """Test clearing WebSocket manager."""
    set_websocket_manager(None)

    from src.workers import progress_updater

    assert progress_updater._websocket_manager is None


# ============================================================================
# Progress Update Tests
# ============================================================================


@pytest.mark.asyncio
async def test_update_progress_from_state(async_session, job_with_progress, mock_langgraph_state):
    """Test updating progress from LangGraph state."""
    job, initial_progress = job_with_progress

    # Update progress
    await update_progress_from_state(str(job.job_id), mock_langgraph_state)

    # Verify progress updated
    await async_session.refresh(initial_progress)

    assert initial_progress.current_phase == 2
    assert initial_progress.phase_name == "Phase 2: Option Generation"
    assert initial_progress.progress_percent == 35.0
    assert initial_progress.screen_count == 5
    assert initial_progress.completed_screens == 2
    assert initial_progress.last_updated is not None


@pytest.mark.asyncio
async def test_update_progress_with_partial_state(async_session, job_with_progress):
    """Test updating progress with partial state data."""
    job, initial_progress = job_with_progress

    partial_state = {
        "current_phase": 3,
        "progress_percent": 50.0,
        # Missing phase_name, screen_count, etc. - should use defaults
    }

    await update_progress_from_state(str(job.job_id), partial_state)

    # Verify progress updated with defaults
    await async_session.refresh(initial_progress)

    assert initial_progress.current_phase == 3
    assert initial_progress.progress_percent == 50.0
    assert initial_progress.phase_name == "Processing"  # Default value
    assert initial_progress.screen_count == 0  # Default value


@pytest.mark.asyncio
async def test_update_progress_with_empty_state(async_session, job_with_progress):
    """Test updating progress with empty state uses defaults."""
    job, initial_progress = job_with_progress

    empty_state = {}

    await update_progress_from_state(str(job.job_id), empty_state)

    # Verify defaults applied
    await async_session.refresh(initial_progress)

    assert initial_progress.current_phase == 0  # Default
    assert initial_progress.progress_percent == 0.0  # Default
    assert initial_progress.phase_name == "Processing"  # Default


@pytest.mark.asyncio
async def test_update_progress_nonexistent_job():
    """Test updating progress for non-existent job doesn't raise exception."""
    from src.database.connection import db_manager
    
    async with db_manager.get_async_session() as async_session:
        fake_job_id = str(uuid.uuid4())
        state = {
            "current_phase": 2,
            "progress_percent": 35.0,
        }

        # Should not raise exception (error is logged)
        await update_progress_from_state(fake_job_id, state)


@pytest.mark.asyncio
async def test_update_progress_invalid_uuid():
    """Test updating progress with invalid UUID logs error."""
    state = {"current_phase": 2}

    # Should not raise exception (error is logged)
    await update_progress_from_state("not-a-uuid", state)


# ============================================================================
# WebSocket Broadcasting Tests
# ============================================================================


@pytest.mark.asyncio
async def test_update_progress_broadcasts_websocket(
    async_session, job_with_progress, mock_langgraph_state, mock_websocket_manager
):
    """Test progress update broadcasts via WebSocket when manager is set."""
    job, _ = job_with_progress

    # Set WebSocket manager
    set_websocket_manager(mock_websocket_manager)

    # Update progress
    await update_progress_from_state(str(job.job_id), mock_langgraph_state)

    # Verify WebSocket broadcast was called
    mock_websocket_manager.broadcast_progress.assert_called_once()
    call_args = mock_websocket_manager.broadcast_progress.call_args
    assert call_args[0][0] == str(job.job_id)
    assert call_args[0][1]["current_phase"] == 2

    # Clean up
    set_websocket_manager(None)


@pytest.mark.asyncio
async def test_update_progress_without_websocket_manager(
    async_session, job_with_progress, mock_langgraph_state
):
    """Test progress update works without WebSocket manager."""
    job, initial_progress = job_with_progress

    # Ensure no WebSocket manager
    set_websocket_manager(None)

    # Update progress (should work without WebSocket)
    await update_progress_from_state(str(job.job_id), mock_langgraph_state)

    # Verify progress updated
    await async_session.refresh(initial_progress)
    assert initial_progress.current_phase == 2


@pytest.mark.asyncio
async def test_update_progress_websocket_failure(
    async_session, job_with_progress, mock_langgraph_state, mock_websocket_manager
):
    """Test progress update continues even if WebSocket broadcast fails."""
    job, initial_progress = job_with_progress

    # Set WebSocket manager to fail
    mock_websocket_manager.broadcast_progress = AsyncMock(
        side_effect=Exception("WebSocket error")
    )
    set_websocket_manager(mock_websocket_manager)

    # Update progress (should not raise exception)
    await update_progress_from_state(str(job.job_id), mock_langgraph_state)

    # Verify progress still updated despite WebSocket failure
    await async_session.refresh(initial_progress)
    assert initial_progress.current_phase == 2

    # Clean up
    set_websocket_manager(None)


# ============================================================================
# ASCII UI Broadcasting Tests
# ============================================================================


@pytest.mark.asyncio
async def test_broadcast_ascii_ui_update(mock_websocket_manager):
    """Test broadcasting ASCII UI update via WebSocket."""
    set_websocket_manager(mock_websocket_manager)

    job_id = str(uuid.uuid4())
    screen_name = "Login Screen"
    ascii_ui = """
┌──────────────────────────────────────┐
│  📱 MyApp                    ☰       │
├──────────────────────────────────────┤
│                                      │
│  Welcome back!                       │
│                                      │
└──────────────────────────────────────┘
"""

    await broadcast_ascii_ui_update(job_id, screen_name, ascii_ui)

    # Verify WebSocket broadcast called
    mock_websocket_manager.broadcast_ascii_ui.assert_called_once_with(
        job_id, screen_name, ascii_ui
    )

    # Clean up
    set_websocket_manager(None)


@pytest.mark.asyncio
async def test_broadcast_ascii_ui_without_manager():
    """Test broadcasting ASCII UI without WebSocket manager logs debug."""
    set_websocket_manager(None)

    job_id = str(uuid.uuid4())
    screen_name = "Dashboard"
    ascii_ui = "# ASCII UI"

    # Should not raise exception
    await broadcast_ascii_ui_update(job_id, screen_name, ascii_ui)


@pytest.mark.asyncio
async def test_broadcast_ascii_ui_failure(mock_websocket_manager):
    """Test ASCII UI broadcast continues even if WebSocket fails."""
    mock_websocket_manager.broadcast_ascii_ui = AsyncMock(
        side_effect=Exception("WebSocket error")
    )
    set_websocket_manager(mock_websocket_manager)

    job_id = str(uuid.uuid4())
    screen_name = "Settings"
    ascii_ui = "# ASCII UI"

    # Should not raise exception (error is logged as warning)
    await broadcast_ascii_ui_update(job_id, screen_name, ascii_ui)

    # Clean up
    set_websocket_manager(None)


# ============================================================================
# Multiple Updates Test
# ============================================================================


@pytest.mark.asyncio
async def test_multiple_progress_updates(async_session, job_with_progress):
    """Test multiple sequential progress updates."""
    job, initial_progress = job_with_progress

    phases = [
        {"current_phase": 1, "progress_percent": 10.0, "phase_name": "Phase 1"},
        {"current_phase": 2, "progress_percent": 35.0, "phase_name": "Phase 2"},
        {"current_phase": 3, "progress_percent": 50.0, "phase_name": "Phase 3"},
        {"current_phase": 4, "progress_percent": 70.0, "phase_name": "Phase 4"},
        {"current_phase": 5, "progress_percent": 85.0, "phase_name": "Phase 5"},
        {"current_phase": 6, "progress_percent": 100.0, "phase_name": "Phase 6"},
    ]

    for state in phases:
        await update_progress_from_state(str(job.job_id), state)
        await async_session.refresh(initial_progress)

        assert initial_progress.current_phase == state["current_phase"]
        assert initial_progress.progress_percent == state["progress_percent"]
        assert initial_progress.phase_name == state["phase_name"]


# ============================================================================
# Edge Case Tests
# ============================================================================


@pytest.mark.asyncio
async def test_update_progress_with_negative_values(async_session, job_with_progress):
    """Test updating progress with negative values (edge case)."""
    job, initial_progress = job_with_progress

    state = {
        "current_phase": -1,
        "progress_percent": -10.0,
        "screen_count": -5,
    }

    # Should not raise exception
    await update_progress_from_state(str(job.job_id), state)

    # Verify values are stored as-is (validation should happen at state level)
    await async_session.refresh(initial_progress)
    assert initial_progress.current_phase == -1


@pytest.mark.asyncio
async def test_update_progress_with_oversized_values(async_session, job_with_progress):
    """Test updating progress with values over 100% (edge case)."""
    job, initial_progress = job_with_progress

    state = {
        "current_phase": 10,
        "progress_percent": 150.0,
        "screen_count": 1000,
    }

    await update_progress_from_state(str(job.job_id), state)

    # Verify values stored (validation at display layer)
    await async_session.refresh(initial_progress)
    assert initial_progress.progress_percent == 150.0


@pytest.mark.asyncio
async def test_concurrent_progress_updates(async_session, job_with_progress):
    """Test handling concurrent progress updates."""
    import asyncio

    job, initial_progress = job_with_progress

    states = [
        {"current_phase": 2, "progress_percent": 20.0},
        {"current_phase": 2, "progress_percent": 25.0},
        {"current_phase": 2, "progress_percent": 30.0},
    ]

    # Run updates concurrently
    await asyncio.gather(
        *[update_progress_from_state(str(job.job_id), state) for state in states]
    )

    # Verify final state (one of the updates should win)
    await async_session.refresh(initial_progress)
    assert initial_progress.current_phase == 2
    assert initial_progress.progress_percent in [20.0, 25.0, 30.0]
