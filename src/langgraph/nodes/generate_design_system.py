"""
Phase 4: Design System Extraction Node.

Analyzes approved ASCII UI designs and extracts a comprehensive Design System
including colors, typography, spacing, borders, shadows, and icons.
"""

from src.langgraph.state import DesignAgentState, DesignSystemSpec
from src.llm.client import llm_client
from src.llm.prompts import format_design_system_extraction_prompt
from src.utils.logger import get_logger

logger = get_logger(__name__)


async def generate_design_system(state: DesignAgentState) -> DesignAgentState:
    """
    Phase 4: Extract Design System from approved ASCII UI designs.

    This node:
    1. Takes all approved ASCII UIs from Phase 3
    2. Analyzes them to extract common design patterns
    3. Generates a comprehensive Design System specification
    4. Updates progress to 70%

    Args:
        state: Current workflow state with selected_designs

    Returns:
        Updated state with design_system
    """
    logger.info("Phase 4: Extracting Design System", job_id=state.get("job_id"))

    try:
        selected_designs = state.get("selected_designs", {})
        design_decisions = state.get("design_decisions", [])
        selected_open_source = state.get("selected_open_source", [])

        if not selected_designs:
            logger.warning("No approved designs found, using defaults")
            # Create minimal design system
            design_system = _create_default_design_system()
        else:
            # Format prompt for LLM
            system_prompt, user_prompt = format_design_system_extraction_prompt(
                selected_designs=selected_designs,
                design_decisions=design_decisions,
                selected_open_source=selected_open_source,
            )

            # Call LLM to extract Design System
            design_system_json = await llm_client.complete_with_json(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.3,  # Low temperature for consistency
            )

            # Validate and structure Design System
            design_system = _validate_design_system(design_system_json)

        logger.info(
            "Design System extracted",
            colors_count=len(design_system.get("colors", {}).get("primary", [])),
            typography_count=len(design_system.get("typography", {}).get("sizes", [])),
            component_libraries_count=len(design_system.get("component_libraries", [])),
        )

        return {
            **state,
            "design_system": design_system,
            "current_phase": 4,
            "phase_name": "Design System Extracted",
            "progress_percent": 70.0,
        }

    except Exception as e:
        logger.error("Error extracting Design System", error=str(e), job_id=state.get("job_id"))

        errors = state.get("errors", [])
        errors.append(f"Design System extraction failed: {str(e)}")

        return {
            **state,
            "errors": errors,
            "should_retry": True,
            "retry_count": state.get("retry_count", 0) + 1,
        }


def _create_default_design_system() -> DesignSystemSpec:
    """
    Create a default Design System when no approved designs are available.

    Returns:
        Default DesignSystemSpec with standard values
    """
    return {
        "colors": {
            "primary": ["#3B82F6", "#2563EB", "#1D4ED8"],  # Blue shades
            "secondary": ["#8B5CF6", "#7C3AED", "#6D28D9"],  # Purple shades
            "semantic": {
                "success": "#10B981",
                "warning": "#F59E0B",
                "error": "#EF4444",
                "info": "#3B82F6",
            },
            "neutrals": {
                "black": "#000000",
                "white": "#FFFFFF",
                "gray": ["#F9FAFB", "#F3F4F6", "#E5E7EB", "#D1D5DB", "#9CA3AF", "#6B7280", "#4B5563", "#374151", "#1F2937", "#111827"],
            },
        },
        "typography": {
            "font_families": {
                "primary": "Inter, system-ui, -apple-system, sans-serif",
                "monospace": "Fira Code, Consolas, monospace",
            },
            "sizes": {
                "xs": "12px",
                "sm": "14px",
                "base": "16px",
                "lg": "18px",
                "xl": "20px",
                "2xl": "24px",
                "3xl": "30px",
                "4xl": "36px",
            },
            "weights": {
                "normal": "400",
                "medium": "500",
                "semibold": "600",
                "bold": "700",
            },
            "line_heights": {
                "tight": "1.25",
                "normal": "1.5",
                "relaxed": "1.75",
            },
        },
        "spacing": {
            "scale": "8pt grid",
            "values": {
                "0": "0px",
                "1": "4px",
                "2": "8px",
                "3": "12px",
                "4": "16px",
                "5": "20px",
                "6": "24px",
                "8": "32px",
                "10": "40px",
                "12": "48px",
                "16": "64px",
                "20": "80px",
            },
        },
        "border_radius": {
            "none": "0px",
            "sm": "4px",
            "base": "8px",
            "md": "12px",
            "lg": "16px",
            "xl": "24px",
            "full": "9999px",
        },
        "shadows": {
            "sm": "0 1px 2px 0 rgba(0, 0, 0, 0.05)",
            "base": "0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)",
            "md": "0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)",
            "lg": "0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)",
            "xl": "0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)",
        },
        "icons": {
            "style": "outline",
            "size": "24px",
            "stroke_width": "2px",
        },
        "component_libraries": [],
    }


def _validate_design_system(design_system_json: dict) -> DesignSystemSpec:
    """
    Validate and normalize Design System JSON from LLM.

    Args:
        design_system_json: Raw JSON from LLM

    Returns:
        Validated DesignSystemSpec
    """
    # Merge with defaults to ensure all required fields exist
    default_system = _create_default_design_system()

    return {
        "colors": design_system_json.get("colors", default_system["colors"]),
        "typography": design_system_json.get("typography", default_system["typography"]),
        "spacing": design_system_json.get("spacing", default_system["spacing"]),
        "border_radius": design_system_json.get("border_radius", default_system["border_radius"]),
        "shadows": design_system_json.get("shadows", default_system["shadows"]),
        "icons": design_system_json.get("icons", default_system["icons"]),
        "component_libraries": design_system_json.get("component_libraries", []),
    }


__all__ = ["generate_design_system"]
