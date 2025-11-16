"""
SQLAlchemy database models for Design Agent.

This module defines all database tables using SQLAlchemy ORM:
- Shared schema: Integration tables (design_jobs, design_progress, design_outputs, etc.)
- Design Agent schema: Internal tables (sessions, checkpoints)
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all models."""

    pass


# ============================================================================
# SHARED SCHEMA - Integration tables for ANYON <-> Design Agent communication
# ============================================================================


class DesignJob(Base):
    """
    Job queue table for triggering Design Agent.

    ANYON inserts rows here to trigger new design sessions.
    Design Agent listens via PostgreSQL LISTEN/NOTIFY for instant pickup.
    """

    __tablename__ = "design_jobs"
    __table_args__ = (
        Index("idx_design_jobs_status", "status"),
        Index("idx_design_jobs_created_at", "created_at"),
        Index("idx_design_jobs_project_id", "project_id"),
        {"schema": "shared"},
    )

    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[str] = mapped_column(String(100), nullable=False)
    user_id: Mapped[str] = mapped_column(String(100), nullable=False)
    prd_content: Mapped[str] = mapped_column(Text, nullable=False)
    trd_content: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="pending",
        comment="pending, running, paused_waiting_for_upload, completed, failed",
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    progress: Mapped[Optional["DesignProgress"]] = relationship(
        "DesignProgress", back_populates="job", uselist=False
    )
    outputs: Mapped[list["DesignOutput"]] = relationship("DesignOutput", back_populates="job")
    decisions: Mapped[list["DesignDecision"]] = relationship("DesignDecision", back_populates="job")
    open_source_selections: Mapped[list["OpenSourceSelection"]] = relationship(
        "OpenSourceSelection", back_populates="job"
    )
    session: Mapped[Optional["Session"]] = relationship("Session", back_populates="job", uselist=False)


class DesignProgress(Base):
    """
    Real-time progress tracking table.

    Updated every 5-10 seconds during active design sessions.
    ANYON reads this for live progress bars and status displays.
    """

    __tablename__ = "design_progress"
    __table_args__ = (
        Index("idx_design_progress_job_id", "job_id"),
        Index("idx_design_progress_last_updated", "last_updated"),
        {"schema": "shared"},
    )

    progress_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("shared.design_jobs.job_id"), nullable=False, unique=True
    )
    current_phase: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, comment="1-6 representing the current phase"
    )
    phase_name: Mapped[str] = mapped_column(String(100), nullable=False)
    progress_percent: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0, comment="0.0 to 100.0"
    )
    screen_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completed_screens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    estimated_time_remaining: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="Seconds remaining"
    )
    last_updated: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    job: Mapped["DesignJob"] = relationship("DesignJob", back_populates="progress")


class DesignOutput(Base):
    """
    Generated documents and validation reports.

    Stores all 6 markdown documents plus validation reports.
    ANYON reads this to display/download completed documents.
    """

    __tablename__ = "design_outputs"
    __table_args__ = (
        Index("idx_design_outputs_job_id", "job_id"),
        Index("idx_design_outputs_document_type", "document_type"),
        Index("idx_design_outputs_created_at", "created_at"),
        UniqueConstraint("job_id", "document_type", "version", name="uq_job_doc_version"),
        {"schema": "shared"},
    )

    output_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("shared.design_jobs.job_id"), nullable=False
    )
    document_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="design_system, ux_flow, screen_specs, ai_prompts, guidelines, opensource_recs, validation_report",
    )
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    version: Mapped[str] = mapped_column(String(20), nullable=False, default="0.9")
    document_metadata: Mapped[Optional[dict]] = mapped_column("metadata", JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    job: Mapped["DesignJob"] = relationship("DesignJob", back_populates="outputs")


class DesignDecision(Base):
    """
    Design decision audit log.

    Tracks all design choices, rationale, and alternatives considered.
    Useful for understanding "why" decisions were made and for compliance.
    """

    __tablename__ = "design_decisions"
    __table_args__ = (
        Index("idx_design_decisions_job_id", "job_id"),
        Index("idx_design_decisions_screen_name", "screen_name"),
        Index("idx_design_decisions_timestamp", "timestamp"),
        {"schema": "shared"},
    )

    decision_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("shared.design_jobs.job_id"), nullable=False
    )
    screen_name: Mapped[str] = mapped_column(String(200), nullable=False)
    decision_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="layout_choice, color_selection, typography, spacing, component_choice, etc.",
    )
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    alternatives: Mapped[Optional[dict]] = mapped_column(
        JSONB, nullable=True, comment="List of alternatives considered"
    )
    user_feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    job: Mapped["DesignJob"] = relationship("DesignJob", back_populates="decisions")


