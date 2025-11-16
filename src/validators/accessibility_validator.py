"""
Accessibility validation for WCAG 2.1 Level AA compliance.

Validates uploaded designs for:
- Color contrast ratios (4.5:1 minimum)
- Touch target sizes (48x48px minimum)
- Alt text on images
- ARIA labels
- Semantic HTML usage
- Keyboard navigation support
"""

import re
from typing import Any

from src.utils.logger import get_logger

logger = get_logger(__name__)


def validate_color_contrast(code: str, design_system: dict[str, Any] | None = None) -> dict[str, Any]:
    """
    Validate color contrast ratios meet WCAG AA standards.

    WCAG AA Requirements:
    - Normal text: 4.5:1 minimum contrast ratio
    - Large text (18pt+/14pt+ bold): 3:1 minimum
    - UI components and graphics: 3:1 minimum

    Args:
        code: Source code string
        design_system: Optional Design System with color definitions

    Returns:
        Dict with:
        - valid: bool
        - contrast_issues: list[str]
        - warnings: list[str]
    """
    warnings = []
    contrast_issues = []

    # Check for common low-contrast patterns
    # Light gray on white backgrounds
    light_gray_patterns = [
        r"text-gray-[123]00",  # Tailwind very light grays
        r"bg-white.*text-gray-[123]00",
        r"#[Ff]{6}.*#[EeFf]{6}",  # White-ish on white-ish
    ]

    for pattern in light_gray_patterns:
        matches = re.findall(pattern, code)
        if matches:
            contrast_issues.append(
                f"Potential low contrast detected: {pattern} (may not meet 4.5:1 ratio)"
            )

    # Check for text on colored backgrounds without sufficient contrast
    if "bg-" in code and "text-" in code:
        # Look for cases where background and text colors might be too similar
        bg_color_classes = re.findall(r"bg-(gray|blue|green|red|yellow|purple|pink|indigo)-(\d+)", code)
        text_color_classes = re.findall(r"text-(gray|blue|green|red|yellow|purple|pink|indigo)-(\d+)", code)

        # Check if background and text are the same hue with close lightness
        for bg_color, bg_shade in bg_color_classes:
            for text_color, text_shade in text_color_classes:
                if bg_color == text_color:
                    bg_shade_int = int(bg_shade)
                    text_shade_int = int(text_shade)
                    if abs(bg_shade_int - text_shade_int) < 400:  # Too close
                        warnings.append(
                            f"Similar colors detected: bg-{bg_color}-{bg_shade} with text-{text_color}-{text_shade} "
                            f"may not have sufficient contrast"
                        )

    # Check for insufficient contrast on interactive elements
    if "disabled:" in code:
        warnings.append(
            "Disabled states detected - ensure disabled elements still meet 3:1 contrast for perception"
        )

    # Placeholder text contrast
    if "placeholder:" in code or "placeholder-" in code:
        warnings.append(
            "Placeholder text detected - ensure placeholders meet 4.5:1 contrast or are supplemented with labels"
        )

    is_valid = len(contrast_issues) == 0

    logger.info(
        "Color contrast validation complete",
        valid=is_valid,
        issues=len(contrast_issues),
        warnings=len(warnings),
    )

    return {
        "valid": is_valid,
        "contrast_issues": contrast_issues,
        "warnings": warnings,
    }


