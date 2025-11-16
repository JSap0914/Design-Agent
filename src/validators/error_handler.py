"""
Error handling for code validation system.

Provides custom exceptions, error recovery strategies, and user-friendly error messages
for validation failures.
"""

from enum import Enum
from typing import Any

from src.utils.logger import get_logger

logger = get_logger(__name__)


# ============================================================================
# Custom Exception Classes
# ============================================================================


class ValidationError(Exception):
    """Base exception for all validation errors."""

    def __init__(self, message: str, code: str = "VALIDATION_ERROR", recoverable: bool = False):
        super().__init__(message)
        self.message = message
        self.code = code
        self.recoverable = recoverable


class SyntaxValidationError(ValidationError):
    """Raised when syntax validation fails."""

    def __init__(self, message: str, errors: list[str]):
        super().__init__(message, code="SYNTAX_ERROR", recoverable=True)
        self.errors = errors


class TypeScriptValidationError(ValidationError):
    """Raised when TypeScript validation fails."""

    def __init__(self, message: str, type_coverage: float, errors: list[str]):
        super().__init__(message, code="TYPESCRIPT_ERROR", recoverable=True)
        self.type_coverage = type_coverage
        self.errors = errors


class TailwindValidationError(ValidationError):
    """Raised when custom CSS is detected (Tailwind-only requirement)."""

    def __init__(self, message: str, css_locations: list[str]):
        super().__init__(message, code="CUSTOM_CSS_ERROR", recoverable=True)
        self.css_locations = css_locations


class AccessibilityValidationError(ValidationError):
    """Raised when accessibility (WCAG AA) validation fails."""

    def __init__(self, message: str, wcag_issues: list[str]):
        super().__init__(message, code="ACCESSIBILITY_ERROR", recoverable=True)
        self.wcag_issues = wcag_issues


class QualityScoreError(ValidationError):
    """Raised when quality score is below minimum threshold."""

    def __init__(self, message: str, score: float, minimum: float):
        super().__init__(message, code="QUALITY_SCORE_ERROR", recoverable=True)
        self.score = score
        self.minimum = minimum


class CodeUploadError(ValidationError):
    """Raised when code upload fails or is invalid."""

    def __init__(self, message: str):
        super().__init__(message, code="UPLOAD_ERROR", recoverable=False)


class DatabaseStorageError(ValidationError):
    """Raised when database storage fails."""

    def __init__(self, message: str):
        super().__init__(message, code="STORAGE_ERROR", recoverable=True)


# ============================================================================
# Error Severity Levels
# ============================================================================


class ErrorSeverity(Enum):
    """Error severity levels for validation issues."""

    CRITICAL = "critical"  # Blocking errors (syntax, missing code)
    HIGH = "high"  # Major issues (WCAG violations, custom CSS)
    MEDIUM = "medium"  # Moderate issues (low type coverage)
    LOW = "low"  # Minor issues (warnings, suggestions)


# ============================================================================
# Error Recovery Strategies
# ============================================================================


