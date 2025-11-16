"""Initial database schema with all tables and PostgreSQL NOTIFY trigger

Revision ID: 20250113_0001
Revises:
Create Date: 2025-01-13 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20250113_0001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create schemas
    op.execute("CREATE SCHEMA IF NOT EXISTS shared")
    op.execute("CREATE SCHEMA IF NOT EXISTS design_agent")

    # ========================================================================
    # SHARED SCHEMA TABLES
    # ========================================================================

    # Create design_jobs table
    op.create_table(
        'design_jobs',
        sa.Column('job_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', sa.String(length=100), nullable=False),
        sa.Column('user_id', sa.String(length=100), nullable=False),
        sa.Column('prd_content', sa.Text(), nullable=False),
        sa.Column('trd_content', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('job_id'),
        schema='shared'
    )
    op.create_index('idx_design_jobs_status', 'design_jobs', ['status'], schema='shared')
    op.create_index('idx_design_jobs_created_at', 'design_jobs', ['created_at'], schema='shared')
    op.create_index('idx_design_jobs_project_id', 'design_jobs', ['project_id'], schema='shared')

    # Create design_progress table
    op.create_table(
        'design_progress',
        sa.Column('progress_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('current_phase', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('phase_name', sa.String(length=100), nullable=False),
        sa.Column('progress_percent', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('screen_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('completed_screens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('estimated_time_remaining', sa.Integer(), nullable=True),
        sa.Column('last_updated', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['job_id'], ['shared.design_jobs.job_id'], ),
        sa.PrimaryKeyConstraint('progress_id'),
        sa.UniqueConstraint('job_id'),
        schema='shared'
    )
    op.create_index('idx_design_progress_job_id', 'design_progress', ['job_id'], schema='shared')
    op.create_index('idx_design_progress_last_updated', 'design_progress', ['last_updated'], schema='shared')

    # Create design_outputs table
    op.create_table(
        'design_outputs',
        sa.Column('output_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('document_type', sa.String(length=100), nullable=False),
        sa.Column('file_name', sa.String(length=255), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('version', sa.String(length=20), nullable=False, server_default='0.9'),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['job_id'], ['shared.design_jobs.job_id'], ),
        sa.PrimaryKeyConstraint('output_id'),
        sa.UniqueConstraint('job_id', 'document_type', 'version', name='uq_job_doc_version'),
        schema='shared'
    )
    op.create_index('idx_design_outputs_job_id', 'design_outputs', ['job_id'], schema='shared')
    op.create_index('idx_design_outputs_document_type', 'design_outputs', ['document_type'], schema='shared')
    op.create_index('idx_design_outputs_created_at', 'design_outputs', ['created_at'], schema='shared')

    # Create design_decisions table
    op.create_table(
        'design_decisions',
        sa.Column('decision_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('screen_name', sa.String(length=200), nullable=False),
        sa.Column('decision_type', sa.String(length=100), nullable=False),
        sa.Column('rationale', sa.Text(), nullable=False),
        sa.Column('alternatives', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('user_feedback', sa.Text(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['job_id'], ['shared.design_jobs.job_id'], ),
        sa.PrimaryKeyConstraint('decision_id'),
        schema='shared'
    )
    op.create_index('idx_design_decisions_job_id', 'design_decisions', ['job_id'], schema='shared')
    op.create_index('idx_design_decisions_screen_name', 'design_decisions', ['screen_name'], schema='shared')
    op.create_index('idx_design_decisions_timestamp', 'design_decisions', ['timestamp'], schema='shared')

    # Create open_source_selections table
    op.create_table(
        'open_source_selections',
        sa.Column('selection_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('library_name', sa.String(length=200), nullable=False),
        sa.Column('github_url', sa.String(length=500), nullable=True),
        sa.Column('npm_url', sa.String(length=500), nullable=True),
        sa.Column('stars', sa.Integer(), nullable=True),
        sa.Column('license', sa.String(length=50), nullable=True),
        sa.Column('bundle_size', sa.String(length=50), nullable=True),
        sa.Column('version', sa.String(length=50), nullable=True),
        sa.Column('ranking_score', sa.Float(), nullable=True),
        sa.Column('rationale', sa.Text(), nullable=False),
        sa.Column('alternatives', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['job_id'], ['shared.design_jobs.job_id'], ),
        sa.PrimaryKeyConstraint('selection_id'),
        schema='shared'
    )
    op.create_index('idx_opensearch_job_id', 'open_source_selections', ['job_id'], schema='shared')
    op.create_index('idx_opensearch_category', 'open_source_selections', ['category'], schema='shared')
    op.create_index('idx_opensearch_timestamp', 'open_source_selections', ['timestamp'], schema='shared')

    # ========================================================================
    # DESIGN AGENT SCHEMA TABLES
    # ========================================================================

    # Create sessions table
    op.create_table(
        'sessions',
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('langgraph_thread_id', sa.String(length=100), nullable=False),
        sa.Column('state_snapshot', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('current_phase', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('pause_reason', sa.String(length=200), nullable=True),
        sa.Column('is_paused', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['job_id'], ['shared.design_jobs.job_id'], ),
        sa.PrimaryKeyConstraint('session_id'),
        sa.UniqueConstraint('job_id'),
        sa.UniqueConstraint('langgraph_thread_id'),
        schema='design_agent'
    )
    op.create_index('idx_sessions_job_id', 'sessions', ['job_id'], schema='design_agent')
    op.create_index('idx_sessions_langgraph_thread_id', 'sessions', ['langgraph_thread_id'], schema='design_agent')
    op.create_index('idx_sessions_created_at', 'sessions', ['created_at'], schema='design_agent')

    # Create checkpoints table (LangGraph)
    op.create_table(
        'checkpoints',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('thread_id', sa.String(length=100), nullable=False),
        sa.Column('checkpoint_ns', sa.String(length=100), nullable=False, server_default=''),
        sa.Column('checkpoint_id', sa.String(length=100), nullable=False),
        sa.Column('parent_checkpoint_id', sa.String(length=100), nullable=True),
        sa.Column('type', sa.String(length=50), nullable=False, server_default='checkpoint'),
        sa.Column('checkpoint', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        schema='design_agent'
    )
    op.create_index('idx_checkpoints_thread_id', 'checkpoints', ['thread_id'], schema='design_agent')
    op.create_index('idx_checkpoints_checkpoint_id', 'checkpoints', ['checkpoint_id'], schema='design_agent')
    op.create_index('idx_checkpoints_parent_checkpoint_id', 'checkpoints', ['parent_checkpoint_id'], schema='design_agent')
    op.create_index('idx_checkpoints_created_at', 'checkpoints', ['created_at'], schema='design_agent')

    # ========================================================================
    # POSTGRESQL NOTIFY TRIGGER
    # ========================================================================

    # Create function to notify on new job
    op.execute("""
        CREATE OR REPLACE FUNCTION shared.notify_new_job_func()
        RETURNS TRIGGER AS $$
        BEGIN
            PERFORM pg_notify(
                'new_design_job',
                json_build_object(
                    'job_id', NEW.job_id::text,
                    'project_id', NEW.project_id,
                    'user_id', NEW.user_id,
                    'status', NEW.status,
                    'created_at', NEW.created_at
                )::text
            );
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    # Create trigger on design_jobs table
    op.execute("""
        CREATE TRIGGER notify_new_job
        AFTER INSERT ON shared.design_jobs
        FOR EACH ROW
        WHEN (NEW.status = 'pending')
        EXECUTE FUNCTION shared.notify_new_job_func();
    """)


