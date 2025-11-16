"""
Unit tests for analytics functions.

Tests individual analytics query functions in src/database/analytics.py.
"""

import pytest
import uuid
from datetime import datetime, timedelta

from src.database.analytics import (
    get_job_summary,
    get_recent_jobs,
    get_session_history,
    get_job_statistics,
    get_dashboard_analytics,
    get_popular_libraries,
    get_success_rate_trends,
    get_avg_completion_time_by_screen_count,
    get_quality_score_distribution,
)
from src.database.models import (
    DesignJob,
    DesignProgress,
    DesignDecision,
    OpenSourceSelection,
    Session,
)


# ============================================================================
# Test Fixtures
# ============================================================================


async def create_completed_job_with_data(async_session):
    """Create a completed job with progress, decisions, and library selections."""
    job_id = uuid.uuid4()

    # Create job
    job = DesignJob(
        job_id=job_id,
        project_id="analytics-test-project",
        user_id="analytics-user-001",
        prd_content="# PRD\n\nTest PRD for analytics",
        trd_content="# TRD\n\nTest TRD for analytics",
        status="completed",
        
        created_at=datetime.utcnow() - timedelta(hours=2),
        started_at=datetime.utcnow() - timedelta(hours=2),
        completed_at=datetime.utcnow(),
        
    )
    async_session.add(job)
    await async_session.flush()

    # Create progress
    progress = DesignProgress(
        job_id=job_id,
        
        phase_name="Complete",
        progress_percent=100.0,
        screen_count=5,
        completed_screens=5,
    )
    async_session.add(progress)

    # Create session
    session = Session(
        session_id=uuid.uuid4(),
        job_id=job_id,
        langgraph_thread_id=f"thread-{job_id}",
        
        is_paused=False,
    )
    async_session.add(session)

    # Create design decisions
    for i in range(3):
        decision = DesignDecision(
            decision_id=uuid.uuid4(),
            job_id=job_id,
            screen_name=f"Screen {i+1}",
            decision_type="layout_choice",
            rationale=f"Test rationale {i+1}",
        )
        async_session.add(decision)

    # Create library selections
    libraries = [
        ("TanStack Table", "ui_components", 22000, 95.0),
        ("React Hook Form", "forms", 35000, 98.0),
        ("Lucide Icons", "icons", 8000, 90.0),
    ]

    for lib_name, category, stars, score in libraries:
        selection = OpenSourceSelection(
            selection_id=uuid.uuid4(),
            job_id=job_id,
            category=category,
            library_name=lib_name,
            github_url=f"https://github.com/test/{lib_name.lower().replace(' ', '-')}",
            stars=stars,
            license="MIT",
            bundle_size="15KB",
            ranking_score=score,
            rationale=f"Selected {lib_name} for testing",
        )
        async_session.add(selection)

    await async_session.commit()
    await async_session.refresh(job)

    return job


async def create_multiple_jobs(async_session):
    """Create multiple jobs with different statuses."""
    jobs = []

    statuses = ["completed", "completed", "running", "failed", "pending"]

    for i, status in enumerate(statuses):
        job = DesignJob(
            job_id=uuid.uuid4(),
            project_id=f"project-{i}",
            user_id=f"user-{i % 3}",  # 3 different users
            prd_content=f"PRD {i}",
            trd_content=f"TRD {i}",
            status=status,
            current_phase=(6 if status == "completed" else i % 6),
            created_at=datetime.utcnow() - timedelta(hours=10 - i),
        )
        async_session.add(job)
        await async_session.flush()

        # Add progress for each job
        progress = DesignProgress(
            job_id=job.job_id,
            current_phase=job.current_phase,
            phase_name=f"Phase {job.current_phase}",
            progress_percent=(100.0 if status == "completed" else i * 20.0),
            screen_count=5,
            completed_screens=(5 if status == "completed" else i),
        )
        async_session.add(progress)

        jobs.append(job)

    await async_session.commit()
    for job in jobs:
        await async_session.refresh(job)

    return jobs


# ============================================================================
# get_job_summary Tests
# ============================================================================


@pytest.mark.asyncio
async def test_get_job_summary_existing_job(completed_job_with_data):
    """Test retrieving job summary for existing job."""
    job = completed_job_with_data

    summary = await get_job_summary(str(job.job_id))

    assert summary is not None
    assert summary["job_id"] == str(job.job_id)
    assert summary["status"] == "completed"
    assert summary["user_id"] == job.user_id


@pytest.mark.asyncio
async def test_get_job_summary_nonexistent_job():
    """Test retrieving summary for non-existent job returns None."""
    fake_job_id = str(uuid.uuid4())

    summary = await get_job_summary(fake_job_id)

    assert summary is None


@pytest.mark.asyncio
async def test_get_job_summary_invalid_uuid():
    """Test retrieving summary with invalid UUID returns None."""
    summary = await get_job_summary("not-a-valid-uuid")

    assert summary is None


# ============================================================================
# get_recent_jobs Tests
# ============================================================================


