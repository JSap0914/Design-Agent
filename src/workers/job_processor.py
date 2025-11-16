"""
Job processor for Design Agent.

This module processes design jobs by executing the LangGraph workflow.
Currently a shell implementation that will be expanded in Week 2.
"""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.database.connection import db_manager
from src.database.models import DesignJob, DesignProgress
from src.utils.logger import get_logger

logger = get_logger(__name__)


async def process_job(job_id: str) -> None:
    """
    Process a design job.

    This is a shell implementation for Week 1 testing.
    Will be expanded in Week 2+ to actually run the LangGraph workflow.

    Args:
        job_id: Job ID to process
    """
    job_uuid = uuid.UUID(job_id)

    try:
        logger.info("Starting job processing", job_id=job_id)

        async with db_manager.get_async_session() as session:
            # Fetch job
            job = await _get_job(session, job_uuid)
            if job is None:
                logger.error("Job not found", job_id=job_id)
                return

            # Update job status to running
            await _update_job_status(session, job_uuid, "running")
            logger.info("Job status updated to running", job_id=job_id)

            # Create progress record
            await _create_progress_record(session, job_uuid)
            logger.info("Progress record created", job_id=job_id)

            # ================================================================
            # LangGraph Workflow Execution (Week 2: Phases 1-2)
            # ================================================================
            logger.info(
                "Executing LangGraph workflow",
                job_id=job_id,
                project_id=job.project_id,
                user_id=job.user_id,
            )

            # Import workflow
            from src.langgraph.workflow import compile_workflow

            # Initialize workflow
            workflow = compile_workflow()

            # Prepare initial state
            initial_state = {
                "job_id": str(job_uuid),
                "project_id": job.project_id,
                "user_id": job.user_id,
                "prd_content": job.prd_content,
                "trd_content": job.trd_content,
                "current_phase": 0,
                "phase_name": "Initializing",
                "progress_percent": 0.0,
                "errors": [],
                "retry_count": 0,
            }

            # Execute workflow with thread_id for checkpointing
            config = {"configurable": {"thread_id": str(job_uuid)}}

            try:
                # Run workflow (async)
                final_state = await workflow.ainvoke(initial_state, config)

                # Log results
                logger.info(
                    "Workflow execution completed",
                    job_id=job_id,
                    phase=final_state.get("current_phase"),
                    screen_count=final_state.get("screen_count", 0),
                    options_count=final_state.get("options_provided_count", 0),
                )

                # Update progress from workflow state
                await _update_progress(
                    session,
                    job_uuid,
                    phase=final_state.get("current_phase", 2),
                    progress=final_state.get("progress_percent", 35.0),
                    phase_name=final_state.get("phase_name", "Phases 1-2 Complete"),
                )

                # Check if workflow is awaiting user feedback (Phase 3)
                if final_state.get("awaiting_feedback"):
                    # Don't mark as completed - waiting for user input via WebSocket
                    await _update_job_status(session, job_uuid, "awaiting_feedback")
                    logger.info(
                        "Job paused, awaiting user feedback",
                        job_id=job_id,
                        screen_name=final_state.get("current_screen_name"),
                    )
                    # Workflow will resume when WebSocket receives feedback
                    return

            except Exception as workflow_error:
                logger.error("Workflow execution failed", error=str(workflow_error), job_id=job_id)
                raise

            # ================================================================
            # END LangGraph Workflow
            # ================================================================

            # Update job status to completed
            await _update_job_status(session, job_uuid, "completed")
            logger.info("Job completed successfully", job_id=job_id)

    except Exception as e:
        logger.error("Error processing job", job_id=job_id, error=str(e))

        # Update job status to failed
        try:
            async with db_manager.get_async_session() as session:
                await _update_job_status(
                    session, job_uuid, "failed", error_message=str(e)
                )
        except Exception as update_error:
            logger.error(
                "Failed to update job status to failed",
                job_id=job_id,
                error=str(update_error),
            )


async def _get_job(session: AsyncSession, job_id: uuid.UUID) -> DesignJob | None:
    """
    Fetch job from database.

    Args:
        session: Database session
        job_id: Job ID

    Returns:
        DesignJob or None if not found
    """
    result = await session.execute(select(DesignJob).where(DesignJob.job_id == job_id))
    return result.scalar_one_or_none()


async def _update_job_status(
    session: AsyncSession,
    job_id: uuid.UUID,
    status: str,
    error_message: str | None = None,
) -> None:
    """
    Update job status in database.

    Args:
        session: Database session
        job_id: Job ID
        status: New status (pending, running, completed, failed)
        error_message: Optional error message for failed jobs
    """
    values: dict[str, Any] = {"status": status}

    if status == "running":
        values["started_at"] = datetime.utcnow()
    elif status in ("completed", "failed"):
        values["completed_at"] = datetime.utcnow()

    if error_message:
        values["error_message"] = error_message

    await session.execute(update(DesignJob).where(DesignJob.job_id == job_id).values(**values))
    await session.commit()


async def _create_progress_record(session: AsyncSession, job_id: uuid.UUID) -> None:
    """
    Create initial progress record.

    Args:
        session: Database session
        job_id: Job ID
    """
    progress = DesignProgress(
        job_id=job_id,
        current_phase=1,
        phase_name="Initializing",
        progress_percent=0.0,
        screen_count=0,
        completed_screens=0,
        estimated_time_remaining=None,
    )
    session.add(progress)
    await session.commit()


async def _update_progress(
    session: AsyncSession,
    job_id: uuid.UUID,
    phase: int,
    progress: float,
    phase_name: str | None = None,
) -> None:
    """
    Update job progress.

    Args:
        session: Database session
        job_id: Job ID
        phase: Current phase (1-6)
        progress: Progress percentage (0-100)
        phase_name: Optional phase name
    """
    values: dict[str, Any] = {
        "current_phase": phase,
        "progress_percent": progress,
        "last_updated": datetime.utcnow(),
    }

    if phase_name:
        values["phase_name"] = phase_name

    await session.execute(
        update(DesignProgress).where(DesignProgress.job_id == job_id).values(**values)
    )
    await session.commit()


# Export for easy import
__all__ = ["process_job"]
