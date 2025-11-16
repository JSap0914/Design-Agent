"""
Load tests for concurrent job processing.

Tests system behavior under high load with multiple simultaneous jobs.
"""

import pytest
import asyncio
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, patch, MagicMock

from src.langgraph.state import DesignAgentState
from src.langgraph.nodes.extract_screens import extract_screens
from src.langgraph.nodes.generate_options import generate_options
from src.database.connection import db_manager
from src.database.models import DesignJob


# ============================================================================
# Concurrent Workflow Execution Tests
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.load
async def test_concurrent_10_jobs():
    """Test 10 jobs running concurrently."""
    num_jobs = 10

    async def run_single_job(job_num: int):
        """Execute a single job workflow."""
        state: DesignAgentState = {
            "job_id": f"load-test-{job_num}",
            "prd_content": f"# Job {job_num} PRD\n\nScreens: Login, Dashboard, Settings",
            "trd_content": "# Tech: React + TypeScript",
            "extracted_screens": [],
            "current_phase": 0,
        }

        with patch("src.langgraph.nodes.extract_screens.generate_json_async", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = {
                "screens": ["Login", "Dashboard", "Settings"],
                "rationale": f"Job {job_num} screens",
            }

            result = await extract_screens(state)
            return result

    # Execute all jobs concurrently
    start_time = asyncio.get_event_loop().time()
    results = await asyncio.gather(*[run_single_job(i) for i in range(num_jobs)])
    end_time = asyncio.get_event_loop().time()

    # Verify all completed successfully
    assert len(results) == num_jobs
    assert all(r["current_phase"] == 1 for r in results)
    assert all(len(r["extracted_screens"]) == 3 for r in results)

    # Performance assertion
    elapsed = end_time - start_time
    assert elapsed < 30.0, f"10 concurrent jobs took {elapsed:.2f}s (expected < 30s)"


@pytest.mark.asyncio
@pytest.mark.load
async def test_concurrent_50_jobs():
    """Test 50 jobs running concurrently (stress test)."""
    num_jobs = 50

    async def run_extract_phase(job_num: int):
        """Execute Phase 1 only."""
        state: DesignAgentState = {
            "job_id": f"stress-test-{job_num}",
            "prd_content": f"# Stress Test {job_num}\n\nScreens: S1, S2, S3",
            "trd_content": "# Tech: React",
            "extracted_screens": [],
            "current_phase": 0,
        }

        with patch("src.langgraph.nodes.extract_screens.generate_json_async", new_callable=AsyncMock) as mock:
            mock.return_value = {"screens": ["S1", "S2", "S3"], "rationale": "Test"}
            return await extract_screens(state)

    start_time = asyncio.get_event_loop().time()
    results = await asyncio.gather(*[run_extract_phase(i) for i in range(num_jobs)])
    end_time = asyncio.get_event_loop().time()

    # Verify completion
    assert len(results) == num_jobs
    assert all(r["current_phase"] == 1 for r in results)

    elapsed = end_time - start_time
    print(f"\n50 concurrent jobs completed in {elapsed:.2f}s")


@pytest.mark.asyncio
@pytest.mark.load
async def test_concurrent_jobs_with_failures():
    """Test concurrent jobs with some failures."""
    num_jobs = 20
    failure_rate = 0.3  # 30% failure rate

    async def run_job_with_possible_failure(job_num: int):
        """Execute job that may fail."""
        state: DesignAgentState = {
            "job_id": f"failure-test-{job_num}",
            "prd_content": "# Test PRD",
            "trd_content": "# Tech: React",
            "extracted_screens": [],
            "current_phase": 0,
        }

        with patch("src.langgraph.nodes.extract_screens.generate_json_async", new_callable=AsyncMock) as mock:
            # Simulate failures for some jobs
            if job_num % 3 == 0:  # Every 3rd job fails
                mock.side_effect = Exception("LLM timeout")
            else:
                mock.return_value = {"screens": ["S1"], "rationale": "Success"}

            return await extract_screens(state)

    results = await asyncio.gather(*[run_job_with_possible_failure(i) for i in range(num_jobs)], return_exceptions=False)

    # Count successes and failures
    successes = sum(1 for r in results if r.get("current_phase") == 1)
    failures = sum(1 for r in results if "errors" in r)

    print(f"\nSuccesses: {successes}, Failures: {failures}")
    assert successes + failures == num_jobs


# ============================================================================
# Database Connection Pool Tests
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.load
async def test_database_connection_pool_under_load():
    """Test database connection pooling with concurrent requests."""
    num_concurrent = 30

    async def create_job_in_db(job_num: int):
        """Create a job record in database."""
        job_id = uuid.uuid4()

        async with db_manager.get_async_session() as session:
            new_job = DesignJob(
                job_id=job_id,
                project_id=f"load-test-{job_num}",
                user_id="load-test-user",
                prd_content="# Test PRD",
                trd_content="# Test TRD",
                status="pending",
                created_at=datetime.utcnow(),
            )
            session.add(new_job)
            await session.commit()
            return job_id

    # Create 30 jobs concurrently
    start_time = asyncio.get_event_loop().time()
    job_ids = await asyncio.gather(*[create_job_in_db(i) for i in range(num_concurrent)])
    end_time = asyncio.get_event_loop().time()

    assert len(job_ids) == num_concurrent

    # Cleanup
    async with db_manager.get_async_session() as session:
        from sqlalchemy import text
        for job_id in job_ids:
            await session.execute(
                text("DELETE FROM shared.design_jobs WHERE job_id = :job_id"),
                {"job_id": job_id}
            )
        await session.commit()

    elapsed = end_time - start_time
    print(f"\n30 concurrent DB inserts completed in {elapsed:.2f}s")


# ============================================================================
# Memory Usage Tests
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.load
async def test_memory_usage_large_prd():
    """Test memory efficiency with large PRD content."""
    # Create a large PRD (simulate complex project)
    large_prd = "# Large Project PRD\n\n" + ("## Screen\nDescription: " + "x" * 1000 + "\n") * 50

    state: DesignAgentState = {
        "job_id": "memory-test",
        "prd_content": large_prd,
        "trd_content": "# Tech: React",
        "extracted_screens": [],
        "current_phase": 0,
    }

    with patch("src.langgraph.nodes.extract_screens.generate_json_async", new_callable=AsyncMock) as mock:
        mock.return_value = {"screens": [f"Screen {i}" for i in range(12)], "rationale": "12 screens"}

        result = await extract_screens(state)

        assert len(result["extracted_screens"]) == 12
        # Verify state doesn't grow excessively
        import sys
        state_size = sys.getsizeof(result)
        assert state_size < 1_000_000, f"State size too large: {state_size} bytes"


@pytest.mark.asyncio
@pytest.mark.load
async def test_memory_usage_many_screens():
    """Test handling maximum number of screens."""
    state: DesignAgentState = {
        "job_id": "max-screens-test",
        "prd_content": "# Test PRD",
        "trd_content": "# Tech: React",
        "extracted_screens": [f"Screen {i}" for i in range(12)],  # Max screens
        "current_phase": 1,
    }

    with patch("src.langgraph.nodes.generate_options.llm_client.complete_with_json", new_callable=AsyncMock) as mock:
        mock.return_value = {
            "options": [
                {
                    "option_number": 1,
                    "layout_description": "Layout",
                    "key_features": ["F"],
                    "pros": ["P"],
                    "cons": ["C"],
                    "recommended": True,
                },
                {
                    "option_number": 2,
                    "layout_description": "Layout 2",
                    "key_features": ["F"],
                    "pros": ["P"],
                    "cons": ["C"],
                    "recommended": False,
                },
            ]
        }

        result = await generate_options(state)

        # Should handle 12 screens without issues
        assert len(result["design_options"]) == 12
        # Verify LLM called 12 times (once per screen)
        assert mock.call_count == 12


# ============================================================================
# Rate Limiting Tests
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.load
async def test_llm_rate_limiting_simulation():
    """Test behavior when LLM rate limits are hit."""
    num_requests = 20
    rate_limit_after = 10  # Simulate rate limit after 10 requests

    call_count = 0

    async def mock_llm_with_rate_limit(*args, **kwargs):
        """Mock LLM that rate limits after N calls."""
        nonlocal call_count
        call_count += 1

        if call_count > rate_limit_after:
            # Simulate rate limit error
            await asyncio.sleep(0.1)  # Small delay
            raise Exception("Rate limit exceeded - too many requests")
        else:
            return {"screens": ["S1"], "rationale": "Success"}

    async def run_job(job_num: int):
        """Execute job that may hit rate limit."""
        state: DesignAgentState = {
            "job_id": f"rate-limit-{job_num}",
            "prd_content": "# Test",
            "trd_content": "# Tech",
            "extracted_screens": [],
            "current_phase": 0,
        }

        with patch("src.langgraph.nodes.extract_screens.generate_json_async", new_callable=AsyncMock) as mock:
            mock.side_effect = mock_llm_with_rate_limit

            try:
                return await extract_screens(state)
            except Exception:
                # Rate limit hit - return partial result
                return {"error": "rate_limit", "job_id": state["job_id"]}

    results = await asyncio.gather(*[run_job(i) for i in range(num_requests)], return_exceptions=False)

    successes = sum(1 for r in results if r.get("current_phase") == 1)
    rate_limited = sum(1 for r in results if r.get("error") == "rate_limit")

    print(f"\nSuccesses: {successes}, Rate Limited: {rate_limited}")
    assert successes + rate_limited == num_requests


# ============================================================================
# Throughput Tests
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.load
async def test_throughput_jobs_per_second():
    """Test system throughput (jobs completed per second)."""
    num_jobs = 100
    batch_size = 10

    async def process_batch(start_idx: int):
        """Process a batch of jobs."""
        async def quick_job(job_num: int):
            state: DesignAgentState = {
                "job_id": f"throughput-{job_num}",
                "prd_content": "# Quick PRD",
                "trd_content": "# Tech: React",
                "extracted_screens": [],
                "current_phase": 0,
            }

            with patch("src.langgraph.nodes.extract_screens.generate_json_async", new_callable=AsyncMock) as mock:
                mock.return_value = {"screens": ["S1"], "rationale": "Fast"}
                return await extract_screens(state)

        return await asyncio.gather(*[quick_job(start_idx + i) for i in range(batch_size)])

    start_time = asyncio.get_event_loop().time()

    # Process in batches
    all_results = []
    for batch_start in range(0, num_jobs, batch_size):
        batch_results = await process_batch(batch_start)
        all_results.extend(batch_results)

    end_time = asyncio.get_event_loop().time()
    elapsed = end_time - start_time

    # Calculate throughput
    throughput = num_jobs / elapsed
    print(f"\nProcessed {num_jobs} jobs in {elapsed:.2f}s")
    print(f"Throughput: {throughput:.2f} jobs/second")

    assert len(all_results) == num_jobs


# ============================================================================
# Stress Recovery Tests
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.load
async def test_recovery_after_load_spike():
    """Test system recovery after sudden load spike."""
    # Phase 1: Normal load
    async def normal_job(job_num: int):
        state: DesignAgentState = {
            "job_id": f"normal-{job_num}",
            "prd_content": "# Test",
            "trd_content": "# Tech",
            "extracted_screens": [],
            "current_phase": 0,
        }

        with patch("src.langgraph.nodes.extract_screens.generate_json_async", new_callable=AsyncMock) as mock:
            mock.return_value = {"screens": ["S1"], "rationale": "Normal"}
            return await extract_screens(state)

    # Normal: 5 jobs
    normal_results = await asyncio.gather(*[normal_job(i) for i in range(5)])
    assert all(r["current_phase"] == 1 for r in normal_results)

    # Phase 2: Sudden spike to 50 jobs
    spike_results = await asyncio.gather(*[normal_job(i + 100) for i in range(50)])
    assert len(spike_results) == 50

    # Phase 3: Back to normal (verify system recovered)
    recovery_results = await asyncio.gather(*[normal_job(i + 200) for i in range(5)])
    assert all(r["current_phase"] == 1 for r in recovery_results)

    print("\n✅ System recovered successfully after load spike")


# ============================================================================
# Full Workflow Load Tests (Phase 1-6) - Week 7 Task 9
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.load
async def test_concurrent_full_workflow_10_jobs(async_session):
    """Test 10 concurrent jobs through complete Phase 1-6 workflow."""
    from src.workers.job_processor import process_job

    num_jobs = 10
    jobs = []

    # Create jobs in database
    for i in range(num_jobs):
        job = DesignJob(
            job_id=uuid.uuid4(),
            project_id=f"load-full-{i}",
            user_id=f"load-user-{i % 3}",
            prd_content=f"# Load Test {i}\n\nScreens: Login, Dashboard, Settings",
            trd_content="# Tech: React + TypeScript + Tailwind",
            status="pending",
            current_phase=0,
        )
        async_session.add(job)
        jobs.append(job)

    await async_session.commit()

    # Mock LangGraph workflow for all phases
    with patch("src.workers.job_processor.compile_workflow") as mock_compile:

        def mock_invoke(state, config):
            return {
                "job_id": state["job_id"],
                "current_phase": 6,
                "progress_percent": 100.0,
                "phase_name": "Complete",
                "screen_count": 3,
                "completed_screens": 3,
                "documents_generated": 6,
                "awaiting_feedback": False,
            }

        mock_workflow = AsyncMock()
        mock_workflow.ainvoke = AsyncMock(side_effect=mock_invoke)
        mock_compile.return_value = mock_workflow

        # Process all jobs concurrently
        start_time = asyncio.get_event_loop().time()
        await asyncio.gather(*[process_job(str(job.job_id)) for job in jobs])
        end_time = asyncio.get_event_loop().time()

    # Verify all jobs completed
    for job in jobs:
        await async_session.refresh(job)
        assert job.status == "completed"

    elapsed = end_time - start_time
    print(f"\n10 concurrent full workflows completed in {elapsed:.2f}s")
    assert elapsed < 60.0, f"10 full workflows took {elapsed:.2f}s (expected < 60s)"


@pytest.mark.asyncio
@pytest.mark.load
async def test_concurrent_full_workflow_25_jobs(async_session):
    """Test 25 concurrent jobs through complete workflow (medium stress)."""
    from src.workers.job_processor import process_job

    num_jobs = 25
    jobs = []

    # Create jobs
    for i in range(num_jobs):
        job = DesignJob(
            job_id=uuid.uuid4(),
            project_id=f"load-25-{i}",
            user_id=f"user-{i % 5}",
            prd_content=f"# PRD {i}\n\nScreens: S1, S2, S3, S4, S5",
            trd_content="# Tech Stack",
            status="pending",
            current_phase=0,
        )
        async_session.add(job)
        jobs.append(job)

    await async_session.commit()

    # Mock workflow
    with patch("src.workers.job_processor.compile_workflow") as mock_compile:
        mock_workflow = AsyncMock()
        mock_workflow.ainvoke = AsyncMock(
            return_value={
                "current_phase": 6,
                "progress_percent": 100.0,
                "awaiting_feedback": False,
            }
        )
        mock_compile.return_value = mock_workflow

        start_time = asyncio.get_event_loop().time()
        await asyncio.gather(*[process_job(str(job.job_id)) for job in jobs])
        end_time = asyncio.get_event_loop().time()

    # Verify completion
    completed_count = 0
    for job in jobs:
        await async_session.refresh(job)
        if job.status == "completed":
            completed_count += 1

    elapsed = end_time - start_time
    print(f"\n25 concurrent jobs: {completed_count}/{num_jobs} completed in {elapsed:.2f}s")
    assert completed_count >= 23, f"Only {completed_count}/25 jobs completed"


@pytest.mark.asyncio
@pytest.mark.load
@pytest.mark.slow
async def test_concurrent_full_workflow_50_jobs(async_session):
    """Test 50 concurrent jobs through complete workflow (high stress)."""
    from src.workers.job_processor import process_job

    num_jobs = 50
    jobs = []

    # Create jobs
    for i in range(num_jobs):
        job = DesignJob(
            job_id=uuid.uuid4(),
            project_id=f"stress-50-{i}",
            user_id=f"user-{i % 10}",
            prd_content=f"# Stress {i}\n\nScreens: A, B, C",
            trd_content="# Tech",
            status="pending",
            current_phase=0,
        )
        async_session.add(job)
        jobs.append(job)

    await async_session.commit()

    # Mock workflow
    with patch("src.workers.job_processor.compile_workflow") as mock_compile:
        mock_workflow = AsyncMock()
        mock_workflow.ainvoke = AsyncMock(
            return_value={
                "current_phase": 6,
                "progress_percent": 100.0,
                "awaiting_feedback": False,
            }
        )
        mock_compile.return_value = mock_workflow

        start_time = asyncio.get_event_loop().time()

        # Process in batches to avoid overwhelming system
        batch_size = 10
        for batch_start in range(0, num_jobs, batch_size):
            batch_jobs = jobs[batch_start : batch_start + batch_size]
            await asyncio.gather(*[process_job(str(job.job_id)) for job in batch_jobs])

        end_time = asyncio.get_event_loop().time()

    # Verify completion
    completed_count = 0
    failed_count = 0
    for job in jobs:
        await async_session.refresh(job)
        if job.status == "completed":
            completed_count += 1
        elif job.status == "failed":
            failed_count += 1

    elapsed = end_time - start_time
    print(f"\n50 concurrent jobs: {completed_count} completed, {failed_count} failed in {elapsed:.2f}s")

    # Allow some failures under extreme load
    assert completed_count >= 45, f"Only {completed_count}/50 jobs completed"


@pytest.mark.asyncio
@pytest.mark.load
async def test_full_workflow_with_pauses(async_session):
    """Test concurrent jobs with some pausing at Phase 3 (awaiting feedback)."""
    from src.workers.job_processor import process_job

    num_jobs = 15
    jobs = []

    for i in range(num_jobs):
        job = DesignJob(
            job_id=uuid.uuid4(),
            project_id=f"pause-test-{i}",
            user_id=f"user-{i % 3}",
            prd_content="# PRD\n\nScreens: Login, Dashboard",
            trd_content="# TRD",
            status="pending",
            current_phase=0,
        )
        async_session.add(job)
        jobs.append(job)

    await async_session.commit()

    # Mock workflow: some pause, some complete
    with patch("src.workers.job_processor.compile_workflow") as mock_compile:

        def mock_invoke(state, config):
            job_id = state["job_id"]
            # Every 3rd job pauses at Phase 3
            if int(job_id.split("-")[-1]) % 3 == 0:
                return {
                    "job_id": job_id,
                    "current_phase": 3,
                    "progress_percent": 50.0,
                    "awaiting_feedback": True,
                }
            else:
                return {
                    "job_id": job_id,
                    "current_phase": 6,
                    "progress_percent": 100.0,
                    "awaiting_feedback": False,
                }

        mock_workflow = AsyncMock()
        mock_workflow.ainvoke = AsyncMock(side_effect=mock_invoke)
        mock_compile.return_value = mock_workflow

        await asyncio.gather(*[process_job(str(job.job_id)) for job in jobs])

    # Verify mixed states
    completed = 0
    awaiting = 0

    for job in jobs:
        await async_session.refresh(job)
        if job.status == "completed":
            completed += 1
        elif job.status == "awaiting_feedback":
            awaiting += 1

    print(f"\n15 jobs: {completed} completed, {awaiting} awaiting feedback")
    assert completed > 0 and awaiting > 0, "Expected mix of completed and paused jobs"


@pytest.mark.asyncio
@pytest.mark.load
async def test_throughput_full_workflow_per_minute(async_session):
    """Test sustained throughput: jobs completed per minute."""
    from src.workers.job_processor import process_job

    # Goal: Process 20 jobs in < 60 seconds
    num_jobs = 20
    jobs = []

    for i in range(num_jobs):
        job = DesignJob(
            job_id=uuid.uuid4(),
            project_id=f"throughput-{i}",
            user_id="throughput-user",
            prd_content="# PRD\n\nScreens: A, B, C",
            trd_content="# TRD",
            status="pending",
            current_phase=0,
        )
        async_session.add(job)
        jobs.append(job)

    await async_session.commit()

    # Mock fast workflow
    with patch("src.workers.job_processor.compile_workflow") as mock_compile:
        mock_workflow = AsyncMock()
        mock_workflow.ainvoke = AsyncMock(
            return_value={
                "current_phase": 6,
                "progress_percent": 100.0,
                "awaiting_feedback": False,
            }
        )
        mock_compile.return_value = mock_workflow

        start_time = asyncio.get_event_loop().time()
        await asyncio.gather(*[process_job(str(job.job_id)) for job in jobs])
        end_time = asyncio.get_event_loop().time()

    elapsed = end_time - start_time
    throughput = num_jobs / (elapsed / 60.0)  # jobs per minute

    print(f"\nThroughput: {throughput:.2f} jobs/minute ({elapsed:.2f}s for {num_jobs} jobs)")

    # Verify reasonable throughput (at least 15 jobs/minute)
    assert throughput >= 15.0, f"Throughput {throughput:.2f} jobs/min is below target (15/min)"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "load", "-s"])