class OpenSourceSelection(Base):
    """
    Selected open-source libraries and recommendations.

    Tracks which libraries were recommended and selected during Phase 3.
    Integrated into Open_Source_Recommendations_v0.9.md document.
    """

    __tablename__ = "open_source_selections"
    __table_args__ = (
        Index("idx_opensearch_job_id", "job_id"),
        Index("idx_opensearch_category", "category"),
        Index("idx_opensearch_timestamp", "timestamp"),
        {"schema": "shared"},
    )

    selection_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("shared.design_jobs.job_id"), nullable=False
    )
    category: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="ui_components, forms, icons, charts, animation, date_time, etc.",
    )
    library_name: Mapped[str] = mapped_column(String(200), nullable=False)
    github_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    npm_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    stars: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    license: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    bundle_size: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    ranking_score: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="0-100 score from ranking algorithm"
    )
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    alternatives: Mapped[Optional[dict]] = mapped_column(
        JSONB, nullable=True, comment="Other options presented to user"
    )
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    job: Mapped["DesignJob"] = relationship("DesignJob", back_populates="open_source_selections")


# ============================================================================
# DESIGN AGENT SCHEMA - Internal tables
# ============================================================================


class Session(Base):
    """
    Design Agent session state management.

    Internal table for tracking active sessions and linking to LangGraph checkpoints.
    """

    __tablename__ = "sessions"
    __table_args__ = (
        Index("idx_sessions_job_id", "job_id"),
        Index("idx_sessions_langgraph_thread_id", "langgraph_thread_id"),
        Index("idx_sessions_created_at", "created_at"),
        {"schema": "design_agent"},
    )

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("shared.design_jobs.job_id"), nullable=False, unique=True
    )
    langgraph_thread_id: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    state_snapshot: Mapped[Optional[dict]] = mapped_column(
        JSONB, nullable=True, comment="Current state for quick access"
    )
    current_phase: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    pause_reason: Mapped[Optional[str]] = mapped_column(
        String(200), nullable=True, comment="google_ai_studio, error, user_request, etc."
    )
    is_paused: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    job: Mapped["DesignJob"] = relationship("DesignJob", back_populates="session")


class Checkpoint(Base):
    """
    LangGraph checkpoint storage.

    Standard LangGraph checkpoint table for state persistence and pause/resume.
    """

    __tablename__ = "checkpoints"
    __table_args__ = (
        Index("idx_checkpoints_thread_id", "thread_id"),
        Index("idx_checkpoints_checkpoint_id", "checkpoint_id"),
        Index("idx_checkpoints_parent_checkpoint_id", "parent_checkpoint_id"),
        Index("idx_checkpoints_created_at", "created_at"),
        {"schema": "design_agent"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    thread_id: Mapped[str] = mapped_column(String(100), nullable=False)
    checkpoint_ns: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    checkpoint_id: Mapped[str] = mapped_column(String(100), nullable=False)
    parent_checkpoint_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    type: Mapped[str] = mapped_column(String(50), nullable=False, default="checkpoint")
    checkpoint: Mapped[dict] = mapped_column(
        JSONB, nullable=False, comment="Full LangGraph state snapshot"
    )
    checkpoint_metadata: Mapped[Optional[dict]] = mapped_column(
        JSONB, nullable=True, comment="Additional checkpoint metadata"
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)


# ============================================================================
# Export all models
# ============================================================================

__all__ = [
    "Base",
    "DesignJob",
    "DesignProgress",
    "DesignOutput",
    "DesignDecision",
    "OpenSourceSelection",
    "Session",
    "Checkpoint",
]