def validate_touch_targets(code: str) -> dict[str, Any]:
    """
    Validate touch target sizes meet WCAG AA standards.

    WCAG AA Requirement:
    - Minimum 44x44 CSS pixels for interactive elements
    - Best practice: 48x48px minimum

    Args:
        code: Source code string

    Returns:
        Dict with:
        - valid: bool
        - violations: list[str]
        - warnings: list[str]
    """
    violations = []
    warnings = []

    # Check for small button/link patterns
    small_size_patterns = [
        r"(w-\d+|h-\d+)",  # Tailwind width/height classes
        r"(p-\d+|px-\d+|py-\d+)",  # Padding classes
    ]

    # Extract all width/height classes
    width_classes = re.findall(r"\bw-(\d+)\b", code)
    height_classes = re.findall(r"\bh-(\d+)\b", code)

    # Check for very small interactive elements (Tailwind uses 0.25rem = 4px scale)
    # w-8 = 2rem = 32px, w-10 = 2.5rem = 40px, w-12 = 3rem = 48px
    for width in width_classes:
        if int(width) < 10:  # Less than 40px (10 * 4px)
            warnings.append(
                f"Small width detected: w-{width} (may be less than 44px minimum for touch targets)"
            )

    for height in height_classes:
        if int(height) < 10:  # Less than 40px
            warnings.append(
                f"Small height detected: h-{height} (may be less than 44px minimum for touch targets)"
            )

    # Check for icon-only buttons without sufficient padding
    if re.search(r"<button[^>]*>[\s\n]*[📱🔍👤⚙️✕❌][\s\n]*</button>", code):
        warnings.append(
            "Icon-only buttons detected - ensure minimum 44x44px touch target with padding"
        )

    # Check for small text links
    if re.search(r"text-(xs|sm)", code) and re.search(r"<a[\s\S]*?</a>", code):
        warnings.append(
            "Small text links detected - ensure clickable area is at least 44x44px (use padding)"
        )

    # Check for insufficient padding on interactive elements
    small_padding = re.findall(r"\b(p-[01]|px-[01]|py-[01])\b", code)
    if small_padding and ("button" in code.lower() or "<a" in code):
        violations.append(
            f"Interactive elements with minimal padding detected: {set(small_padding)} "
            f"may not meet 44x44px touch target requirement"
        )

    is_valid = len(violations) == 0

    logger.info(
        "Touch target validation complete",
        valid=is_valid,
        violations=len(violations),
        warnings=len(warnings),
    )

    return {
        "valid": is_valid,
        "violations": violations,
        "warnings": warnings,
    }


def validate_alt_text(code: str) -> dict[str, Any]:
    """
    Validate images have appropriate alt text.

    WCAG AA Requirement:
    - All <img> elements must have alt attribute
    - Alt text must be descriptive (not empty for meaningful images)
    - Decorative images should have alt=""

    Args:
        code: Source code string

    Returns:
        Dict with:
        - valid: bool
        - missing_alt: list[str]
        - empty_alt: list[str]
        - warnings: list[str]
    """
    missing_alt = []
    empty_alt = []
    warnings = []

    # Find all <img> tags
    img_tags = re.findall(r"<img[^>]*>", code, re.IGNORECASE)

    for img_tag in img_tags:
        # Check if alt attribute exists
        if not re.search(r'\balt\s*=', img_tag, re.IGNORECASE):
            src_match = re.search(r'src\s*=\s*["\']([^"\']+)["\']', img_tag)
            src = src_match.group(1) if src_match else "unknown"
            missing_alt.append(f"Image missing alt attribute: {src}")
        else:
            # Check if alt is empty
            alt_match = re.search(r'alt\s*=\s*["\']([^"\']*)["\']', img_tag, re.IGNORECASE)
            if alt_match and not alt_match.group(1).strip():
                empty_alt.append(f"Image with empty alt text: {img_tag[:50]}...")

    # Check for background images that might need accessible alternatives
    if "background-image:" in code or "bg-[url(" in code:
        warnings.append(
            "Background images detected - ensure meaningful images have text alternatives"
        )

    # Check for SVG without title/desc
    svg_tags = re.findall(r"<svg[^>]*>[\s\S]*?</svg>", code, re.IGNORECASE)
    for svg_tag in svg_tags:
        if not re.search(r"<title>", svg_tag, re.IGNORECASE) and not re.search(r'aria-label', svg_tag):
            warnings.append(
                "SVG without <title> or aria-label detected - ensure decorative or has accessible name"
            )

    is_valid = len(missing_alt) == 0

    logger.info(
        "Alt text validation complete",
        valid=is_valid,
        missing_alt=len(missing_alt),
        empty_alt=len(empty_alt),
    )

    return {
        "valid": is_valid,
        "missing_alt": missing_alt,
        "empty_alt": empty_alt,
        "warnings": warnings,
    }