class ErrorRecoveryStrategy:
    """Strategies for recovering from validation errors."""

    @staticmethod
    def can_retry(error: ValidationError, retry_count: int, max_retries: int = 3) -> bool:
        """
        Determine if error is recoverable and retry count is within limit.

        Args:
            error: The validation error
            retry_count: Current retry count
            max_retries: Maximum allowed retries

        Returns:
            True if can retry, False otherwise
        """
        return error.recoverable and retry_count < max_retries

    @staticmethod
    def should_ask_user(error: ValidationError) -> bool:
        """
        Determine if user should be asked for manual intervention.

        Args:
            error: The validation error

        Returns:
            True if user input needed, False otherwise
        """
        # Ask user for manual intervention on these error types
        return isinstance(
            error,
            (
                TailwindValidationError,
                AccessibilityValidationError,
                QualityScoreError,
            ),
        )

    @staticmethod
    def get_user_prompt(error: ValidationError) -> str:
        """
        Get user-friendly prompt for error recovery.

        Args:
            error: The validation error

        Returns:
            User-friendly error message with recovery options
        """
        if isinstance(error, SyntaxValidationError):
            return (
                f"❌ Syntax Error\n\n"
                f"Your code has {len(error.errors)} syntax errors:\n"
                + "\n".join(f"  • {e}" for e in error.errors[:5])
                + ("\n  ... and more" if len(error.errors) > 5 else "")
                + "\n\nPlease fix the syntax errors and re-upload your code."
            )

        elif isinstance(error, TypeScriptValidationError):
            return (
                f"❌ TypeScript Compliance Issue\n\n"
                f"Type coverage: {error.type_coverage:.0%}\n"
                f"Issues found: {len(error.errors)}\n\n"
                + "\n".join(f"  • {e}" for e in error.errors[:5])
                + "\n\nPlease add TypeScript types to your code and re-upload."
            )

        elif isinstance(error, TailwindValidationError):
            return (
                f"❌ Custom CSS Detected\n\n"
                f"Found {len(error.css_locations)} instances of custom CSS.\n"
                f"Only Tailwind CSS classes are allowed.\n\n"
                + "\n".join(f"  • {loc}" for loc in error.css_locations[:5])
                + "\n\nPlease replace custom CSS with Tailwind classes and re-upload."
            )

        elif isinstance(error, AccessibilityValidationError):
            return (
                f"❌ Accessibility (WCAG AA) Issues\n\n"
                f"Found {len(error.wcag_issues)} accessibility violations:\n"
                + "\n".join(f"  • {issue}" for issue in error.wcag_issues[:5])
                + ("\n  ... and more" if len(error.wcag_issues) > 5 else "")
                + "\n\nPlease fix accessibility issues and re-upload."
            )

        elif isinstance(error, QualityScoreError):
            return (
                f"❌ Quality Score Too Low\n\n"
                f"Score: {error.score:.1f}/100\n"
                f"Minimum required: {error.minimum:.1f}/100\n\n"
                f"Your code does not meet the minimum quality standard.\n\n"
                f"Options:\n"
                f"  1. Fix the issues and re-upload\n"
                f'  2. Type "override" to proceed anyway (not recommended)\n'
                f'  3. Type "skip" to skip validation and go to document generation'
            )

        elif isinstance(error, CodeUploadError):
            return (
                f"❌ Code Upload Error\n\n"
                f"{error.message}\n\n"
                f"Please upload valid code files and try again."
            )

        else:
            return f"❌ Error: {error.message}\n\nPlease review and try again."


# ============================================================================
# Error Aggregation
# ============================================================================


class ValidationErrorReport:
    """Aggregates and categorizes validation errors."""

    def __init__(self):
        self.errors: list[tuple[ErrorSeverity, str]] = []
        self.warnings: list[str] = []

    def add_error(self, severity: ErrorSeverity, message: str):
        """Add an error to the report."""
        self.errors.append((severity, message))

    def add_warning(self, message: str):
        """Add a warning to the report."""
        self.warnings.append(message)

    def has_critical_errors(self) -> bool:
        """Check if report has any critical errors."""
        return any(severity == ErrorSeverity.CRITICAL for severity, _ in self.errors)

    def has_high_severity_errors(self) -> bool:
        """Check if report has high or critical errors."""
        return any(
            severity in [ErrorSeverity.CRITICAL, ErrorSeverity.HIGH] for severity, _ in self.errors
        )

    def get_summary(self) -> dict[str, Any]:
        """Get summary of all errors and warnings."""
        error_counts = {
            "critical": sum(1 for s, _ in self.errors if s == ErrorSeverity.CRITICAL),
            "high": sum(1 for s, _ in self.errors if s == ErrorSeverity.HIGH),
            "medium": sum(1 for s, _ in self.errors if s == ErrorSeverity.MEDIUM),
            "low": sum(1 for s, _ in self.errors if s == ErrorSeverity.LOW),
        }

        return {
            "total_errors": len(self.errors),
            "total_warnings": len(self.warnings),
            "error_counts_by_severity": error_counts,
            "has_blocking_errors": self.has_critical_errors(),
            "errors": [{"severity": s.value, "message": m} for s, m in self.errors],
            "warnings": self.warnings,
        }

    def format_user_message(self) -> str:
        """Format user-friendly error message."""
        if not self.errors and not self.warnings:
            return "✅ No issues found"

        message = []

        if self.errors:
            critical = [m for s, m in self.errors if s == ErrorSeverity.CRITICAL]
            high = [m for s, m in self.errors if s == ErrorSeverity.HIGH]
            medium = [m for s, m in self.errors if s == ErrorSeverity.MEDIUM]
            low = [m for s, m in self.errors if s == ErrorSeverity.LOW]

            if critical:
                message.append(f"❌ Critical Errors ({len(critical)}):")
                message.extend(f"  • {e}" for e in critical)

            if high:
                message.append(f"\n⚠️  High Priority ({len(high)}):")
                message.extend(f"  • {e}" for e in high)

            if medium:
                message.append(f"\n⚠️  Medium Priority ({len(medium)}):")
                message.extend(f"  • {e}" for e in medium[:3])
                if len(medium) > 3:
                    message.append(f"  ... and {len(medium) - 3} more")

            if low:
                message.append(f"\n💡 Low Priority ({len(low)}):")
                message.extend(f"  • {e}" for e in low[:3])
                if len(low) > 3:
                    message.append(f"  ... and {len(low) - 3} more")

        if self.warnings:
            message.append(f"\n💡 Warnings ({len(self.warnings)}):")
            message.extend(f"  • {w}" for w in self.warnings[:5])
            if len(self.warnings) > 5:
                message.append(f"  ... and {len(self.warnings) - 5} more")

        return "\n".join(message)


