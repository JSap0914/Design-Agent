"""
LangGraph state schema for Design Agent.

This module defines the state that flows through the 6-phase design workflow.
"""

from typing import Any, TypedDict


class OpenSourceRecommendation(TypedDict):
    """Open-source library recommendation."""

    category: str  # ui_components, forms, icons, charts, etc.
    library_name: str
    github_url: str | None
    npm_url: str | None
    stars: int | None
    license: str | None
    bundle_size: str | None
    version: str | None
    ranking_score: float | None  # 0-100
    rationale: str
    alternatives: list[dict[str, Any]] | None  # Other options presented


class DesignDecision(TypedDict):
    """Design decision with rationale."""

    screen_name: str
    decision_type: str  # layout_choice, color_selection, typography, spacing, etc.
    rationale: str
    alternatives: list[str] | None
    user_feedback: str | None


class ValidationResult(TypedDict):
    """Code validation result."""

    syntax_valid: bool
    typescript_valid: bool
    tailwind_only: bool
    accessibility_score: float  # 0-100
    design_system_compliant: bool
    quality_score: float  # 0-100 overall score
    errors: list[str]
    warnings: list[str]


class DesignSystemSpec(TypedDict):
    """Design system specification."""

    colors: dict[str, Any]  # Primary, secondary, semantic colors
    typography: dict[str, Any]  # Fonts, sizes, weights
    spacing: dict[str, Any]  # 8pt grid system
    border_radius: dict[str, Any]
    shadows: dict[str, Any]
    icons: dict[str, Any]
    component_libraries: list[str]  # Selected open-source libraries


class DesignAgentState(TypedDict, total=False):
    """
    State for the Design Agent LangGraph workflow.

    This state flows through all 6 phases:
    1. Screen extraction
    2. Layout option generation
    3. ASCII UI creation and refinement
    4. Design System extraction
    5. Optional pause/resume with code validation
    6. Document generation

    All fields are optional (total=False) to allow incremental state building.
    """

    # ========================================================================
    # Input (from ANYON)
    # ========================================================================
    job_id: str  # UUID as string
    project_id: str
    user_id: str
    prd_content: str  # Product Requirements Document
    trd_content: str  # Technical Requirements Document

    # ========================================================================
    # Phase 1: Screen Extraction
    # ========================================================================
    extracted_screens: list[str]  # List of screen names
    screen_count: int

    # ========================================================================
    # Phase 2: Layout Options
    # ========================================================================
    design_options: dict[str, list[str]]  # screen_name -> [option1_ascii, option2_ascii, option3_ascii]
    design_options_metadata: dict[
        str, list[dict[str, Any]]
    ]  # Additional metadata for each option

    # ========================================================================
    # Phase 3: ASCII UI Refinement
    # ========================================================================
    selected_designs: dict[str, str]  # screen_name -> final_ascii_ui
    design_decisions: list[DesignDecision]  # All design decisions with rationale
    user_interactions: list[dict[str, Any]]  # Log of user feedback and changes
    completed_screens: int  # Count of finalized screens
    current_screen_index: int  # Which screen we're currently refining (0-based index)
    current_screen_name: str  # Name of screen being refined
    user_feedback: str | None  # Current user feedback for modifications
    awaiting_feedback: bool  # True if waiting for user input via WebSocket
    refinement_complete: bool  # True when all screens approved and refinement done

    # ========================================================================
    # Phase 3 (NEW): Open-Source Discovery
    # ========================================================================
    open_source_suggestions: list[
        OpenSourceRecommendation
    ]  # All recommendations shown to user
    selected_open_source: list[OpenSourceRecommendation]  # User-selected libraries
    awaiting_library_selection: bool  # True if waiting for user to select library
    pending_library_options: list[dict[str, Any]]  # Libraries currently being presented
    pending_library_query: str | None  # Search query for pending options
    pending_library_category: str | None  # Category for pending options

    # ========================================================================
    # Phase 4: Design System Extraction
    # ========================================================================
    design_system: DesignSystemSpec  # Extracted from approved designs

    # ========================================================================
    # Phase 5: Optional Pause/Resume & Validation (Google AI Studio)
    # ========================================================================
    should_pause_for_google_ai: bool  # User choice: pause or skip to documents
    paused: bool  # True if waiting for user to upload code
    uploaded_code: str | None  # User-created design code from Google AI Studio
    uploaded_code_metadata: dict[str, Any] | None  # File names, structure, etc.
    validation_results: ValidationResult | None  # Code validation results

    # ========================================================================
    # Phase 6: Document Generation
    # ========================================================================
    generated_documents: dict[str, str]  # document_type -> markdown_content
    # document_type: design_system, ux_flow, screen_specs, ai_prompts, guidelines, opensource_recs

    # ========================================================================
    # Workflow Control
    # ========================================================================
    current_phase: int  # 1-6
    phase_name: str  # Human-readable phase name
    progress_percent: float  # 0-100
    estimated_time_remaining: int | None  # Seconds

    # ========================================================================
    # Error Handling
    # ========================================================================
    errors: list[str]  # Accumulated errors
    retry_count: int  # Number of retries for current operation
    should_retry: bool  # Whether to retry current operation

    # ========================================================================
    # BMAD Methodology Tracking
    # ========================================================================
    options_provided_count: int  # Track that we always provide 2-3 options
    require_rationale: bool  # Ensure decision rationale is captured


# Export for easy import
__all__ = [
    "DesignAgentState",
    "OpenSourceRecommendation",
    "DesignDecision",
    "ValidationResult",
    "DesignSystemSpec",
]
