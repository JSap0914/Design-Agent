"""
Quality scoring algorithm for uploaded design code.

Calculates comprehensive quality score (0-100) based on:
- Syntax correctness (20%)
- TypeScript compliance (20%)
- Tailwind-only enforcement (20%)
- Accessibility (WCAG AA) (40%)

Target: 90/100 minimum for acceptance.
"""

from typing import Any

from src.utils.logger import get_logger

logger = get_logger(__name__)


# Scoring weights
WEIGHTS = {
    "syntax": 0.20,  # 20%
    "typescript": 0.20,  # 20%
    "tailwind": 0.20,  # 20%
    "accessibility": 0.40,  # 40%
}

# Deduction values
DEDUCTIONS = {
    "error": 5.0,  # -5 points per error
    "warning": 1.0,  # -1 point per warning
}

# Minimum acceptable score
MIN_ACCEPTABLE_SCORE = 90.0


def calculate_syntax_score(syntax_result: dict[str, Any]) -> dict[str, Any]:
    """
    Calculate syntax quality score (0-100).

    Args:
        syntax_result: Result from validate_syntax()

    Returns:
        Dict with:
        - score: float (0-100)
        - deductions: dict with breakdown
        - rationale: str
    """
    base_score = 100.0
    deductions = {}

    # Deduct for errors
    error_count = len(syntax_result.get("errors", []))
    error_deduction = error_count * DEDUCTIONS["error"]
    deductions["syntax_errors"] = error_deduction

    # Deduct for warnings
    warning_count = len(syntax_result.get("warnings", []))
    warning_deduction = warning_count * DEDUCTIONS["warning"]
    deductions["syntax_warnings"] = warning_deduction

    total_deduction = error_deduction + warning_deduction
    final_score = max(0.0, base_score - total_deduction)

    rationale = f"Syntax: {error_count} errors, {warning_count} warnings"

    return {
        "score": final_score,
        "deductions": deductions,
        "rationale": rationale,
    }


def calculate_typescript_score(typescript_result: dict[str, Any]) -> dict[str, Any]:
    """
    Calculate TypeScript quality score (0-100).

    Args:
        typescript_result: Result from validate_typescript()

    Returns:
        Dict with:
        - score: float (0-100)
        - deductions: dict with breakdown
        - rationale: str
    """
    base_score = 100.0
    deductions = {}

    # Deduct for errors
    error_count = len(typescript_result.get("errors", []))
    error_deduction = error_count * DEDUCTIONS["error"]
    deductions["typescript_errors"] = error_deduction

    # Deduct for warnings
    warning_count = len(typescript_result.get("warnings", []))
    warning_deduction = warning_count * DEDUCTIONS["warning"]
    deductions["typescript_warnings"] = warning_deduction

    # Bonus/penalty for type coverage
    type_coverage = typescript_result.get("type_coverage", 0.0)
    has_types = typescript_result.get("has_types", False)

    if not has_types:
        # No types detected - significant penalty
        deductions["no_typescript"] = 30.0
    elif type_coverage < 0.5:
        # Low type coverage - moderate penalty
        coverage_penalty = (0.5 - type_coverage) * 40  # Up to -20 points
        deductions["low_type_coverage"] = coverage_penalty
    elif type_coverage >= 0.8:
        # High type coverage - small bonus
        deductions["high_type_coverage"] = -5.0  # Bonus

    total_deduction = sum(deductions.values())
    final_score = max(0.0, min(100.0, base_score - total_deduction))

    rationale = (
        f"TypeScript: {error_count} errors, {warning_count} warnings, "
        f"{type_coverage:.0%} type coverage"
    )

    return {
        "score": final_score,
        "deductions": deductions,
        "rationale": rationale,
    }


def calculate_tailwind_score(tailwind_result: dict[str, Any]) -> dict[str, Any]:
    """
    Calculate Tailwind-only enforcement score (0-100).

    Args:
        tailwind_result: Result from validate_tailwind_only()

    Returns:
        Dict with:
        - score: float (0-100)
        - deductions: dict with breakdown
        - rationale: str
    """
    base_score = 100.0
    deductions = {}

    # Deduct for custom CSS violations
    error_count = len(tailwind_result.get("errors", []))
    custom_css_count = len(tailwind_result.get("custom_css_locations", []))

    # Custom CSS is a major violation
    if tailwind_result.get("has_custom_css", False):
        # Each custom CSS violation is worth -15 points (very严重)
        css_deduction = custom_css_count * 15.0
        deductions["custom_css_violations"] = css_deduction
    else:
        # Perfect Tailwind-only compliance - small bonus
        deductions["tailwind_only_bonus"] = -5.0

    total_deduction = sum(deductions.values())
    final_score = max(0.0, min(100.0, base_score - total_deduction))

    rationale = f"Tailwind: {custom_css_count} custom CSS violations"

    return {
        "score": final_score,
        "deductions": deductions,
        "rationale": rationale,
    }