# ============================================================================
# Error Handling Helpers
# ============================================================================


def handle_validation_exception(
    exception: Exception,
    job_id: str,
    retry_count: int = 0,
) -> dict[str, Any]:
    """
    Handle validation exceptions and return error state update.

    Args:
        exception: The exception that occurred
        job_id: Job identifier
        retry_count: Current retry count

    Returns:
        State update dict with error information
    """
    logger.error(
        "Validation exception occurred",
        job_id=job_id,
        exception_type=type(exception).__name__,
        error=str(exception),
        retry_count=retry_count,
    )

    # Convert to ValidationError if not already
    if isinstance(exception, ValidationError):
        error = exception
    else:
        error = ValidationError(str(exception), code="UNKNOWN_ERROR", recoverable=False)

    # Determine recovery strategy
    can_retry = ErrorRecoveryStrategy.can_retry(error, retry_count)
    should_ask_user = ErrorRecoveryStrategy.should_ask_user(error)
    user_prompt = ErrorRecoveryStrategy.get_user_prompt(error)

    return {
        "error_occurred": True,
        "error_type": error.code,
        "error_message": error.message,
        "error_recoverable": error.recoverable,
        "can_retry": can_retry,
        "should_ask_user": should_ask_user,
        "user_prompt": user_prompt,
        "retry_count": retry_count + 1 if can_retry else retry_count,
        "should_retry": can_retry,
    }


def create_error_from_validation_results(
    validation_results: dict[str, Any],
) -> ValidationError | None:
    """
    Create appropriate ValidationError from validation results.

    Args:
        validation_results: Results from validate_code_comprehensive

    Returns:
        ValidationError if validation failed, None otherwise
    """
    # Check quality score
    if not validation_results.get("meets_minimum", True):
        overall_score = validation_results.get("overall_score", 0)
        return QualityScoreError(
            message=f"Quality score {overall_score:.1f}/100 is below minimum threshold",
            score=overall_score,
            minimum=90.0,
        )

    code_val = validation_results.get("code_validation", {})
    accessibility_val = validation_results.get("accessibility_validation", {})

    # Check for custom CSS
    if code_val.get("has_custom_css"):
        return TailwindValidationError(
            message="Custom CSS detected - only Tailwind CSS allowed",
            css_locations=[e for e in code_val.get("errors", []) if "css" in e.lower()],
        )

    # Check for accessibility issues
    if not accessibility_val.get("wcag_aa_compliant"):
        return AccessibilityValidationError(
            message="Code does not meet WCAG AA accessibility standards",
            wcag_issues=accessibility_val.get("issues", []),
        )

    # Check for syntax errors
    if not code_val.get("syntax_valid"):
        return SyntaxValidationError(
            message="Syntax errors detected",
            errors=[e for e in code_val.get("errors", []) if "syntax" in e.lower()],
        )

    # Check for TypeScript issues
    if not code_val.get("typescript_valid") or code_val.get("type_coverage", 0) < 0.5:
        return TypeScriptValidationError(
            message="TypeScript compliance issues detected",
            type_coverage=code_val.get("type_coverage", 0),
            errors=[e for e in code_val.get("errors", []) if "type" in e.lower()],
        )

    return None


__all__ = [
    "ValidationError",
    "SyntaxValidationError",
    "TypeScriptValidationError",
    "TailwindValidationError",
    "AccessibilityValidationError",
    "QualityScoreError",
    "CodeUploadError",
    "DatabaseStorageError",
    "ErrorSeverity",
    "ErrorRecoveryStrategy",
    "ValidationErrorReport",
    "handle_validation_exception",
    "create_error_from_validation_results",
]
