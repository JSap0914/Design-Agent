"""
Phase 5: Code Validation Node.

Validates uploaded code for:
- Syntax correctness
- TypeScript compliance
- Tailwind CSS only (no custom CSS)
- Accessibility (WCAG AA)
- Overall quality score (0-100, minimum 90)
"""

from typing import Any

from src.database.validation_storage import store_validation_results
from src.langgraph.state import DesignAgentState
from src.utils.logger import get_logger
from src.validators.accessibility_validator import validate_accessibility_comprehensive
from src.validators.code_validator import validate_code_comprehensive
from src.validators.quality_scorer import MIN_ACCEPTABLE_SCORE, calculate_quality_score

logger = get_logger(__name__)


async def validate_code(state: DesignAgentState) -> DesignAgentState:
    """
    Phase 5: Validate uploaded code comprehensively.

    This node:
    1. Retrieves uploaded code from state
    2. Runs all validators (syntax, TypeScript, Tailwind, accessibility)
    3. Calculates quality score (0-100)
    4. Checks if score meets minimum threshold (90/100)
    5. Stores validation results in state

    Args:
        state: Current workflow state with uploaded_code

    Returns:
        Updated state with validation_results and quality_score
    """
    logger.info("Phase 5: Validating uploaded code", job_id=state.get("job_id"))

    try:
        uploaded_code = state.get("uploaded_code")
        uploaded_code_metadata = state.get("uploaded_code_metadata", {})
        design_system = state.get("design_system")

        if not uploaded_code:
            logger.error("No uploaded code found in state")
            errors = state.get("errors", [])
            errors.append("No uploaded code to validate")

            return {
                **state,
                "errors": errors,
                "should_retry": True,
                "retry_count": state.get("retry_count", 0) + 1,
            }

        # Determine file extension
        file_extension = uploaded_code_metadata.get("file_extension", ".tsx")

        # Step 1: Run code validation (syntax, TypeScript, Tailwind)
        logger.info("Running code validation", file_extension=file_extension)
        code_validation_result = await validate_code_comprehensive(
            code=uploaded_code,
            file_extension=file_extension,
        )

        # Step 2: Run accessibility validation
        logger.info("Running accessibility validation")
        accessibility_result = await validate_accessibility_comprehensive(
            code=uploaded_code,
            design_system=design_system,
        )

        # Step 3: Calculate quality score
        logger.info("Calculating quality score")
        quality_result = calculate_quality_score(
            syntax_result={
                "valid": code_validation_result["syntax_valid"],
                "errors": [e for e in code_validation_result["errors"] if "syntax" in e.lower()],
                "warnings": [w for w in code_validation_result["warnings"] if "syntax" in w.lower()],
            },
            typescript_result={
                "valid": code_validation_result["typescript_valid"],
                "has_types": code_validation_result.get("type_coverage", 0) > 0,
                "type_coverage": code_validation_result.get("type_coverage", 0),
                "errors": [e for e in code_validation_result["errors"] if "typescript" in e.lower() or "type" in e.lower()],
                "warnings": [w for w in code_validation_result["warnings"] if "typescript" in w.lower() or "type" in w.lower()],
            },
            tailwind_result={
                "valid": code_validation_result["tailwind_only"],
                "has_custom_css": code_validation_result["has_custom_css"],
                "custom_css_locations": [],
                "errors": [e for e in code_validation_result["errors"] if "css" in e.lower() or "tailwind" in e.lower()],
            },
            accessibility_result=accessibility_result,
        )

        overall_score = quality_result["overall_score"]
        meets_minimum = quality_result["meets_minimum"]
        grade = quality_result["grade"]

        # Step 4: Determine if validation passed
        all_valid = code_validation_result["all_valid"] and accessibility_result["wcag_aa_compliant"]

        logger.info(
            "Validation complete",
            overall_score=overall_score,
            grade=grade,
            meets_minimum=meets_minimum,
            all_valid=all_valid,
        )

        # Step 5: Build comprehensive validation results
        validation_results = {
            "overall_score": overall_score,
            "grade": grade,
            "meets_minimum": meets_minimum,
            "all_valid": all_valid,
            "component_scores": quality_result["component_scores"],
            "code_validation": {
                "syntax_valid": code_validation_result["syntax_valid"],
                "typescript_valid": code_validation_result["typescript_valid"],
                "tailwind_only": code_validation_result["tailwind_only"],
                "type_coverage": code_validation_result.get("type_coverage", 0),
                "has_custom_css": code_validation_result["has_custom_css"],
                "errors": code_validation_result["errors"],
                "warnings": code_validation_result["warnings"],
            },
            "accessibility_validation": {
                "wcag_aa_compliant": accessibility_result["wcag_aa_compliant"],
                "contrast_valid": accessibility_result["contrast_valid"],
                "touch_targets_valid": accessibility_result["touch_targets_valid"],
                "alt_text_valid": accessibility_result["alt_text_valid"],
                "aria_valid": accessibility_result["aria_valid"],
                "semantic_html_valid": accessibility_result["semantic_html_valid"],
                "keyboard_accessible": accessibility_result["keyboard_accessible"],
                "issues": accessibility_result["issues"],
                "warnings": accessibility_result["warnings"],
            },
            "quality_breakdown": quality_result["detailed_breakdown"],
            "rationale": quality_result["rationale"],
        }

        # Step 6: Store validation results in database
        storage_result = await store_validation_results(
            job_id=state.get("job_id", "unknown"),
            validation_results=validation_results,
            uploaded_code=uploaded_code,
            uploaded_code_metadata=uploaded_code_metadata,
        )

        if not storage_result.get("success"):
            logger.warning(
                "Failed to store validation results",
                error=storage_result.get("error"),
            )
            # Continue anyway - storage failure shouldn't block validation
        else:
            logger.info(
                "Validation results stored",
                stored_id=storage_result.get("stored_id"),
            )

        # Step 7: Update state with validation results
        return {
            **state,
            "validation_results": validation_results,
            "validation_stored_id": storage_result.get("stored_id"),
            "quality_score": overall_score,
            "validation_passed": meets_minimum and all_valid,
            "current_phase": 5,
            "phase_name": f"Code Validated - Score: {overall_score:.1f}/100 ({grade})",
            "progress_percent": 85.0,
        }

    except Exception as e:
        logger.error("Error validating code", error=str(e), job_id=state.get("job_id"))

        errors = state.get("errors", [])
        errors.append(f"Code validation failed: {str(e)}")

        return {
            **state,
            "errors": errors,
            "should_retry": True,
            "retry_count": state.get("retry_count", 0) + 1,
        }


