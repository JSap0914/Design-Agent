"""Create ANYON read-only views for dashboard integration

Revision ID: 20250113_0002
Revises: 20250113_0001
Create Date: 2025-01-13

Week 7 Task 1: Database views for ANYON read access

Creates 3 read-only views in shared schema:
1. v_job_summary - Job status, duration, quality scores for dashboard
2. v_session_history - User session history for tracking
3. v_design_analytics - Aggregated analytics (popular libraries, trends)
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20250113_0002'
down_revision = '20250113_0001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create ANYON read-only views."""

    # ========================================================================
    # View 1: Job Summary
    # ========================================================================
    op.execute("""
        CREATE OR REPLACE VIEW shared.v_job_summary AS
        SELECT
            j.job_id,
            j.project_id,
            j.user_id,
            j.status,
            j.created_at,
            j.started_at,
            j.completed_at,
            -- Duration calculations
            CASE
                WHEN j.completed_at IS NOT NULL
                THEN EXTRACT(EPOCH FROM (j.completed_at - j.started_at))::INTEGER
                WHEN j.started_at IS NOT NULL
                THEN EXTRACT(EPOCH FROM (NOW() - j.started_at))::INTEGER
                ELSE NULL
            END AS duration_seconds,
            -- Progress information
            p.current_phase,
            p.phase_name,
            p.progress_percent,
            p.screen_count,
            p.completed_screens,
            p.estimated_time_remaining,
            p.last_updated AS progress_last_updated,
            -- Quality metrics
            (
                SELECT jsonb_build_object(
                    'quality_score',
                    COALESCE(
                        (SELECT metadata->>'quality_score'
                         FROM shared.design_outputs
                         WHERE job_id = j.job_id AND document_type = 'validation_report'
                         LIMIT 1),
                        '0'
                    )::INTEGER,
                    'document_count',
                    COUNT(DISTINCT o.document_type)
                )
                FROM shared.design_outputs o
                WHERE o.job_id = j.job_id
            ) AS quality_metrics,
            -- Decision count
            (SELECT COUNT(*) FROM shared.design_decisions WHERE job_id = j.job_id) AS decision_count,
            -- Open source library count
            (SELECT COUNT(*) FROM shared.open_source_selections WHERE job_id = j.job_id) AS library_count,
            -- Error message if failed
            j.error_message
        FROM
            shared.design_jobs j
        LEFT JOIN
            shared.design_progress p ON j.job_id = p.job_id
        ORDER BY
            j.created_at DESC;
    """)

    # ========================================================================
    # View 2: Session History
    # ========================================================================
    op.execute("""
        CREATE OR REPLACE VIEW shared.v_session_history AS
        SELECT
            s.session_id,
            s.job_id,
            j.project_id,
            j.user_id,
            s.langgraph_thread_id,
            s.current_phase,
            s.is_paused,
            s.pause_reason,
            s.created_at AS session_started,
            s.updated_at AS session_updated,
            -- Job status
            j.status AS job_status,
            j.completed_at AS job_completed,
            -- Session duration
            CASE
                WHEN j.completed_at IS NOT NULL
                THEN EXTRACT(EPOCH FROM (j.completed_at - s.created_at))::INTEGER
                ELSE EXTRACT(EPOCH FROM (NOW() - s.created_at))::INTEGER
            END AS session_duration_seconds,
            -- Screen information
            (SELECT screen_count FROM shared.design_progress WHERE job_id = s.job_id) AS total_screens,
            (SELECT completed_screens FROM shared.design_progress WHERE job_id = s.job_id) AS completed_screens,
            -- Decision summary
            (
                SELECT jsonb_agg(decision_data ORDER BY decision_data->>'timestamp')
                FROM (
                    SELECT jsonb_build_object(
                        'screen_name', d.screen_name,
                        'decision_type', d.decision_type,
                        'timestamp', d.timestamp
                    ) AS decision_data
                    FROM shared.design_decisions d
                    WHERE d.job_id = s.job_id
                ) decisions
            ) AS decisions_summary,
            -- Library selections
            (
                SELECT jsonb_agg(library_data ORDER BY library_data->>'timestamp')
                FROM (
                    SELECT jsonb_build_object(
                        'library_name', os.library_name,
                        'category', os.category,
                        'stars', os.stars,
                        'timestamp', os.timestamp
                    ) AS library_data
                    FROM shared.open_source_selections os
                    WHERE os.job_id = s.job_id
                ) libraries
            ) AS selected_libraries
        FROM
            design_agent.sessions s
        INNER JOIN
            shared.design_jobs j ON s.job_id = j.job_id
        ORDER BY
            s.created_at DESC;
    """)

    # ========================================================================
    # View 3: Design Analytics
    # ========================================================================
    op.execute("""
        CREATE OR REPLACE VIEW shared.v_design_analytics AS
        SELECT
            -- Most popular open-source libraries (Top 20)
            (
                SELECT jsonb_agg(row_to_json(t))
                FROM (
                    SELECT
                        library_name,
                        category,
                        COUNT(*) AS selection_count,
                        AVG(stars) AS avg_stars,
                        AVG(ranking_score) AS avg_ranking_score
                    FROM shared.open_source_selections
                    GROUP BY library_name, category
                    ORDER BY COUNT(*) DESC, AVG(stars) DESC
                    LIMIT 20
                ) t
            ) AS popular_libraries,

            -- Average completion time per phase (in seconds)
            (
                SELECT jsonb_object_agg(
                    'phase_' || phase_data.phase_num::TEXT,
                    phase_data.avg_duration
                )
                FROM (
                    SELECT
                        current_phase AS phase_num,
                        AVG(
                            EXTRACT(EPOCH FROM (completed_at - started_at))::INTEGER
                        ) AS avg_duration
                    FROM shared.design_jobs j
                    INNER JOIN shared.design_progress p ON j.job_id = p.job_id
                    WHERE j.status = 'completed'
                    GROUP BY current_phase
                ) phase_data
            ) AS avg_phase_durations,

            -- Success/failure rates
            (
                SELECT jsonb_build_object(
                    'total_jobs', COUNT(*),
                    'completed', COUNT(*) FILTER (WHERE status = 'completed'),
                    'failed', COUNT(*) FILTER (WHERE status = 'failed'),
                    'pending', COUNT(*) FILTER (WHERE status = 'pending'),
                    'running', COUNT(*) FILTER (WHERE status = 'running'),
                    'paused', COUNT(*) FILTER (WHERE status = 'paused_waiting_for_upload'),
                    'success_rate',
                    ROUND(
                        (COUNT(*) FILTER (WHERE status = 'completed')::NUMERIC /
                         NULLIF(COUNT(*)::NUMERIC, 0)) * 100,
                        2
                    )
                )
                FROM shared.design_jobs
            ) AS job_statistics,

            -- Screen count distribution
            (
                SELECT jsonb_object_agg(
                    screen_count::TEXT,
                    job_count
                )
                FROM (
                    SELECT
                        screen_count,
                        COUNT(*) AS job_count
                    FROM shared.design_progress
                    GROUP BY screen_count
                    ORDER BY screen_count
                ) screen_dist
            ) AS screen_distribution,

            -- Quality score trends (last 30 days)
            (
                SELECT jsonb_agg(row_to_json(t))
                FROM (
                    SELECT
                        DATE(j.completed_at) AS date,
                        COUNT(*) AS jobs_completed,
                        AVG(
                            (o.metadata->>'quality_score')::INTEGER
                        ) AS avg_quality_score
                    FROM shared.design_jobs j
                    INNER JOIN shared.design_outputs o
                        ON j.job_id = o.job_id AND o.document_type = 'validation_report'
                    WHERE j.completed_at >= NOW() - INTERVAL '30 days'
                        AND j.status = 'completed'
                    GROUP BY DATE(j.completed_at)
                    ORDER BY DATE(j.completed_at) DESC
                    LIMIT 30
                ) t
            ) AS quality_trends,

            -- Most common decision types
            (
                SELECT jsonb_agg(row_to_json(t))
                FROM (
                    SELECT
                        decision_type,
                        COUNT(*) AS decision_count
                    FROM shared.design_decisions
                    GROUP BY decision_type
                    ORDER BY COUNT(*) DESC
                    LIMIT 10
                ) t
            ) AS common_decisions,

            -- Average screens per job
            (
                SELECT jsonb_build_object(
                    'avg_screens', AVG(screen_count),
                    'min_screens', MIN(screen_count),
                    'max_screens', MAX(screen_count),
                    'median_screens', PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY screen_count)
                )
                FROM shared.design_progress
            ) AS screen_statistics,

            -- Recent activity (last 24 hours)
            (
                SELECT jsonb_build_object(
                    'jobs_created', COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '24 hours'),
                    'jobs_completed', COUNT(*) FILTER (WHERE completed_at >= NOW() - INTERVAL '24 hours'),
                    'active_sessions', COUNT(*) FILTER (WHERE status = 'running')
                )
                FROM shared.design_jobs
            ) AS recent_activity
        ;
    """)

    # ========================================================================
    # Grant read access to ANYON role (if it exists)
    # ========================================================================
    # Note: This assumes an 'anyon_readonly' role exists for ANYON dashboard access
    # If the role doesn't exist, this will be a no-op
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anyon_readonly') THEN
                GRANT SELECT ON shared.v_job_summary TO anyon_readonly;
                GRANT SELECT ON shared.v_session_history TO anyon_readonly;
                GRANT SELECT ON shared.v_design_analytics TO anyon_readonly;
            END IF;
        END $$;
    """)

    print("Created 3 ANYON read-only views:")
    print("   - shared.v_job_summary")
    print("   - shared.v_session_history")
    print("   - shared.v_design_analytics")


def downgrade() -> None:
    """Drop ANYON read-only views."""
    op.execute("DROP VIEW IF EXISTS shared.v_design_analytics;")
    op.execute("DROP VIEW IF EXISTS shared.v_session_history;")
    op.execute("DROP VIEW IF EXISTS shared.v_job_summary;")

    print("Dropped ANYON read-only views")