def validate_aria_labels(code: str) -> dict[str, Any]:
    """
    Validate ARIA labels and roles are used correctly.

    WCAG AA Requirements:
    - Interactive elements have accessible names
    - ARIA roles are valid and used correctly
    - aria-label or aria-labelledby for icon-only buttons

    Args:
        code: Source code string

    Returns:
        Dict with:
        - valid: bool
        - missing_labels: list[str]
        - invalid_aria: list[str]
        - warnings: list[str]
    """
    missing_labels = []
    invalid_aria = []
    warnings = []

    # Check for icon-only buttons without aria-label
    icon_button_pattern = r"<button[^>]*>[\s\n]*[📱🔍👤⚙️✕❌🏠📧🔔][\s\n]*</button>"
    icon_buttons = re.findall(icon_button_pattern, code)

    for button in icon_buttons:
        if not re.search(r'aria-label\s*=', button) and not re.search(r'aria-labelledby\s*=', button):
            missing_labels.append(f"Icon-only button missing aria-label: {button[:50]}...")

    # Check for custom interactive elements without role
    clickable_divs = re.findall(r"<div[^>]*onClick[^>]*>", code, re.IGNORECASE)
    for div in clickable_divs:
        if not re.search(r'\brole\s*=\s*["\']button["\']', div):
            warnings.append(
                f"Clickable div without role=\"button\": {div[:50]}... (use <button> instead)"
            )

    # Check for form inputs without labels
    input_tags = re.findall(r"<input[^>]*>", code, re.IGNORECASE)
    for input_tag in input_tags:
        # Check if input has id and corresponding label, or aria-label
        has_id = re.search(r'\bid\s*=\s*["\']([^"\']+)["\']', input_tag)
        has_aria_label = re.search(r'\baria-label\s*=', input_tag)
        has_aria_labelledby = re.search(r'\baria-labelledby\s*=', input_tag)

        if not (has_aria_label or has_aria_labelledby):
            if has_id:
                input_id = has_id.group(1)
                # Check if there's a corresponding <label for="...">
                if not re.search(rf'<label[^>]*for\s*=\s*["\']?{input_id}["\']?', code, re.IGNORECASE):
                    missing_labels.append(f"Input field without label: id=\"{input_id}\"")
            else:
                missing_labels.append(f"Input field without id, label, or aria-label: {input_tag[:50]}...")

    # Check for valid ARIA roles
    aria_roles = re.findall(r'\brole\s*=\s*["\']([^"\']+)["\']', code)
    valid_roles = {
        "button", "link", "navigation", "main", "complementary", "banner", "contentinfo",
        "search", "form", "article", "region", "alert", "status", "dialog", "menu",
        "menuitem", "tab", "tabpanel", "tablist", "listbox", "option", "checkbox",
        "radio", "switch", "slider", "spinbutton", "progressbar", "img"
    }

    for role in aria_roles:
        if role not in valid_roles:
            invalid_aria.append(f"Invalid or non-standard ARIA role: {role}")

    # Check for aria-hidden on focusable elements
    if re.search(r'aria-hidden\s*=\s*["\']true["\'][^>]*tabindex', code):
        warnings.append(
            "aria-hidden=\"true\" on focusable element detected - creates keyboard trap"
        )

    is_valid = len(missing_labels) == 0 and len(invalid_aria) == 0

    logger.info(
        "ARIA validation complete",
        valid=is_valid,
        missing_labels=len(missing_labels),
        invalid_aria=len(invalid_aria),
    )

    return {
        "valid": is_valid,
        "missing_labels": missing_labels,
        "invalid_aria": invalid_aria,
        "warnings": warnings,
    }


