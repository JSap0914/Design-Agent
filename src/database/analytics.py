"""
Analytics queries for ANYON dashboard integration.

Week 7 Task 2 & 4: Session history tracking and analytics queries

Provides functions to query the ANYON read-only views created in migration 20250113_0002:
- v_job_summary
- v_session_history
- v_design_analytics
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.connection import db_manager
from src.utils.logger import get_logger

logger = get_logger(__name__)


# ============================================================================
# Job Summary Queries
# ============================================================================


async def get_job_summary(job_id: str) -> Optional[Dict[str, Any]]:
    """
    Get comprehensive summary for a single job.

    Args:
        job_id: Design job UUID

    Returns:
        Job summary dictionary or None if not found

    Example:
        {
            "job_id": "...",
            "status": "completed",
            "duration_seconds": 1234,
            "progress_percent": 100.0,
            "quality_metrics": {"quality_score": 95, "document_count": 6},
            ...
        }
    """
    try:
        job_uuid = uuid.UUID(job_id)

        async with db_manager.get_async_session() as session:
            result = await session.execute(
                text("""
                    SELECT
                        job_id::TEXT,
                        project_id,
                        user_id,
                        status,
                        created_at,
                        started_at,
                        completed_at,
                        duration_seconds,
                        current_phase,
                        phase_name,
                        progress_percent,
                        screen_count,
                        completed_screens,
                        estimated_time_remaining,
                        quality_metrics,
                        decision_count,
                        library_count,
                        error_message
                    FROM shared.v_job_summary
                    WHERE job_id = :job_id
                """),
                {"job_id": job_uuid}
            )

            row = result.one_or_none()
            if not row:
                return None

            return dict(row._mapping)

    except Exception as e:
        logger.error(f"Failed to get job summary: {e}", job_id=job_id)
        return None


async def get_recent_jobs(
    user_id: Optional[str] = None,
    limit: int = 50,
    status: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Get recent jobs with optional filtering.

    Args:
        user_id: Filter by user (optional)
        limit: Maximum number of jobs to return
        status: Filter by status (optional)

    Returns:
        List of job summaries
    """
    try:
        query = "SELECT * FROM shared.v_job_summary WHERE 1=1"
        params = {}

        if user_id:
            query += " AND user_id = :user_id"
            params["user_id"] = user_id

        if status:
            query += " AND status = :status"
            params["status"] = status

        query += " ORDER BY created_at DESC LIMIT :limit"
        params["limit"] = limit

        async with db_manager.get_async_session() as session:
            result = await session.execute(text(query), params)
            return [dict(row._mapping) for row in result]

    except Exception as e:
        logger.error(f"Failed to get recent jobs: {e}")
        return []


# ============================================================================
# Session History Queries
# ============================================================================


async def get_session_history(
    user_id: str,
    limit: int = 50,
    include_paused: bool = True
) -> List[Dict[str, Any]]:
    """
    Get user's design session history.

    Args:
        user_id: User ID to query
        limit: Maximum number of sessions
        include_paused: Include paused sessions

    Returns:
        List of session history records

    Example:
        [
            {
                "session_id": "...",
                "job_id": "...",
                "current_phase": 3,
                "session_duration_seconds": 1234,
                "total_screens": 8,
                "decisions_summary": [...],
                ...
            },
            ...
        ]
    """
    try:
        query = """
            SELECT
                session_id::TEXT,
                job_id::TEXT,
                project_id,
                user_id,
                langgraph_thread_id,
                current_phase,
                is_paused,
                pause_reason,
                session_started,
                session_updated,
                job_status,
                job_completed,
                session_duration_seconds,
                total_screens,
                completed_screens,
                decisions_summary,
                selected_libraries
            FROM shared.v_session_history
            WHERE user_id = :user_id
        """

        if not include_paused:
            query += " AND is_paused = false"

        query += " ORDER BY session_started DESC LIMIT :limit"

        async with db_manager.get_async_session() as session:
            result = await session.execute(
                text(query),
                {"user_id": user_id, "limit": limit}
            )
            return [dict(row._mapping) for row in result]

    except Exception as e:
        logger.error(f"Failed to get session history: {e}", user_id=user_id)
        return []


