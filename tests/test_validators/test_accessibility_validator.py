"""
Unit tests for accessibility_validator module.

Tests WCAG 2.1 Level AA compliance validation.
"""

import pytest

from src.validators.accessibility_validator import (
    validate_color_contrast,
    validate_touch_targets,
    validate_alt_text,
    validate_aria_labels,
    validate_semantic_html,
    validate_keyboard_navigation,
    validate_accessibility_comprehensive,
)


# ============================================================================
# Color Contrast Tests
# ============================================================================


def test_validate_color_contrast_passing():
    """Test color contrast validation with good contrast."""
    code = """
    <div className="bg-white text-gray-900">
        <h1 className="text-black">Title</h1>
        <p className="text-gray-800">Body text</p>
    </div>
    """

    result = validate_color_contrast(code)

    assert result["valid"] is True
    assert len(result["contrast_issues"]) == 0


def test_validate_color_contrast_low_contrast():
    """Test detection of low contrast (light gray on white)."""
    code = """
    <div className="bg-white text-gray-200">
        Low contrast text
    </div>
    """

    result = validate_color_contrast(code)

    assert result["valid"] is False
    assert len(result["contrast_issues"]) > 0
    assert "low contrast" in result["contrast_issues"][0].lower()


def test_validate_color_contrast_similar_colors():
    """Test detection of similar background and text colors."""
    code = """
    <div className="bg-blue-500 text-blue-600">
        Similar colors
    </div>
    """

    result = validate_color_contrast(code)

    # Should have warning about similar colors
    assert len(result["warnings"]) > 0
    assert any("similar colors" in w.lower() for w in result["warnings"])


def test_validate_color_contrast_disabled_states():
    """Test warning for disabled states."""
    code = """
    <button className="disabled:text-gray-400">
        Disabled button
    </button>
    """

    result = validate_color_contrast(code)

    assert any("disabled" in w.lower() for w in result["warnings"])


def test_validate_color_contrast_placeholder():
    """Test warning for placeholder text."""
    code = """
    <input type="text" className="placeholder:text-gray-400" />
    """

    result = validate_color_contrast(code)

    assert any("placeholder" in w.lower() for w in result["warnings"])


# ============================================================================
# Touch Target Tests
# ============================================================================


def test_validate_touch_targets_passing():
    """Test touch target validation with adequate sizes."""
    code = """
    <button className="w-12 h-12 p-4">
        Button
    </button>
    """

    result = validate_touch_targets(code)

    assert result["valid"] is True
    assert len(result["violations"]) == 0


def test_validate_touch_targets_small_width():
    """Test detection of small width (less than 44px)."""
    code = """
    <button className="w-6 h-12">
        Too narrow
    </button>
    """

    result = validate_touch_targets(code)

    assert len(result["warnings"]) > 0
    assert any("small width" in w.lower() for w in result["warnings"])


def test_validate_touch_targets_small_height():
    """Test detection of small height (less than 44px)."""
    code = """
    <button className="w-12 h-6">
        Too short
    </button>
    """

    result = validate_touch_targets(code)

    assert len(result["warnings"]) > 0
    assert any("small height" in w.lower() for w in result["warnings"])


def test_validate_touch_targets_icon_only_button():
    """Test warning for icon-only buttons."""
    code = """
    <button>
        🔍
    </button>
    """

    result = validate_touch_targets(code)

    assert len(result["warnings"]) > 0
    assert any("icon-only" in w.lower() for w in result["warnings"])


def test_validate_touch_targets_small_text_links():
    """Test warning for small text links."""
    code = """
    <a href="#" className="text-xs">
        Small link
    </a>
    """

    result = validate_touch_targets(code)

    assert len(result["warnings"]) > 0
    assert any("small text link" in w.lower() for w in result["warnings"])


def test_validate_touch_targets_minimal_padding():
    """Test violation for interactive elements with minimal padding."""
    code = """
    <button className="p-0">
        No padding button
    </button>
    """

    result = validate_touch_targets(code)

    assert result["valid"] is False
    assert len(result["violations"]) > 0
    assert any("minimal padding" in v.lower() for v in result["violations"])


# ============================================================================
# Alt Text Tests
# ============================================================================


def test_validate_alt_text_passing():
    """Test alt text validation with proper alt attributes."""
    code = """
    <img src="logo.png" alt="Company Logo" />
    <img src="photo.jpg" alt="Team photo from 2024 conference" />
    """

    result = validate_alt_text(code)

    assert result["valid"] is True
    assert len(result["missing_alt"]) == 0


