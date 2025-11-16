"""
Code validation system for uploaded designs.

Validates syntax, TypeScript compliance, and Tailwind CSS usage.
"""

import re
from typing import Any

from src.utils.logger import get_logger

logger = get_logger(__name__)


def validate_syntax(code: str, file_extension: str = ".tsx") -> dict[str, Any]:
    """
    Validate basic syntax of code.

    Args:
        code: Source code string
        file_extension: File extension (.tsx, .ts, .jsx, .js)

    Returns:
        Dict with:
        - valid: bool
        - errors: list[str]
        - warnings: list[str]
    """
    errors = []
    warnings = []

    # Check for basic syntax issues
    if not code.strip():
        errors.append("Code is empty")
        return {"valid": False, "errors": errors, "warnings": warnings}

    # Check for unmatched brackets
    brackets = {"(": ")", "[": "]", "{": "}"}
    stack = []
    for i, char in enumerate(code):
        if char in brackets:
            stack.append(char)
        elif char in brackets.values():
            if not stack:
                errors.append(f"Unmatched closing bracket '{char}' at position {i}")
            else:
                expected = brackets[stack.pop()]
                if char != expected:
                    errors.append(f"Mismatched bracket: expected '{expected}', got '{char}' at position {i}")

    if stack:
        errors.append(f"Unclosed brackets: {stack}")

    # Check for common syntax errors
    if "import " in code:
        import_lines = [line for line in code.split("\n") if line.strip().startswith("import ")]
        for line in import_lines:
            if not line.strip().endswith(";") and not line.strip().endswith('"') and not line.strip().endswith("'"):
                warnings.append(f"Import statement might be missing semicolon: {line[:50]}")

    # TypeScript specific checks
    if file_extension in [".ts", ".tsx"]:
        if "any" in code:
            warnings.append("Usage of 'any' type detected - consider using more specific types")

    is_valid = len(errors) == 0

    logger.info(
        "Syntax validation complete",
        valid=is_valid,
        error_count=len(errors),
        warning_count=len(warnings),
    )

    return {
        "valid": is_valid,
        "errors": errors,
        "warnings": warnings,
    }


def validate_typescript(code: str) -> dict[str, Any]:
    """
    Validate TypeScript compliance.

    Args:
        code: Source code string

    Returns:
        Dict with:
        - valid: bool
        - has_types: bool
        - type_coverage: float (0-1)
        - errors: list[str]
        - warnings: list[str]
    """
    errors = []
    warnings = []

    # Check for TypeScript presence
    has_interface = "interface " in code
    has_type = "type " in code or ": " in code  # Type annotations
    has_generic = "<" in code and ">" in code

    has_types = has_interface or has_type

    # Estimate type coverage (rough heuristic)
    function_count = len(re.findall(r"\bfunction\s+\w+|const\s+\w+\s*=\s*\(", code))
    typed_function_count = len(re.findall(r":\s*\w+(\[\])?(\s*=>|\s*\{)", code))

    type_coverage = typed_function_count / function_count if function_count > 0 else 0.0

    # Validate TypeScript usage
    if not has_types:
        warnings.append("No TypeScript types detected - code may be plain JavaScript")

    if type_coverage < 0.5:
        warnings.append(f"Low type coverage ({type_coverage:.1%}) - consider adding more type annotations")

    # Check for 'any' abuse
    any_count = len(re.findall(r":\s*any\b", code))
    if any_count > 5:
        warnings.append(f"Excessive use of 'any' type ({any_count} occurrences)")

    is_valid = len(errors) == 0

    logger.info(
        "TypeScript validation complete",
        valid=is_valid,
        has_types=has_types,
        type_coverage=f"{type_coverage:.1%}",
    )

    return {
        "valid": is_valid,
        "has_types": has_types,
        "type_coverage": type_coverage,
        "errors": errors,
        "warnings": warnings,
    }


def validate_tailwind_only(code: str) -> dict[str, Any]:
    """
    Validate that ONLY Tailwind CSS is used (no custom CSS).

    Args:
        code: Source code string

    Returns:
        Dict with:
        - valid: bool
        - has_custom_css: bool
        - custom_css_locations: list[str]
        - errors: list[str]
    """
    errors = []
    custom_css_locations = []

    # Check for custom CSS in various forms

    # 1. Inline style objects
    style_objects = re.findall(r"style\s*=\s*\{([^}]+)\}", code)
    if style_objects:
        for i, match in enumerate(style_objects):
            custom_css_locations.append(f"Inline style object #{i + 1}: {match[:50]}...")
            errors.append(f"Custom CSS detected in inline style (use Tailwind classes instead)")

    # 2. styled-components or similar CSS-in-JS
    if "styled." in code or "styled(" in code:
        custom_css_locations.append("styled-components usage detected")
        errors.append("styled-components detected - use Tailwind classes only")

    # 3. CSS files imported
    css_imports = re.findall(r"import\s+['\"].*\.css['\"]", code)
    if css_imports:
        for css_import in css_imports:
            custom_css_locations.append(f"CSS import: {css_import}")
            errors.append(f"Custom CSS file imported: {css_import}")

    # 4. <style> tags (in case of HTML/JSX)
    if "<style" in code:
        custom_css_locations.append("<style> tag detected")
        errors.append("<style> tags detected - use Tailwind classes only")

    has_custom_css = len(custom_css_locations) > 0
    is_valid = not has_custom_css

    logger.info(
        "Tailwind validation complete",
        valid=is_valid,
        has_custom_css=has_custom_css,
        violations=len(custom_css_locations),
    )

    return {
        "valid": is_valid,
        "has_custom_css": has_custom_css,
        "custom_css_locations": custom_css_locations,
        "errors": errors,
    }


async def validate_code_comprehensive(
    code: str,
    file_extension: str = ".tsx",
) -> dict[str, Any]:
    """
    Run all code validators comprehensively.

    Args:
        code: Source code string
        file_extension: File extension

    Returns:
        Dict with all validation results
    """
    logger.info("Running comprehensive code validation")

    # Run all validators
    syntax_result = validate_syntax(code, file_extension)
    typescript_result = validate_typescript(code)
    tailwind_result = validate_tailwind_only(code)

    # Aggregate results
    all_valid = (
        syntax_result["valid"]
        and typescript_result["valid"]
        and tailwind_result["valid"]
    )

    all_errors = (
        syntax_result["errors"]
        + typescript_result["errors"]
        + tailwind_result["errors"]
    )

    all_warnings = (
        syntax_result.get("warnings", [])
        + typescript_result.get("warnings", [])
    )

    result = {
        "syntax_valid": syntax_result["valid"],
        "typescript_valid": typescript_result["valid"],
        "tailwind_only": tailwind_result["valid"],
        "all_valid": all_valid,
        "type_coverage": typescript_result["type_coverage"],
        "has_custom_css": tailwind_result["has_custom_css"],
        "errors": all_errors,
        "warnings": all_warnings,
    }

    logger.info(
        "Comprehensive validation complete",
        all_valid=all_valid,
        total_errors=len(all_errors),
        total_warnings=len(all_warnings),
    )

    return result


__all__ = [
    "validate_syntax",
    "validate_typescript",
    "validate_tailwind_only",
    "validate_code_comprehensive",
]
