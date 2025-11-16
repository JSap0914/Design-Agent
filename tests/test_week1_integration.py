"""
Week 1 Integration Test: End-to-end database trigger flow.

Tests the complete flow:
1. ANYON inserts job → shared.design_jobs
2. PostgreSQL trigger fires NOTIFY
3. Job listener receives notification
4. Job processor executes
5. Job completes and updates database
"""

import asyncio
import uuid
from datetime import datetime

import pytest
from sqlalchemy import select

from src.database.connection import db_manager
from src.database.models import DesignJob, DesignProgress
from src.workers.job_listener import job_listener
from src.workers.job_processor import process_job


@pytest.fixture
async def setup_database():
    """Setup database connection for tests."""
    db_manager.initialize_async_engine()
    yield
    await db_manager.close()


@pytest.mark.asyncio
async def test_job_creation_and_processing(setup_database):
    """
    Test complete job flow from insertion to completion.

    This test verifies:
    1. Job can be inserted into database
    2. Job processor can pick up and process job
    3. Job status updates correctly
    4. Progress tracking works
    """
    # Create test job
    test_job_id = uuid.uuid4()
    test_prd = """
    # Product Requirements Document

    ## Overview
    Build a simple task management application.

    ## Screens
    1. Login Screen
    2. Task List Screen
    3. Task Detail Screen
    """
    test_trd = """
    # Technical Requirements Document

    ## Technology Stack
    - Frontend: React 19
    - Backend: FastAPI
    - Database: PostgreSQL
    """

    # Insert test job directly (simulating ANYON insertion)
    async with db_manager.get_async_session() as session:
        job = DesignJob(
            job_id=test_job_id,
            project_id="test-project-001",
            user_id="test-user-001",
            prd_content=test_prd,
            trd_content=test_trd,
            status="pending",
        )
        session.add(job)
        await session.commit()

    print(f"✓ Test job created: {test_job_id}")

    # Process job directly (simulating job listener triggering processor)
    await process_job(str(test_job_id))

    print("✓ Job processor executed")

    # Verify job status updated
    async with db_manager.get_async_session() as session:
        result = await session.execute(
            select(DesignJob).where(DesignJob.job_id == test_job_id)
        )
        completed_job = result.scalar_one_or_none()

        assert completed_job is not None, "Job not found in database"
        assert completed_job.status == "completed", f"Expected 'completed', got '{completed_job.status}'"
        assert completed_job.started_at is not None, "started_at should be set"
        assert completed_job.completed_at is not None, "completed_at should be set"

    print(f"✓ Job status verified: {completed_job.status}")

    # Verify progress record created
    async with db_manager.get_async_session() as session:
        result = await session.execute(
            select(DesignProgress).where(DesignProgress.job_id == test_job_id)
        )
        progress = result.scalar_one_or_none()

        assert progress is not None, "Progress record not found"
        assert progress.progress_percent == 100.0, f"Expected 100.0, got {progress.progress_percent}"
        assert progress.current_phase == 6, f"Expected phase 6, got {progress.current_phase}"

    print(f"✓ Progress tracking verified: {progress.progress_percent}% complete")

    # Cleanup
    async with db_manager.get_async_session() as session:
        # Delete progress first (foreign key constraint)
        await session.delete(progress)
        await session.delete(completed_job)
        await session.commit()

    print("✓ Test cleanup complete")
    print("\n✅ Week 1 Integration Test PASSED: Job creation → processing → completion")


@pytest.mark.asyncio
async def test_job_listener_connection(setup_database):
    """
    Test that job listener can connect to PostgreSQL.

    This test verifies:
    1. Listener can establish connection
    2. LISTEN command executes successfully
    3. Listener can disconnect gracefully
    """
    try:
        # Connect listener
        await job_listener.connect()
        print("✓ Job listener connected to PostgreSQL")

        # Verify connection is active
        assert job_listener.connection is not None, "Connection should not be None"
        assert not job_listener.connection.is_closed(), "Connection should be open"

        print("✓ LISTEN/NOTIFY channel active: new_design_job")

        # Disconnect
        await job_listener.disconnect()
        print("✓ Job listener disconnected gracefully")

        print("\n✅ Job Listener Connection Test PASSED")

    except Exception as e:
        pytest.fail(f"Job listener connection failed: {e}")


@pytest.mark.asyncio
async def test_notify_trigger_exists(setup_database):
    """
    Test that PostgreSQL NOTIFY trigger exists and is configured correctly.

    This test verifies:
    1. Trigger function exists
    2. Trigger is attached to design_jobs table
    """
    async with db_manager.get_async_session() as session:
        # Check if trigger function exists
        result = await session.execute("""
            SELECT EXISTS (
                SELECT 1
                FROM pg_proc p
                JOIN pg_namespace n ON p.pronamespace = n.oid
                WHERE n.nspname = 'shared'
                AND p.proname = 'notify_new_job_func'
            );
        """)
        function_exists = result.scalar()
        assert function_exists, "Trigger function 'notify_new_job_func' not found"
        print("✓ Trigger function 'notify_new_job_func' exists")

        # Check if trigger exists on table
        result = await session.execute("""
            SELECT EXISTS (
                SELECT 1
                FROM pg_trigger t
                JOIN pg_class c ON t.tgrelid = c.oid
                JOIN pg_namespace n ON c.relnamespace = n.oid
                WHERE n.nspname = 'shared'
                AND c.relname = 'design_jobs'
                AND t.tgname = 'notify_new_job'
            );
        """)
        trigger_exists = result.scalar()
        assert trigger_exists, "Trigger 'notify_new_job' not found on 'design_jobs' table"
        print("✓ Trigger 'notify_new_job' attached to 'design_jobs' table")

    print("\n✅ NOTIFY Trigger Configuration Test PASSED")