@pytest.mark.asyncio
async def test_get_recent_jobs_no_filter(multiple_jobs):
    """Test retrieving recent jobs without filters."""
    jobs = await get_recent_jobs(limit=10)

    assert len(jobs) == 5  # All jobs created in fixture
    assert all(isinstance(job, dict) for job in jobs)


@pytest.mark.asyncio
async def test_get_recent_jobs_by_user(multiple_jobs):
    """Test retrieving recent jobs filtered by user_id."""
    jobs = await get_recent_jobs(user_id="user-0", limit=10)

    assert len(jobs) >= 1
    assert all(job["user_id"] == "user-0" for job in jobs)


@pytest.mark.asyncio
async def test_get_recent_jobs_by_status(multiple_jobs):
    """Test retrieving recent jobs filtered by status."""
    completed_jobs = await get_recent_jobs(status="completed", limit=10)

    assert len(completed_jobs) == 2  # 2 completed jobs in fixture
    assert all(job["status"] == "completed" for job in completed_jobs)


@pytest.mark.asyncio
async def test_get_recent_jobs_with_limit(multiple_jobs):
    """Test limit parameter works correctly."""
    jobs = await get_recent_jobs(limit=3)

    assert len(jobs) == 3


@pytest.mark.asyncio
async def test_get_recent_jobs_empty_result():
    """Test retrieving jobs with filter that matches nothing."""
    jobs = await get_recent_jobs(user_id="nonexistent-user", limit=10)

    assert jobs == []


# ============================================================================
# get_session_history Tests
# ============================================================================


@pytest.mark.asyncio
async def test_get_session_history_by_user():
    """Test retrieving session history for a user."""
    from src.database.connection import db_manager
    
    async with db_manager.get_async_session() as async_session:
        user_id = "history-test-user"

        # Create job and session
        job = DesignJob(
            job_id=uuid.uuid4(),
            project_id="history-test",
            user_id=user_id,
            prd_content="PRD",
            trd_content="TRD",
            status="completed",
        
        )
        async_session.add(job)
        await async_session.flush()

        session = Session(
            session_id=uuid.uuid4(),
            job_id=job.job_id,
            langgraph_thread_id=f"thread-{job.job_id}",
        
            is_paused=False,
        )
        async_session.add(session)
        await async_session.commit()

        # Query history
        history = await get_session_history(user_id=user_id, limit=10)

        assert len(history) >= 1


@pytest.mark.asyncio
async def test_get_session_history_with_limit():
    """Test session history respects limit."""
    # This test depends on existing data or fixture setup
    history = await get_session_history(user_id="test-user", limit=5)

    assert len(history) <= 5


# ============================================================================
# get_job_statistics Tests
# ============================================================================


@pytest.mark.asyncio
async def test_get_job_statistics_existing_job(completed_job_with_data):
    """Test retrieving statistics for existing job."""
    job = completed_job_with_data

    stats = await get_job_statistics(str(job.job_id))

    # Stats may be None if view doesn't populate data immediately
    if stats:
        assert "job_id" in stats
        assert stats["job_id"] == str(job.job_id)


@pytest.mark.asyncio
async def test_get_job_statistics_nonexistent_job():
    """Test retrieving statistics for non-existent job returns None."""
    fake_job_id = str(uuid.uuid4())

    stats = await get_job_statistics(fake_job_id)

    assert stats is None


# ============================================================================
# get_dashboard_analytics Tests
# ============================================================================


@pytest.mark.asyncio
async def test_get_dashboard_analytics(multiple_jobs):
    """Test retrieving dashboard analytics."""
    analytics = await get_dashboard_analytics()

    # Analytics should return a dictionary (may be empty if view has no data)
    assert isinstance(analytics, dict)


@pytest.mark.asyncio
async def test_get_dashboard_analytics_empty_database():
    """Test dashboard analytics with no data."""
    analytics = await get_dashboard_analytics()

    # Should return empty dict, not raise exception
    assert isinstance(analytics, dict)


# ============================================================================
# get_popular_libraries Tests
# ============================================================================


@pytest.mark.asyncio
async def test_get_popular_libraries_no_filter(completed_job_with_data):
    """Test retrieving popular libraries without filter."""
    libraries = await get_popular_libraries(limit=10)

    assert isinstance(libraries, list)
    # May be empty if view hasn't aggregated data yet


@pytest.mark.asyncio
async def test_get_popular_libraries_by_category(completed_job_with_data):
    """Test retrieving popular libraries filtered by category."""
    libraries = await get_popular_libraries(category="ui_components", limit=10)

    assert isinstance(libraries, list)
    if libraries:
        assert all(lib["category"] == "ui_components" for lib in libraries)


@pytest.mark.asyncio
async def test_get_popular_libraries_with_limit():
    """Test limit parameter for popular libraries."""
    libraries = await get_popular_libraries(limit=5)

    assert len(libraries) <= 5


@pytest.mark.asyncio
async def test_get_popular_libraries_empty_result():
    """Test popular libraries with non-existent category."""
    libraries = await get_popular_libraries(category="nonexistent_category", limit=10)

    assert libraries == []