def calculate_accessibility_score(accessibility_result: dict[str, Any]) -> dict[str, Any]:
    """
    Calculate accessibility (WCAG AA) score (0-100).

    Args:
        accessibility_result: Result from validate_accessibility_comprehensive()

    Returns:
        Dict with:
        - score: float (0-100)
        - deductions: dict with breakdown
        - rationale: str
    """
    base_score = 100.0
    deductions = {}

    # Deduct for issues (more严重 than warnings)
    issue_count = accessibility_result.get("issue_count", 0)
    issue_deduction = issue_count * DEDUCTIONS["error"]  # -5 per issue
    deductions["accessibility_issues"] = issue_deduction

    # Deduct for warnings
    warning_count = accessibility_result.get("warning_count", 0)
    warning_deduction = warning_count * DEDUCTIONS["warning"]  # -1 per warning
    deductions["accessibility_warnings"] = warning_deduction

    # Additional penalties for specific violations
    if not accessibility_result.get("contrast_valid", True):
        deductions["contrast_violations"] = 10.0

    if not accessibility_result.get("touch_targets_valid", True):
        deductions["touch_target_violations"] = 8.0

    if not accessibility_result.get("alt_text_valid", True):
        deductions["missing_alt_text"] = 12.0

    if not accessibility_result.get("aria_valid", True):
        deductions["aria_violations"] = 10.0

    if not accessibility_result.get("keyboard_accessible", True):
        deductions["keyboard_issues"] = 15.0

    # Bonus for full WCAG AA compliance
    if accessibility_result.get("wcag_aa_compliant", False):
        deductions["wcag_aa_bonus"] = -5.0

    total_deduction = sum(deductions.values())
    final_score = max(0.0, min(100.0, base_score - total_deduction))

    rationale = (
        f"Accessibility: {issue_count} issues, {warning_count} warnings, "
        f"WCAG AA: {'✓' if accessibility_result.get('wcag_aa_compliant') else '✗'}"
    )

    return {
        "score": final_score,
        "deductions": deductions,
        "rationale": rationale,
    }


def calculate_quality_score(
    syntax_result: dict[str, Any],
    typescript_result: dict[str, Any],
    tailwind_result: dict[str, Any],
    accessibility_result: dict[str, Any],
) -> dict[str, Any]:
    """
    Calculate comprehensive quality score (0-100) from all validation results.

    Scoring breakdown:
    - Syntax: 20%
    - TypeScript: 20%
    - Tailwind: 20%
    - Accessibility: 40%

    Target: 90/100 minimum for acceptance.

    Args:
        syntax_result: Result from validate_syntax()
        typescript_result: Result from validate_typescript()
        tailwind_result: Result from validate_tailwind_only()
        accessibility_result: Result from validate_accessibility_comprehensive()

    Returns:
        Dict with:
        - overall_score: float (0-100)
        - meets_minimum: bool (>= 90)
        - component_scores: dict with breakdown
        - rationale: str
        - grade: str (A+, A, B, C, D, F)
    """
    logger.info("Calculating comprehensive quality score")

    # Calculate component scores
    syntax_score_data = calculate_syntax_score(syntax_result)
    typescript_score_data = calculate_typescript_score(typescript_result)
    tailwind_score_data = calculate_tailwind_score(tailwind_result)
    accessibility_score_data = calculate_accessibility_score(accessibility_result)

    # Extract scores
    syntax_score = syntax_score_data["score"]
    typescript_score = typescript_score_data["score"]
    tailwind_score = tailwind_score_data["score"]
    accessibility_score = accessibility_score_data["score"]

    # Calculate weighted overall score
    overall_score = (
        syntax_score * WEIGHTS["syntax"]
        + typescript_score * WEIGHTS["typescript"]
        + tailwind_score * WEIGHTS["tailwind"]
        + accessibility_score * WEIGHTS["accessibility"]
    )

    # Determine grade
    grade = _calculate_grade(overall_score)

    # Check if meets minimum
    meets_minimum = overall_score >= MIN_ACCEPTABLE_SCORE

    # Build rationale
    rationale = (
        f"Overall: {overall_score:.1f}/100 (Grade: {grade})\n"
        f"├─ Syntax: {syntax_score:.1f}/100 (20% weight) - {syntax_score_data['rationale']}\n"
        f"├─ TypeScript: {typescript_score:.1f}/100 (20% weight) - {typescript_score_data['rationale']}\n"
        f"├─ Tailwind: {tailwind_score:.1f}/100 (20% weight) - {tailwind_score_data['rationale']}\n"
        f"└─ Accessibility: {accessibility_score:.1f}/100 (40% weight) - {accessibility_score_data['rationale']}\n"
    )

    if not meets_minimum:
        rationale += f"\n⚠️  Does not meet minimum quality standard (90/100 required)"
    else:
        rationale += f"\n✓ Meets minimum quality standard (90/100)"

    result = {
        "overall_score": round(overall_score, 1),
        "meets_minimum": meets_minimum,
        "grade": grade,
        "component_scores": {
            "syntax": round(syntax_score, 1),
            "typescript": round(typescript_score, 1),
            "tailwind": round(tailwind_score, 1),
            "accessibility": round(accessibility_score, 1),
        },
        "component_weights": WEIGHTS,
        "detailed_breakdown": {
            "syntax": syntax_score_data,
            "typescript": typescript_score_data,
            "tailwind": tailwind_score_data,
            "accessibility": accessibility_score_data,
        },
        "rationale": rationale,
    }

    logger.info(
        "Quality score calculation complete",
        overall_score=overall_score,
        grade=grade,
        meets_minimum=meets_minimum,
    )

    return result


def _calculate_grade(score: float) -> str:
    """
    Calculate letter grade from score.

    Args:
        score: Quality score (0-100)

    Returns:
        Letter grade (A+, A, A-, B+, B, B-, C+, C, C-, D, F)
    """
    if score >= 97:
        return "A+"
    elif score >= 93:
        return "A"
    elif score >= 90:
        return "A-"
    elif score >= 87:
        return "B+"
    elif score >= 83:
        return "B"
    elif score >= 80:
        return "B-"
    elif score >= 77:
        return "C+"
    elif score >= 73:
        return "C"
    elif score >= 70:
        return "C-"
    elif score >= 60:
        return "D"
    else:
        return "F"


__all__ = [
    "calculate_syntax_score",
    "calculate_typescript_score",
    "calculate_tailwind_score",
    "calculate_accessibility_score",
    "calculate_quality_score",
    "MIN_ACCEPTABLE_SCORE",
    "WEIGHTS",
]