def test_validate_alt_text_missing():
    """Test detection of missing alt attributes."""
    code = """
    <img src="image.png" />
    """

    result = validate_alt_text(code)

    assert result["valid"] is False
    assert len(result["missing_alt"]) == 1
    assert "image.png" in result["missing_alt"][0]


def test_validate_alt_text_empty():
    """Test detection of empty alt text (decorative images)."""
    code = """
    <img src="decorative.svg" alt="" />
    """

    result = validate_alt_text(code)

    # Empty alt is valid for decorative images
    assert result["valid"] is True
    assert len(result["empty_alt"]) == 1


def test_validate_alt_text_background_images():
    """Test warning for background images."""
    code = """
    <div style="background-image: url('hero.jpg')">
        Content
    </div>
    """

    result = validate_alt_text(code)

    assert len(result["warnings"]) > 0
    assert any("background image" in w.lower() for w in result["warnings"])


def test_validate_alt_text_svg_without_title():
    """Test warning for SVG without title or aria-label."""
    code = """
    <svg width="100" height="100">
        <circle cx="50" cy="50" r="40" />
    </svg>
    """

    result = validate_alt_text(code)

    assert len(result["warnings"]) > 0
    assert any("svg" in w.lower() for w in result["warnings"])


def test_validate_alt_text_svg_with_title():
    """Test SVG with proper title tag."""
    code = """
    <svg width="100" height="100">
        <title>Circle Icon</title>
        <circle cx="50" cy="50" r="40" />
    </svg>
    """

    result = validate_alt_text(code)

    # Should not warn about this SVG
    assert result["valid"] is True


# ============================================================================
# ARIA Labels Tests
# ============================================================================


def test_validate_aria_labels_passing():
    """Test ARIA validation with proper labels."""
    code = """
    <button aria-label="Search">
        🔍
    </button>
    <input id="email" type="email" />
    <label for="email">Email</label>
    """

    result = validate_aria_labels(code)

    assert result["valid"] is True
    assert len(result["missing_labels"]) == 0


def test_validate_aria_labels_icon_button_missing():
    """Test detection of icon-only button without aria-label."""
    code = """
    <button>
        📱
    </button>
    """

    result = validate_aria_labels(code)

    assert result["valid"] is False
    assert len(result["missing_labels"]) > 0
    assert any("icon-only button" in label.lower() for label in result["missing_labels"])


def test_validate_aria_labels_clickable_div():
    """Test warning for clickable div without role."""
    code = """
    <div onClick={handleClick}>
        Click me
    </div>
    """

    result = validate_aria_labels(code)

    assert len(result["warnings"]) > 0
    assert any("clickable div" in w.lower() for w in result["warnings"])


def test_validate_aria_labels_input_without_label():
    """Test detection of input without label."""
    code = """
    <input id="username" type="text" />
    """

    result = validate_aria_labels(code)

    assert result["valid"] is False
    assert len(result["missing_labels"]) > 0
    assert "username" in result["missing_labels"][0]


def test_validate_aria_labels_input_with_aria_label():
    """Test input with aria-label is valid."""
    code = """
    <input type="text" aria-label="Username" />
    """

    result = validate_aria_labels(code)

    assert result["valid"] is True


def test_validate_aria_labels_invalid_role():
    """Test detection of invalid ARIA role."""
    code = """
    <div role="superbutton">
        Invalid role
    </div>
    """

    result = validate_aria_labels(code)

    assert result["valid"] is False
    assert len(result["invalid_aria"]) > 0
    assert "superbutton" in result["invalid_aria"][0]


def test_validate_aria_labels_valid_roles():
    """Test acceptance of valid ARIA roles."""
    code = """
    <div role="button" tabindex="0">Button</div>
    <nav role="navigation">Nav</nav>
    <main role="main">Main content</main>
    """

    result = validate_aria_labels(code)

    assert len(result["invalid_aria"]) == 0


def test_validate_aria_labels_aria_hidden_trap():
    """Test warning for aria-hidden on focusable element."""
    code = """
    <button aria-hidden="true" tabindex="0">
        Hidden but focusable
    </button>
    """

    result = validate_aria_labels(code)

    assert len(result["warnings"]) > 0
    assert any("keyboard trap" in w.lower() for w in result["warnings"])


# ============================================================================
# Semantic HTML Tests
# ============================================================================


def test_validate_semantic_html_passing():
    """Test semantic HTML validation with proper structure."""
    code = """
    <header>
        <h1>Main Title</h1>
        <nav>Navigation</nav>
    </header>
    <main>
        <article>
            <h2>Section Title</h2>
            <p>Content</p>
        </article>
    </main>
    <footer>Footer</footer>
    """

    result = validate_semantic_html(code)

    assert result["valid"] is True
    assert len(result["hierarchy_issues"]) == 0
    assert len(result["semantic_issues"]) == 0