async def get_job_statistics(job_id: str) -> Optional[Dict[str, Any]]:
    """
    Get detailed statistics for a specific job.

    Args:
        job_id: Design job UUID

    Returns:
        Statistics dictionary with decision breakdown, library usage, phase timings
    """
    try:
        job_uuid = uuid.UUID(job_id)

        async with db_manager.get_async_session() as session:
            # Get from session history view (includes decision and library summaries)
            result = await session.execute(
                text("""
                    SELECT
                        job_id::TEXT,
                        session_duration_seconds,
                        total_screens,
                        completed_screens,
                        decisions_summary,
                        selected_libraries
                    FROM shared.v_session_history
                    WHERE job_id = :job_id
                """),
                {"job_id": job_uuid}
            )

            row = result.one_or_none()
            if not row:
                return None

            stats = dict(row._mapping)

            # Add phase-by-phase timing (if available from progress updates)
            # This requires querying design_progress history if we track it
            # For now, return the basic stats
            return stats

    except Exception as e:
        logger.error(f"Failed to get job statistics: {e}", job_id=job_id)
        return None


# ============================================================================
# Dashboard Analytics Queries
# ============================================================================


async def get_dashboard_analytics() -> Dict[str, Any]:
    """
    Get aggregated analytics for ANYON dashboard.

    Returns:
        Analytics dictionary with:
        - popular_libraries: Top 20 most used libraries
        - avg_phase_durations: Average time per phase
        - job_statistics: Success/failure rates
        - screen_distribution: Screen count distribution
        - quality_trends: Quality scores over last 30 days
        - common_decisions: Most common decision types
        - screen_statistics: Min/max/avg screens per job
        - recent_activity: Last 24 hours activity

    Example:
        {
            "popular_libraries": [
                {"library_name": "TanStack Table", "selection_count": 45, ...},
                ...
            ],
            "job_statistics": {
                "total_jobs": 150,
                "completed": 140,
                "success_rate": 93.33
            },
            ...
        }
    """
    try:
        async with db_manager.get_async_session() as session:
            result = await session.execute(
                text("SELECT * FROM shared.v_design_analytics")
            )

            row = result.one_or_none()
            if not row:
                return {}

            analytics = dict(row._mapping)

            logger.info("Dashboard analytics retrieved")
            return analytics

    except Exception as e:
        logger.error(f"Failed to get dashboard analytics: {e}")
        return {}


async def get_popular_libraries(
    category: Optional[str] = None,
    limit: int = 20
) -> List[Dict[str, Any]]:
    """
    Get most popular open-source libraries.

    Args:
        category: Filter by category (optional)
        limit: Maximum number of libraries

    Returns:
        List of popular libraries with usage statistics
    """
    try:
        query = """
            SELECT
                library_name,
                category,
                COUNT(*) AS selection_count,
                AVG(stars) AS avg_stars,
                AVG(ranking_score) AS avg_ranking_score,
                ARRAY_AGG(DISTINCT version ORDER BY version DESC) AS versions_used
            FROM shared.open_source_selections
        """

        params = {"limit": limit}

        if category:
            query += " WHERE category = :category"
            params["category"] = category

        query += """
            GROUP BY library_name, category
            ORDER BY COUNT(*) DESC, AVG(stars) DESC
            LIMIT :limit
        """

        async with db_manager.get_async_session() as session:
            result = await session.execute(text(query), params)
            return [dict(row._mapping) for row in result]

    except Exception as e:
        logger.error(f"Failed to get popular libraries: {e}")
        return []


async def get_success_rate_trends(days: int = 30) -> List[Dict[str, Any]]:
    """
    Get success rate trends over time.

    Args:
        days: Number of days to analyze

    Returns:
        List of daily success rates

    Example:
        [
            {"date": "2025-01-13", "total_jobs": 10, "completed": 9, "success_rate": 90.0},
            ...
        ]
    """
    try:
        async with db_manager.get_async_session() as session:
            result = await session.execute(
                text("""
                    SELECT
                        DATE(created_at) AS date,
                        COUNT(*) AS total_jobs,
                        COUNT(*) FILTER (WHERE status = 'completed') AS completed,
                        ROUND(
                            (COUNT(*) FILTER (WHERE status = 'completed')::NUMERIC /
                             NULLIF(COUNT(*)::NUMERIC, 0)) * 100,
                            2
                        ) AS success_rate
                    FROM shared.design_jobs
                    WHERE created_at >= NOW() - INTERVAL ':days days'
                    GROUP BY DATE(created_at)
                    ORDER BY DATE(created_at) DESC
                """),
                {"days": days}
            )

            return [dict(row._mapping) for row in result]

    except Exception as e:
        logger.error(f"Failed to get success rate trends: {e}")
        return []