@pytest.mark.asyncio
async def test_listen_notify_end_to_end(setup_database):
    """
    Test complete LISTEN/NOTIFY flow.

    This test verifies:
    1. Listener starts and connects
    2. Job insertion triggers PostgreSQL NOTIFY
    3. Listener receives notification
    4. Job processor runs automatically
    5. Job completes successfully
    """
    import uuid

    # Track if job was processed
    processed_jobs = []

    # Patch process_job to track calls
    original_process_job = process_job

    async def tracked_process_job(job_id: str):
        processed_jobs.append(job_id)
        await original_process_job(job_id)

    # Monkey patch
    import src.workers.job_listener as listener_module
    listener_module.process_job = tracked_process_job

    try:
        # Start listener in background
        listener_task = asyncio.create_task(job_listener.run())

        # Wait for listener to connect
        await asyncio.sleep(2)

        print("✓ Job listener started")

        # Create test job (this should trigger NOTIFY)
        test_job_id = uuid.uuid4()
        async with db_manager.get_async_session() as session:
            job = DesignJob(
                job_id=test_job_id,
                project_id="test-listen-notify-001",
                user_id="test-user-001",
                prd_content="# Test PRD",
                trd_content="# Test TRD",
                status="pending",
            )
            session.add(job)
            await session.commit()

        print(f"✓ Test job inserted: {test_job_id}")

        # Wait for notification and processing (max 10 seconds)
        for i in range(20):  # 20 * 0.5 = 10 seconds max
            await asyncio.sleep(0.5)
            if str(test_job_id) in processed_jobs:
                break

        # Verify job was processed via LISTEN/NOTIFY
        assert str(test_job_id) in processed_jobs, "Job was not processed via LISTEN/NOTIFY"
        print("✓ Job processed via LISTEN/NOTIFY trigger")

        # Verify job completed
        async with db_manager.get_async_session() as session:
            result = await session.execute(
                select(DesignJob).where(DesignJob.job_id == test_job_id)
            )
            completed_job = result.scalar_one_or_none()

            assert completed_job is not None, "Job not found"
            assert completed_job.status == "completed", f"Expected 'completed', got '{completed_job.status}'"

        print(f"✓ Job status: {completed_job.status}")

        # Cleanup test job
        async with db_manager.get_async_session() as session:
            # Delete progress first
            await session.execute(
                select(DesignProgress).where(DesignProgress.job_id == test_job_id)
            ).scalar_one_or_none()

            result = await session.execute(
                select(DesignProgress).where(DesignProgress.job_id == test_job_id)
            )
            progress = result.scalar_one_or_none()
            if progress:
                await session.delete(progress)

            await session.delete(completed_job)
            await session.commit()

        print("✓ Test cleanup complete")
        print("\n✅ LISTEN/NOTIFY End-to-End Test PASSED")

    finally:
        # Stop listener
        job_listener.stop()
        await asyncio.sleep(1)
        listener_task.cancel()
        try:
            await listener_task
        except asyncio.CancelledError:
            pass

        # Restore original function
        listener_module.process_job = original_process_job


# Manual test script (can be run standalone)
async def run_manual_test():
    """
    Manual test that can be run without pytest.

    Usage:
        python -m tests.test_week1_integration
    """
    from src.utils.logger import configure_logging

    # Configure logging
    configure_logging()

    print("=" * 70)
    print("Week 1 Integration Test - Manual Execution")
    print("=" * 70)

    # Initialize database
    db_manager.initialize_async_engine()

    try:
        print("\n[1/4] Testing NOTIFY trigger configuration...")
        await test_notify_trigger_exists(None)

        print("\n[2/4] Testing job listener connection...")
        await test_job_listener_connection(None)

        print("\n[3/4] Testing job processing (direct call)...")
        await test_job_creation_and_processing(None)

        print("\n[4/4] Testing LISTEN/NOTIFY end-to-end flow...")
        await test_listen_notify_end_to_end(None)

        print("\n" + "=" * 70)
        print("✅ ALL WEEK 1 TESTS PASSED")
        print("=" * 70)
        print("\nWeek 1 Deliverable Verified:")
        print("  • Database schema live ✓")
        print("  • Job listener working ✓")
        print("  • End-to-end trigger flow operational ✓")
        print("  • LISTEN/NOTIFY integration tested ✓")

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        raise
    finally:
        await db_manager.close()


if __name__ == "__main__":
    asyncio.run(run_manual_test())