def downgrade() -> None:
    # Drop trigger and function
    op.execute("DROP TRIGGER IF EXISTS notify_new_job ON shared.design_jobs")
    op.execute("DROP FUNCTION IF EXISTS shared.notify_new_job_func()")

    # Drop design_agent schema tables
    op.drop_index('idx_checkpoints_created_at', table_name='checkpoints', schema='design_agent')
    op.drop_index('idx_checkpoints_parent_checkpoint_id', table_name='checkpoints', schema='design_agent')
    op.drop_index('idx_checkpoints_checkpoint_id', table_name='checkpoints', schema='design_agent')
    op.drop_index('idx_checkpoints_thread_id', table_name='checkpoints', schema='design_agent')
    op.drop_table('checkpoints', schema='design_agent')

    op.drop_index('idx_sessions_created_at', table_name='sessions', schema='design_agent')
    op.drop_index('idx_sessions_langgraph_thread_id', table_name='sessions', schema='design_agent')
    op.drop_index('idx_sessions_job_id', table_name='sessions', schema='design_agent')
    op.drop_table('sessions', schema='design_agent')

    # Drop shared schema tables
    op.drop_index('idx_opensearch_timestamp', table_name='open_source_selections', schema='shared')
    op.drop_index('idx_opensearch_category', table_name='open_source_selections', schema='shared')
    op.drop_index('idx_opensearch_job_id', table_name='open_source_selections', schema='shared')
    op.drop_table('open_source_selections', schema='shared')

    op.drop_index('idx_design_decisions_timestamp', table_name='design_decisions', schema='shared')
    op.drop_index('idx_design_decisions_screen_name', table_name='design_decisions', schema='shared')
    op.drop_index('idx_design_decisions_job_id', table_name='design_decisions', schema='shared')
    op.drop_table('design_decisions', schema='shared')

    op.drop_index('idx_design_outputs_created_at', table_name='design_outputs', schema='shared')
    op.drop_index('idx_design_outputs_document_type', table_name='design_outputs', schema='shared')
    op.drop_index('idx_design_outputs_job_id', table_name='design_outputs', schema='shared')
    op.drop_table('design_outputs', schema='shared')

    op.drop_index('idx_design_progress_last_updated', table_name='design_progress', schema='shared')
    op.drop_index('idx_design_progress_job_id', table_name='design_progress', schema='shared')
    op.drop_table('design_progress', schema='shared')

    op.drop_index('idx_design_jobs_project_id', table_name='design_jobs', schema='shared')
    op.drop_index('idx_design_jobs_created_at', table_name='design_jobs', schema='shared')
    op.drop_index('idx_design_jobs_status', table_name='design_jobs', schema='shared')
    op.drop_table('design_jobs', schema='shared')

    # Drop schemas
    op.execute("DROP SCHEMA IF EXISTS design_agent CASCADE")
    op.execute("DROP SCHEMA IF EXISTS shared CASCADE")