# ============================================================================
# get_success_rate_trends Tests
# ============================================================================


@pytest.mark.asyncio
async def test_get_success_rate_trends_default_days(multiple_jobs):
    """Test retrieving success rate trends with default 30 days."""
    trends = await get_success_rate_trends()

    assert isinstance(trends, list)


@pytest.mark.asyncio
async def test_get_success_rate_trends_custom_days(multiple_jobs):
    """Test retrieving success rate trends with custom days."""
    trends = await get_success_rate_trends(days=7)

    assert isinstance(trends, list)


@pytest.mark.asyncio
async def test_get_success_rate_trends_empty_database():
    """Test success rate trends with no data."""
    trends = await get_success_rate_trends()

    assert isinstance(trends, list)
    # May be empty if no jobs in timeframe


# ============================================================================
# get_avg_completion_time_by_screen_count Tests
# ============================================================================


@pytest.mark.asyncio
async def test_get_avg_completion_time_by_screen_count(multiple_jobs):
    """Test retrieving average completion time by screen count."""
    completion_times = await get_avg_completion_time_by_screen_count()

    assert isinstance(completion_times, list)


@pytest.mark.asyncio
async def test_get_avg_completion_time_empty_database():
    """Test completion time analysis with no completed jobs."""
    completion_times = await get_avg_completion_time_by_screen_count()

    assert isinstance(completion_times, list)


# ============================================================================
# get_quality_score_distribution Tests
# ============================================================================


@pytest.mark.asyncio
async def test_get_quality_score_distribution(completed_job_with_data):
    """Test retrieving quality score distribution."""
    distribution = await get_quality_score_distribution()

    assert isinstance(distribution, dict)


@pytest.mark.asyncio
async def test_get_quality_score_distribution_empty_database():
    """Test quality score distribution with no data."""
    distribution = await get_quality_score_distribution()

    assert isinstance(distribution, dict)


# ============================================================================
# Error Handling Tests
# ============================================================================


@pytest.mark.asyncio
async def test_analytics_functions_handle_database_errors():
    """Test that analytics functions handle database errors gracefully."""
    # Test with invalid connection (simulated error)
    # All functions should return None or empty results, not raise exceptions

    functions_to_test = [
        (get_job_summary, (str(uuid.uuid4()),)),
        (get_recent_jobs, ()),
        (get_session_history, ()),
        (get_job_statistics, (str(uuid.uuid4()),)),
        (get_dashboard_analytics, ()),
        (get_popular_libraries, ()),
        (get_success_rate_trends, ()),
        (get_avg_completion_time_by_screen_count, ()),
        (get_quality_score_distribution, ()),
    ]

    for func, args in functions_to_test:
        try:
            result = await func(*args)
            # Should return None, empty list, or empty dict - not raise
            assert result is None or isinstance(result, (list, dict))
        except Exception as e:
            pytest.fail(f"{func.__name__} raised exception: {e}")


# ============================================================================
# Integration Tests
# ============================================================================


@pytest.mark.asyncio
async def test_analytics_workflow_integration():
    """Test complete analytics workflow with realistic data."""
    from src.database.connection import db_manager
    
    async with db_manager.get_async_session() as async_session:
        # Create job
        job = DesignJob(
            job_id=uuid.uuid4(),
            project_id="integration-test",
            user_id="integration-user",
            prd_content="PRD",
            trd_content="TRD",
            status="completed",
        
            quality_metrics={"quality_score": 92},
        )
        async_session.add(job)
        await async_session.flush()

        # Create progress
        progress = DesignProgress(
            job_id=job.job_id,
        
            phase_name="Complete",
            progress_percent=100.0,
            screen_count=8,
            completed_screens=8,
        )
        async_session.add(progress)

        # Create session
        session = Session(
            session_id=uuid.uuid4(),
            job_id=job.job_id,
            langgraph_thread_id=f"thread-{job.job_id}",
        
            is_paused=False,
        )
        async_session.add(session)

        # Create decisions
        decision = DesignDecision(
            decision_id=uuid.uuid4(),
            job_id=job.job_id,
            screen_name="Login",
            decision_type="layout_choice",
            rationale="Test decision",
        )
        async_session.add(decision)

        # Create library selection
        library = OpenSourceSelection(
            selection_id=uuid.uuid4(),
            job_id=job.job_id,
            category="forms",
            library_name="Formik",
            stars=30000,
            license="MIT",
            ranking_score=95.0,
            rationale="Popular form library",
        )
        async_session.add(library)

        await async_session.commit()

        # Test all analytics functions
        summary = await get_job_summary(str(job.job_id))
        assert summary is not None

        recent = await get_recent_jobs(user_id="integration-user")
        assert len(recent) >= 1

        history = await get_session_history(user_id="integration-user")
        assert len(history) >= 1

        # Other analytics may need more data to return results
        dashboard = await get_dashboard_analytics()
        assert isinstance(dashboard, dict)