def test_validate_semantic_html_no_h1():
    """Test warning for missing h1."""
    code = """
    <div>
        <h2>Subtitle</h2>
        <p>Content</p>
    </div>
    """

    result = validate_semantic_html(code)

    assert len(result["warnings"]) > 0
    assert any("no <h1>" in w.lower() for w in result["warnings"])


def test_validate_semantic_html_multiple_h1():
    """Test warning for multiple h1 tags."""
    code = """
    <h1>First Title</h1>
    <h1>Second Title</h1>
    """

    result = validate_semantic_html(code)

    assert len(result["warnings"]) > 0
    assert any("multiple <h1>" in w.lower() for w in result["warnings"])


def test_validate_semantic_html_heading_skip():
    """Test detection of heading hierarchy skip."""
    code = """
    <h1>Main Title</h1>
    <h3>Skipped h2</h3>
    """

    result = validate_semantic_html(code)

    assert result["valid"] is False
    assert len(result["hierarchy_issues"]) > 0
    assert "h1" in result["hierarchy_issues"][0]
    assert "h3" in result["hierarchy_issues"][0]


def test_validate_semantic_html_no_main():
    """Test warning for missing main landmark."""
    code = """
    <div>
        <div>Long content that should be in main...</div>
        <div>More content...</div>
        <div>Even more content to make it non-trivial...</div>
        <div>And more...</div>
        <div>And more...</div>
    </div>
    """

    result = validate_semantic_html(code)

    assert len(result["warnings"]) > 0
    assert any("<main>" in w for w in result["warnings"])


def test_validate_semantic_html_div_soup():
    """Test detection of excessive divs without semantic elements."""
    code = """
    <div>
        <div><div><div><div><div><div><div><div><div><div><div>
            Nested divs
        </div></div></div></div></div></div></div></div></div></div></div>
    </div>
    """

    result = validate_semantic_html(code)

    assert result["valid"] is False
    assert len(result["semantic_issues"]) > 0
    assert any("excessive <div>" in issue.lower() for issue in result["semantic_issues"])


def test_validate_semantic_html_li_outside_list():
    """Test detection of li outside ul/ol."""
    code = """
    <div>
        <li>Item 1</li>
        <li>Item 2</li>
    </div>
    """

    result = validate_semantic_html(code)

    assert result["valid"] is False
    assert any("<li>" in issue for issue in result["semantic_issues"])


def test_validate_semantic_html_table_without_headers():
    """Test warning for table without th headers."""
    code = """
    <table>
        <tr><td>Cell 1</td><td>Cell 2</td></tr>
    </table>
    """

    result = validate_semantic_html(code)

    assert len(result["warnings"]) > 0
    assert any("table" in w.lower() for w in result["warnings"])


# ============================================================================
# Keyboard Navigation Tests
# ============================================================================


def test_validate_keyboard_navigation_passing():
    """Test keyboard navigation with proper implementation."""
    code = """
    <button className="focus:ring-2">
        Accessible Button
    </button>
    <a href="#" className="focus:border-blue-500">
        Accessible Link
    </a>
    """

    result = validate_keyboard_navigation(code)

    assert result["valid"] is True
    assert len(result["issues"]) == 0


def test_validate_keyboard_navigation_negative_tabindex():
    """Test warning for negative tabindex."""
    code = """
    <button tabindex="-1">
        Removed from tab order
    </button>
    """

    result = validate_keyboard_navigation(code)

    assert len(result["warnings"]) > 0
    assert any("negative tabindex" in w.lower() for w in result["warnings"])


def test_validate_keyboard_navigation_high_tabindex():
    """Test issue for high tabindex values."""
    code = """
    <button tabindex="999">
        High tabindex
    </button>
    """

    result = validate_keyboard_navigation(code)

    assert result["valid"] is False
    assert len(result["issues"]) > 0
    assert any("high tabindex" in issue.lower() for issue in result["issues"])


def test_validate_keyboard_navigation_outline_none_no_replacement():
    """Test issue for focus:outline-none without replacement."""
    code = """
    <button className="focus:outline-none">
        No focus indicator
    </button>
    """

    result = validate_keyboard_navigation(code)

    assert result["valid"] is False
    assert len(result["issues"]) > 0
    assert any("focus outline disabled" in issue.lower() for issue in result["issues"])


def test_validate_keyboard_navigation_outline_none_with_replacement():
    """Test outline-none is valid when alternative focus indicator exists."""
    code = """
    <button className="focus:outline-none focus:ring-2">
        Has ring as focus indicator
    </button>
    """

    result = validate_keyboard_navigation(code)

    # Should be valid (has focus:ring as replacement)
    assert result["valid"] is True


