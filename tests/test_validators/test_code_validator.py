"""
Unit tests for code_validator module.

Tests syntax, TypeScript, and Tailwind CSS validation.
"""

import pytest

from src.validators.code_validator import (
    validate_syntax,
    validate_typescript,
    validate_tailwind_only,
    validate_code_comprehensive,
)


# ============================================================================
# Syntax Validation Tests
# ============================================================================


def test_validate_syntax_passing():
    """Test syntax validation with valid code."""
    code = """
    const MyComponent = () => {
        return <div>Hello World</div>;
    };
    """

    result = validate_syntax(code, ".tsx")

    assert result["valid"] is True
    assert len(result["errors"]) == 0


def test_validate_syntax_empty_code():
    """Test syntax validation with empty code."""
    code = "   "

    result = validate_syntax(code)

    assert result["valid"] is False
    assert len(result["errors"]) == 1
    assert "empty" in result["errors"][0].lower()


def test_validate_syntax_unmatched_opening_bracket():
    """Test detection of unmatched opening bracket."""
    code = """
    function test() {
        console.log("missing closing brace");
    """

    result = validate_syntax(code)

    assert result["valid"] is False
    assert len(result["errors"]) > 0
    assert any("unclosed" in err.lower() for err in result["errors"])


def test_validate_syntax_unmatched_closing_bracket():
    """Test detection of unmatched closing bracket."""
    code = """
    function test() {
        console.log("extra closing");
    }}
    """

    result = validate_syntax(code)

    assert result["valid"] is False
    assert len(result["errors"]) > 0


def test_validate_syntax_mismatched_brackets():
    """Test detection of mismatched bracket types."""
    code = """
    const arr = [1, 2, 3};
    """

    result = validate_syntax(code)

    assert result["valid"] is False
    assert any("mismatched" in err.lower() for err in result["errors"])


def test_validate_syntax_import_semicolon_warning():
    """Test warning for imports without semicolons."""
    code = """
    import React from 'react'
    import { useState } from 'react'
    """

    result = validate_syntax(code, ".tsx")

    assert result["valid"] is True  # Warnings don't fail validation
    assert len(result["warnings"]) > 0
    assert any("semicolon" in w.lower() for w in result["warnings"])


def test_validate_syntax_typescript_any_warning():
    """Test warning for 'any' type usage in TypeScript."""
    code = """
    const data: any = fetchData();
    """

    result = validate_syntax(code, ".ts")

    assert len(result["warnings"]) > 0
    assert any("any" in w.lower() for w in result["warnings"])


def test_validate_syntax_javascript_file():
    """Test syntax validation for JavaScript files."""
    code = """
    function greet(name) {
        return `Hello, ${name}!`;
    }
    """

    result = validate_syntax(code, ".js")

    assert result["valid"] is True


# ============================================================================
# TypeScript Validation Tests
# ============================================================================


def test_validate_typescript_with_types():
    """Test TypeScript validation with proper type annotations."""
    code = """
    interface User {
        id: number;
        name: string;
    }

    const getUser = (id: number): User => {
        return { id, name: "John" };
    };
    """

    result = validate_typescript(code)

    assert result["valid"] is True
    assert result["has_types"] is True
    assert result["type_coverage"] > 0


def test_validate_typescript_no_types():
    """Test warning for code without TypeScript types."""
    code = """
    const add = (a, b) => {
        return a + b;
    };
    """

    result = validate_typescript(code)

    assert result["has_types"] is False
    assert len(result["warnings"]) > 0
    assert any("no typescript types" in w.lower() for w in result["warnings"])


def test_validate_typescript_low_type_coverage():
    """Test warning for low type coverage."""
    code = """
    const foo = (a, b) => a + b;
    const bar = (x: number): number => x * 2;
    const baz = (y, z) => y - z;
    """

    result = validate_typescript(code)

    assert result["type_coverage"] < 0.5
    assert any("low type coverage" in w.lower() for w in result["warnings"])


def test_validate_typescript_high_type_coverage():
    """Test TypeScript with high type coverage."""
    code = """
    const add = (a: number, b: number): number => a + b;
    const multiply = (x: number, y: number): number => x * y;
    const divide = (a: number, b: number): number => a / b;
    """

    result = validate_typescript(code)

    assert result["type_coverage"] >= 0.5
    assert result["has_types"] is True