async def get_avg_completion_time_by_screen_count() -> List[Dict[str, Any]]:
    """
    Get average completion time grouped by screen count.

    Returns:
        List of screen count vs. completion time

    Example:
        [
            {"screen_count": 5, "avg_duration_minutes": 25.5, "job_count": 20},
            {"screen_count": 8, "avg_duration_minutes": 35.2, "job_count": 15},
            ...
        ]
    """
    try:
        async with db_manager.get_async_session() as session:
            result = await session.execute(
                text("""
                    SELECT
                        p.screen_count,
                        COUNT(*) AS job_count,
                        ROUND(
                            AVG(EXTRACT(EPOCH FROM (j.completed_at - j.started_at)) / 60),
                            1
                        ) AS avg_duration_minutes
                    FROM shared.design_jobs j
                    INNER JOIN shared.design_progress p ON j.job_id = p.job_id
                    WHERE j.status = 'completed'
                        AND j.started_at IS NOT NULL
                        AND j.completed_at IS NOT NULL
                    GROUP BY p.screen_count
                    ORDER BY p.screen_count
                """)
            )

            return [dict(row._mapping) for row in result]

    except Exception as e:
        logger.error(f"Failed to get completion time by screen count: {e}")
        return []


# ============================================================================
# Quality Analytics
# ============================================================================


async def get_quality_score_distribution() -> Dict[str, Any]:
    """
    Get distribution of quality scores.

    Returns:
        Quality score statistics

    Example:
        {
            "avg_score": 92.5,
            "min_score": 75,
            "max_score": 100,
            "median_score": 93,
            "score_buckets": {
                "90-100": 45,
                "80-89": 20,
                "70-79": 5,
                ...
            }
        }
    """
    try:
        async with db_manager.get_async_session() as session:
            result = await session.execute(
                text("""
                    WITH scores AS (
                        SELECT (metadata->>'quality_score')::INTEGER AS quality_score
                        FROM shared.design_outputs
                        WHERE document_type = 'validation_report'
                            AND metadata->>'quality_score' IS NOT NULL
                    )
                    SELECT
                        AVG(quality_score) AS avg_score,
                        MIN(quality_score) AS min_score,
                        MAX(quality_score) AS max_score,
                        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY quality_score) AS median_score,
                        COUNT(*) AS total_jobs
                    FROM scores
                """)
            )

            row = result.one_or_none()
            if not row:
                return {}

            stats = dict(row._mapping)

            # Get score distribution buckets
            bucket_result = await session.execute(
                text("""
                    SELECT
                        CASE
                            WHEN quality_score >= 90 THEN '90-100'
                            WHEN quality_score >= 80 THEN '80-89'
                            WHEN quality_score >= 70 THEN '70-79'
                            WHEN quality_score >= 60 THEN '60-69'
                            ELSE '<60'
                        END AS score_bucket,
                        COUNT(*) AS job_count
                    FROM (
                        SELECT (metadata->>'quality_score')::INTEGER AS quality_score
                        FROM shared.design_outputs
                        WHERE document_type = 'validation_report'
                            AND metadata->>'quality_score' IS NOT NULL
                    ) scores
                    GROUP BY score_bucket
                    ORDER BY score_bucket DESC
                """)
            )

            stats["score_buckets"] = {
                row.score_bucket: row.job_count
                for row in bucket_result
            }

            return stats

    except Exception as e:
        logger.error(f"Failed to get quality score distribution: {e}")
        return {}


__all__ = [
    "get_job_summary",
    "get_recent_jobs",
    "get_session_history",
    "get_job_statistics",
    "get_dashboard_analytics",
    "get_popular_libraries",
    "get_success_rate_trends",
    "get_avg_completion_time_by_screen_count",
    "get_quality_score_distribution",
]