def test_validate_keyboard_navigation_clickable_div_not_accessible():
    """Test issue for clickable div without keyboard accessibility."""
    code = """
    <div onClick={handleClick}>
        Click me
    </div>
    """

    result = validate_keyboard_navigation(code)

    assert result["valid"] is False
    assert len(result["issues"]) > 0
    assert any("not keyboard accessible" in issue.lower() for issue in result["issues"])


def test_validate_keyboard_navigation_missing_keyboard_handlers():
    """Test warning for click handlers without keyboard handlers."""
    code = """
    <div onClick={handleClick}>
        Click only
    </div>
    """

    result = validate_keyboard_navigation(code)

    assert len(result["warnings"]) > 0
    assert any("keyboard handler" in w.lower() for w in result["warnings"])


def test_validate_keyboard_navigation_with_keyboard_handlers():
    """Test that keyboard handlers suppress warnings."""
    code = """
    <div onClick={handleClick} onKeyDown={handleKeyDown}>
        Accessible
    </div>
    """

    result = validate_keyboard_navigation(code)

    # Should not warn about missing keyboard handlers
    assert not any("keyboard handler" in w.lower() for w in result.get("warnings", []))


# ============================================================================
# Comprehensive Validation Tests
# ============================================================================


@pytest.mark.asyncio
async def test_validate_accessibility_comprehensive_all_passing():
    """Test comprehensive validation with fully accessible code."""
    code = """
    <header>
        <h1>Main Title</h1>
        <nav role="navigation">
            <a href="#" className="w-12 h-12 focus:ring-2">Link</a>
        </nav>
    </header>
    <main>
        <article>
            <h2>Section Title</h2>
            <img src="photo.jpg" alt="Descriptive alt text" />
            <form>
                <label for="email">Email</label>
                <input id="email" type="email" className="focus:border-blue-500" />
                <button type="submit" className="w-12 h-12 bg-blue-600 text-white">
                    Submit
                </button>
            </form>
        </article>
    </main>
    """

    result = await validate_accessibility_comprehensive(code)

    assert result["wcag_aa_compliant"] is True
    assert result["contrast_valid"] is True
    assert result["touch_targets_valid"] is True
    assert result["alt_text_valid"] is True
    assert result["aria_valid"] is True
    assert result["semantic_html_valid"] is True
    assert result["keyboard_accessible"] is True
    assert result["issue_count"] == 0


@pytest.mark.asyncio
async def test_validate_accessibility_comprehensive_multiple_issues():
    """Test comprehensive validation with multiple accessibility issues."""
    code = """
    <div className="bg-white text-gray-200">
        <img src="logo.png" />
        <button className="p-0">📱</button>
        <div onClick={handleClick}>Click me</div>
        <h3>Skipped h1 and h2</h3>
        <button className="focus:outline-none">No focus indicator</button>
    </div>
    """

    result = await validate_accessibility_comprehensive(code)

    assert result["wcag_aa_compliant"] is False
    assert result["contrast_valid"] is False  # Light gray on white
    assert result["touch_targets_valid"] is False  # Minimal padding
    assert result["alt_text_valid"] is False  # Missing alt
    assert result["aria_valid"] is False  # Icon button without label
    assert result["semantic_html_valid"] is False  # Heading skip
    assert result["keyboard_accessible"] is False  # Multiple issues
    assert result["issue_count"] > 0
    assert result["warning_count"] > 0


@pytest.mark.asyncio
async def test_validate_accessibility_comprehensive_with_design_system():
    """Test comprehensive validation with Design System provided."""
    code = """
    <div className="bg-primary-500 text-white">
        Content
    </div>
    """

    design_system = {
        "colors": {
            "primary": ["#3B82F6", "#2563EB", "#1D4ED8"],
        }
    }

    result = await validate_accessibility_comprehensive(code, design_system)

    # Should still validate (Design System parameter accepted)
    assert "wcag_aa_compliant" in result


@pytest.mark.asyncio
async def test_validate_accessibility_comprehensive_warnings_only():
    """Test comprehensive validation with warnings but no critical issues."""
    code = """
    <header>
        <h1>Title</h1>
        <nav>
            <a href="#" className="text-sm">Small link</a>
        </nav>
    </header>
    <main>
        <img src="decorative.svg" alt="" />
        <p className="placeholder:text-gray-400">Content</p>
    </main>
    """

    result = await validate_accessibility_comprehensive(code)

    # Should pass (warnings don't fail WCAG compliance)
    assert result["wcag_aa_compliant"] is True
    assert result["issue_count"] == 0
    assert result["warning_count"] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