def test_validate_typescript_excessive_any():
    """Test warning for excessive use of 'any' type."""
    code = """
    const data: any = {};
    const config: any = {};
    const state: any = {};
    const props: any = {};
    const context: any = {};
    const options: any = {};
    """

    result = validate_typescript(code)

    assert len(result["warnings"]) > 0
    assert any("excessive" in w.lower() and "any" in w.lower() for w in result["warnings"])


def test_validate_typescript_with_interface():
    """Test TypeScript detection via interface."""
    code = """
    interface Props {
        title: string;
        onClick: () => void;
    }
    """

    result = validate_typescript(code)

    assert result["has_types"] is True


def test_validate_typescript_with_type_alias():
    """Test TypeScript detection via type alias."""
    code = """
    type User = {
        id: number;
        name: string;
    };
    """

    result = validate_typescript(code)

    assert result["has_types"] is True


def test_validate_typescript_with_generics():
    """Test TypeScript detection via generics."""
    code = """
    function identity<T>(arg: T): T {
        return arg;
    }
    """

    result = validate_typescript(code)

    assert result["has_types"] is True


# ============================================================================
# Tailwind CSS Validation Tests
# ============================================================================


def test_validate_tailwind_only_passing():
    """Test Tailwind validation with only Tailwind classes."""
    code = """
    <div className="bg-blue-500 text-white p-4 rounded-lg shadow-md">
        <h1 className="text-2xl font-bold">Title</h1>
        <p className="text-sm text-gray-600">Description</p>
    </div>
    """

    result = validate_tailwind_only(code)

    assert result["valid"] is True
    assert result["has_custom_css"] is False
    assert len(result["custom_css_locations"]) == 0


def test_validate_tailwind_only_inline_style():
    """Test detection of inline style objects."""
    code = """
    <div style={{ backgroundColor: 'red', padding: '10px' }}>
        Custom styles
    </div>
    """

    result = validate_tailwind_only(code)

    assert result["valid"] is False
    assert result["has_custom_css"] is True
    assert len(result["custom_css_locations"]) > 0
    assert len(result["errors"]) > 0
    assert any("inline style" in err.lower() for err in result["errors"])


def test_validate_tailwind_only_styled_components():
    """Test detection of styled-components."""
    code = """
    import styled from 'styled-components';

    const Button = styled.button`
        background-color: blue;
        padding: 10px;
    `;
    """

    result = validate_tailwind_only(code)

    assert result["valid"] is False
    assert result["has_custom_css"] is True
    assert any("styled-components" in loc.lower() for loc in result["custom_css_locations"])


def test_validate_tailwind_only_css_import():
    """Test detection of CSS file imports."""
    code = """
    import React from 'react';
    import './styles.css';
    import './components/Button.css';
    """

    result = validate_tailwind_only(code)

    assert result["valid"] is False
    assert result["has_custom_css"] is True
    assert len(result["errors"]) >= 2
    assert any("css import" in err.lower() or "css file" in err.lower() for err in result["errors"])


def test_validate_tailwind_only_style_tag():
    """Test detection of <style> tags."""
    code = """
    <div>
        <style>
            .custom-class {
                color: red;
            }
        </style>
        <p className="custom-class">Text</p>
    </div>
    """

    result = validate_tailwind_only(code)

    assert result["valid"] is False
    assert result["has_custom_css"] is True
    assert any("<style>" in loc.lower() for loc in result["custom_css_locations"])


def test_validate_tailwind_only_multiple_violations():
    """Test detection of multiple CSS violations."""
    code = """
    import './styles.css';
    import styled from 'styled-components';

    const Container = styled.div`background: blue;`;

    <div style={{ margin: '10px' }}>
        <style>.custom { color: red; }</style>
    </div>
    """

    result = validate_tailwind_only(code)

    assert result["valid"] is False
    assert len(result["custom_css_locations"]) >= 3
    assert len(result["errors"]) >= 3


def test_validate_tailwind_only_no_false_positives():
    """Test that Tailwind classes don't trigger false positives."""
    code = """
    <div className="hover:bg-blue-700 focus:ring-2 active:scale-95">
        <button className="transition-colors duration-200">
            Click me
        </button>
    </div>
    """

    result = validate_tailwind_only(code)

    assert result["valid"] is True


# ============================================================================
# Comprehensive Validation Tests
# ============================================================================