def validate_semantic_html(code: str) -> dict[str, Any]:
    """
    Validate semantic HTML usage.

    WCAG AA Best Practices:
    - Use semantic elements (<header>, <nav>, <main>, <footer>, <article>, <section>)
    - Proper heading hierarchy (h1 -> h2 -> h3, no skipping)
    - Lists use <ul>/<ol>/<li>
    - Forms use <form>, <label>, <fieldset>

    Args:
        code: Source code string

    Returns:
        Dict with:
        - valid: bool
        - hierarchy_issues: list[str]
        - semantic_issues: list[str]
        - warnings: list[str]
    """
    hierarchy_issues = []
    semantic_issues = []
    warnings = []

    # Check heading hierarchy
    headings = re.findall(r"<h([1-6])", code, re.IGNORECASE)
    if headings:
        heading_levels = [int(h) for h in headings]

        # Check for h1 (should have exactly one)
        h1_count = heading_levels.count(1)
        if h1_count == 0:
            warnings.append("No <h1> heading found - page should have one main heading")
        elif h1_count > 1:
            warnings.append(f"Multiple <h1> headings found ({h1_count}) - should have only one per page")

        # Check for skipped heading levels
        for i in range(len(heading_levels) - 1):
            current = heading_levels[i]
            next_level = heading_levels[i + 1]
            if next_level > current + 1:
                hierarchy_issues.append(
                    f"Heading hierarchy skip detected: <h{current}> to <h{next_level}> (should increment by 1)"
                )

    # Check for semantic landmarks
    has_main = bool(re.search(r"<main[\s>]", code, re.IGNORECASE))
    has_nav = bool(re.search(r"<nav[\s>]", code, re.IGNORECASE))
    has_header = bool(re.search(r"<header[\s>]", code, re.IGNORECASE))
    has_footer = bool(re.search(r"<footer[\s>]", code, re.IGNORECASE))

    if not has_main and len(code) > 500:  # Only warn for non-trivial components
        warnings.append("No <main> landmark found - consider using semantic HTML5 elements")

    # Check for div soup (excessive divs without semantic elements)
    div_count = len(re.findall(r"<div[\s>]", code, re.IGNORECASE))
    semantic_count = (
        len(re.findall(r"<(main|nav|header|footer|article|section|aside)[\s>]", code, re.IGNORECASE))
    )

    if div_count > 10 and semantic_count == 0:
        semantic_issues.append(
            f"Excessive <div> usage ({div_count}) without semantic HTML5 elements - "
            f"use <main>, <nav>, <header>, <footer>, <article>, <section>"
        )

    # Check for list items outside lists
    if re.search(r"<li[\s>]", code, re.IGNORECASE):
        # Ensure <li> is inside <ul> or <ol>
        if not re.search(r"<[uo]l[\s>][\s\S]*?<li", code, re.IGNORECASE):
            semantic_issues.append("<li> elements found outside <ul> or <ol>")

    # Check for tables used for layout (deprecated)
    if re.search(r"<table", code, re.IGNORECASE):
        if not re.search(r"<th[\s>]", code, re.IGNORECASE):
            warnings.append(
                "Table without <th> headers detected - ensure table is for data, not layout"
            )

    is_valid = len(hierarchy_issues) == 0 and len(semantic_issues) == 0

    logger.info(
        "Semantic HTML validation complete",
        valid=is_valid,
        hierarchy_issues=len(hierarchy_issues),
        semantic_issues=len(semantic_issues),
    )

    return {
        "valid": is_valid,
        "hierarchy_issues": hierarchy_issues,
        "semantic_issues": semantic_issues,
        "warnings": warnings,
    }