def should_proceed_after_validation(state: DesignAgentState) -> str:
    """
    Conditional routing function for validate_code node.

    Returns:
        - "validation_passed" if code meets quality standards (90/100+)
        - "validation_failed" if code does not meet standards
        - "retry" if validation had errors and should retry
    """
    # Check for validation errors
    if state.get("should_retry") and state.get("retry_count", 0) < 3:
        logger.info("Validation had errors, routing to retry")
        return "retry"

    # Check if validation passed
    validation_passed = state.get("validation_passed", False)
    quality_score = state.get("quality_score", 0)

    if validation_passed and quality_score >= MIN_ACCEPTABLE_SCORE:
        logger.info(
            "Validation passed, proceeding to Phase 6",
            quality_score=quality_score,
        )
        return "validation_passed"
    else:
        logger.warning(
            "Validation failed - code does not meet quality standards",
            quality_score=quality_score,
            minimum_required=MIN_ACCEPTABLE_SCORE,
        )
        return "validation_failed"


async def handle_validation_failure(state: DesignAgentState) -> DesignAgentState:
    """
    Handle validation failure by providing feedback to user.

    This node:
    1. Extracts validation errors and warnings
    2. Formats user-friendly feedback
    3. Sets awaiting_feedback flag for user to fix code
    4. User can either:
       - Re-upload improved code
       - Override validation (proceed anyway with warning)

    Args:
        state: Current workflow state with failed validation

    Returns:
        Updated state with feedback message
    """
    logger.info("Handling validation failure", job_id=state.get("job_id"))

    validation_results = state.get("validation_results", {})
    quality_score = state.get("quality_score", 0)
    grade = validation_results.get("grade", "F")

    # Extract all issues
    code_errors = validation_results.get("code_validation", {}).get("errors", [])
    code_warnings = validation_results.get("code_validation", {}).get("warnings", [])
    accessibility_issues = validation_results.get("accessibility_validation", {}).get("issues", [])
    accessibility_warnings = validation_results.get("accessibility_validation", {}).get("warnings", [])

    # Build feedback message
    feedback_message = f"""
Code Validation Failed - Score: {quality_score:.1f}/100 (Grade: {grade})
Minimum required: {MIN_ACCEPTABLE_SCORE}/100 (Grade: A-)

Issues Found:

Code Quality:
{chr(10).join(f"  ❌ {e}" for e in code_errors) if code_errors else "  ✓ No code errors"}
{chr(10).join(f"  ⚠️  {w}" for w in code_warnings) if code_warnings else ""}

Accessibility (WCAG AA):
{chr(10).join(f"  ❌ {i}" for i in accessibility_issues) if accessibility_issues else "  ✓ No accessibility issues"}
{chr(10).join(f"  ⚠️  {w}" for w in accessibility_warnings) if accessibility_warnings else ""}

Component Scores:
  - Syntax: {validation_results.get("component_scores", {}).get("syntax", 0):.1f}/100
  - TypeScript: {validation_results.get("component_scores", {}).get("typescript", 0):.1f}/100
  - Tailwind: {validation_results.get("component_scores", {}).get("tailwind", 0):.1f}/100
  - Accessibility: {validation_results.get("component_scores", {}).get("accessibility", 0):.1f}/100

Please fix the issues and re-upload, or type "override" to proceed anyway (not recommended).
"""

    return {
        **state,
        "awaiting_feedback": True,
        "validation_feedback": feedback_message,
        "phase_name": "Validation Failed - Awaiting Code Fix",
        "progress_percent": 82.0,
    }


__all__ = [
    "validate_code",
    "should_proceed_after_validation",
    "handle_validation_failure",
]