@pytest.mark.asyncio
async def test_validate_code_comprehensive_all_passing():
    """Test comprehensive validation with fully compliant code."""
    code = """
    interface ButtonProps {
        label: string;
        onClick: () => void;
    }

    const Button = ({ label, onClick }: ButtonProps) => {
        return (
            <button
                onClick={onClick}
                className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
            >
                {label}
            </button>
        );
    };
    """

    result = await validate_code_comprehensive(code, ".tsx")

    assert result["all_valid"] is True
    assert result["syntax_valid"] is True
    assert result["typescript_valid"] is True
    assert result["tailwind_only"] is True
    assert len(result["errors"]) == 0


@pytest.mark.asyncio
async def test_validate_code_comprehensive_syntax_error():
    """Test comprehensive validation with syntax errors."""
    code = """
    const broken = () => {
        return <div>Unclosed div;
    """

    result = await validate_code_comprehensive(code, ".tsx")

    assert result["all_valid"] is False
    assert result["syntax_valid"] is False
    assert len(result["errors"]) > 0


@pytest.mark.asyncio
async def test_validate_code_comprehensive_no_typescript():
    """Test comprehensive validation with no TypeScript."""
    code = """
    const MyComponent = () => {
        return <div className="p-4">No types</div>;
    };
    """

    result = await validate_code_comprehensive(code, ".tsx")

    # Should be valid (TypeScript is optional but warned)
    assert result["syntax_valid"] is True
    assert result["tailwind_only"] is True
    assert result["type_coverage"] < 0.5
    assert len(result["warnings"]) > 0


@pytest.mark.asyncio
async def test_validate_code_comprehensive_custom_css():
    """Test comprehensive validation with custom CSS."""
    code = """
    interface Props {
        title: string;
    }

    const Component = ({ title }: Props) => {
        return <div style={{ padding: '10px' }}>{title}</div>;
    };
    """

    result = await validate_code_comprehensive(code, ".tsx")

    assert result["all_valid"] is False
    assert result["tailwind_only"] is False
    assert result["has_custom_css"] is True
    assert len(result["errors"]) > 0


@pytest.mark.asyncio
async def test_validate_code_comprehensive_multiple_errors():
    """Test comprehensive validation with multiple errors."""
    code = """
    import './styles.css';

    const broken = () => {
        return <div style={{ color: 'red' }}>Unclosed;
    """

    result = await validate_code_comprehensive(code, ".tsx")

    assert result["all_valid"] is False
    assert result["syntax_valid"] is False
    assert result["tailwind_only"] is False
    assert len(result["errors"]) >= 2  # Syntax + Tailwind violations


@pytest.mark.asyncio
async def test_validate_code_comprehensive_javascript_file():
    """Test comprehensive validation for JavaScript file."""
    code = """
    const add = (a, b) => {
        return a + b;
    };

    export default add;
    """

    result = await validate_code_comprehensive(code, ".js")

    # Should be valid (JavaScript doesn't require TypeScript)
    assert result["syntax_valid"] is True
    assert result["tailwind_only"] is True


@pytest.mark.asyncio
async def test_validate_code_comprehensive_warnings_only():
    """Test comprehensive validation with warnings but no errors."""
    code = """
    const MyComponent = () => {
        const data: any = fetchData();
        return <div className="p-4">{data}</div>;
    };
    """

    result = await validate_code_comprehensive(code, ".tsx")

    # Should be valid (warnings don't fail validation)
    assert result["all_valid"] is True
    assert len(result["errors"]) == 0
    assert len(result["warnings"]) > 0


@pytest.mark.asyncio
async def test_validate_code_comprehensive_real_world_example():
    """Test comprehensive validation with realistic React component."""
    code = """
    import React, { useState } from 'react';

    interface TodoProps {
        id: number;
        text: string;
        completed: boolean;
    }

    const TodoItem: React.FC<TodoProps> = ({ id, text, completed }) => {
        const [isCompleted, setIsCompleted] = useState(completed);

        const handleToggle = () => {
            setIsCompleted(!isCompleted);
        };

        return (
            <div className="flex items-center gap-2 p-2 border-b hover:bg-gray-50">
                <input
                    type="checkbox"
                    checked={isCompleted}
                    onChange={handleToggle}
                    className="w-4 h-4"
                />
                <span className={isCompleted ? 'line-through text-gray-500' : ''}>
                    {text}
                </span>
            </div>
        );
    };

    export default TodoItem;
    """

    result = await validate_code_comprehensive(code, ".tsx")

    assert result["all_valid"] is True
    assert result["syntax_valid"] is True
    assert result["typescript_valid"] is True
    assert result["tailwind_only"] is True
    assert result["type_coverage"] > 0.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