def validate_keyboard_navigation(code: str) -> dict[str, Any]:
    """
    Validate keyboard navigation support.

    WCAG AA Requirements:
    - All interactive elements are keyboard accessible
    - No keyboard traps
    - Focus indicators are visible
    - Logical tab order

    Args:
        code: Source code string

    Returns:
        Dict with:
        - valid: bool
        - issues: list[str]
        - warnings: list[str]
    """
    issues = []
    warnings = []

    # Check for negative tabindex (removes from tab order)
    negative_tabindex = re.findall(r'tabindex\s*=\s*["\']?-\d+', code)
    if negative_tabindex:
        warnings.append(
            f"Negative tabindex detected ({len(negative_tabindex)} instances) - "
            f"may make elements inaccessible to keyboard users"
        )

    # Check for very high tabindex values (disrupts natural tab order)
    high_tabindex = re.findall(r'tabindex\s*=\s*["\']?([1-9]\d{2,})', code)
    if high_tabindex:
        issues.append(
            f"High tabindex values detected: {set(high_tabindex)} - "
            f"avoid manual tab order, use natural DOM order"
        )

    # Check for disabled focus styles
    if re.search(r"focus:outline-none", code) or re.search(r"outline:\s*none", code):
        focus_replacement = (
            re.search(r"focus:ring", code) or
            re.search(r"focus:border", code) or
            re.search(r"focus:shadow", code)
        )
        if not focus_replacement:
            issues.append(
                "Focus outline disabled without alternative focus indicator - "
                "keyboard users need visible focus"
            )

    # Check for clickable elements that aren't keyboard accessible
    onclick_divs = re.findall(r"<div[^>]*onClick[^>]*>", code)
    for div in onclick_divs:
        if not re.search(r'\btabindex\s*=', div) and not re.search(r'\brole\s*=\s*["\']button["\']', div):
            issues.append(
                f"Clickable div without tabindex or role=\"button\": {div[:50]}... "
                f"(not keyboard accessible - use <button> instead)"
            )

    # Check for onKeyPress/onKeyDown handlers
    has_click_handlers = bool(re.search(r"onClick", code))
    has_keyboard_handlers = bool(re.search(r"(onKeyDown|onKeyPress|onKeyUp)", code))

    if has_click_handlers and not has_keyboard_handlers:
        warnings.append(
            "Click handlers detected without keyboard handlers - "
            "ensure custom interactive elements handle Enter/Space keys"
        )

    is_valid = len(issues) == 0

    logger.info(
        "Keyboard navigation validation complete",
        valid=is_valid,
        issues=len(issues),
        warnings=len(warnings),
    )

    return {
        "valid": is_valid,
        "issues": issues,
        "warnings": warnings,
    }


async def validate_accessibility_comprehensive(
    code: str,
    design_system: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Run all accessibility validators comprehensively.

    Args:
        code: Source code string
        design_system: Optional Design System with color definitions

    Returns:
        Dict with all accessibility validation results
    """
    logger.info("Running comprehensive accessibility validation")

    # Run all validators
    contrast_result = validate_color_contrast(code, design_system)
    touch_result = validate_touch_targets(code)
    alt_result = validate_alt_text(code)
    aria_result = validate_aria_labels(code)
    semantic_result = validate_semantic_html(code)
    keyboard_result = validate_keyboard_navigation(code)

    # Aggregate results
    all_valid = (
        contrast_result["valid"]
        and touch_result["valid"]
        and alt_result["valid"]
        and aria_result["valid"]
        and semantic_result["valid"]
        and keyboard_result["valid"]
    )

    all_issues = (
        contrast_result.get("contrast_issues", [])
        + touch_result.get("violations", [])
        + alt_result.get("missing_alt", [])
        + aria_result.get("missing_labels", [])
        + aria_result.get("invalid_aria", [])
        + semantic_result.get("hierarchy_issues", [])
        + semantic_result.get("semantic_issues", [])
        + keyboard_result.get("issues", [])
    )

    all_warnings = (
        contrast_result.get("warnings", [])
        + touch_result.get("warnings", [])
        + alt_result.get("warnings", [])
        + aria_result.get("warnings", [])
        + semantic_result.get("warnings", [])
        + keyboard_result.get("warnings", [])
    )

    result = {
        "wcag_aa_compliant": all_valid,
        "contrast_valid": contrast_result["valid"],
        "touch_targets_valid": touch_result["valid"],
        "alt_text_valid": alt_result["valid"],
        "aria_valid": aria_result["valid"],
        "semantic_html_valid": semantic_result["valid"],
        "keyboard_accessible": keyboard_result["valid"],
        "issues": all_issues,
        "warnings": all_warnings,
        "issue_count": len(all_issues),
        "warning_count": len(all_warnings),
    }

    logger.info(
        "Comprehensive accessibility validation complete",
        wcag_aa_compliant=all_valid,
        total_issues=len(all_issues),
        total_warnings=len(all_warnings),
    )

    return result


__all__ = [
    "validate_color_contrast",
    "validate_touch_targets",
    "validate_alt_text",
    "validate_aria_labels",
    "validate_semantic_html",
    "validate_keyboard_navigation",
    "validate_accessibility_comprehensive",
]
