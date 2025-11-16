"""
Keyword detection for library discovery triggers.

Detects when user feedback mentions specific features or components
that might benefit from open-source library recommendations.
"""

import re
from typing import Any

from src.utils.logger import get_logger

logger = get_logger(__name__)

# Keyword patterns mapped to library categories
LIBRARY_KEYWORDS = {
    "ui_components": [
        # Data display
        "table",
        "data table",
        "grid",
        "data grid",
        "list",
        "virtual list",
        "infinite scroll",
        # Forms
        "form",
        "input",
        "select",
        "dropdown",
        "combobox",
        "autocomplete",
        "date picker",
        "time picker",
        "datetime picker",
        "calendar",
        "color picker",
        "file upload",
        "drag and drop",
        # UI elements
        "modal",
        "dialog",
        "popup",
        "tooltip",
        "popover",
        "toast",
        "notification",
        "alert",
        "snackbar",
        "drawer",
        "sidebar",
        "navbar",
        "menu",
        "tabs",
        "accordion",
        "carousel",
        "slider",
        "progress bar",
        "spinner",
        "loading",
        "skeleton",
        "badge",
        "chip",
        "tag",
    ],
    "authentication": [
        "login",
        "sign in",
        "sign up",
        "register",
        "authentication",
        "auth",
        "oauth",
        "social login",
        "google login",
        "facebook login",
        "jwt",
        "session",
        "password",
        "forgot password",
        "reset password",
        "two factor",
        "2fa",
        "mfa",
    ],
    "icons": [
        "icon",
        "icons",
        "svg",
        "emoji",
        "symbol",
    ],
    "charts": [
        "chart",
        "graph",
        "visualization",
        "plot",
        "bar chart",
        "line chart",
        "pie chart",
        "scatter plot",
        "heatmap",
        "dashboard",
    ],
    "animation": [
        "animation",
        "animate",
        "transition",
        "motion",
        "fade",
        "slide",
        "bounce",
        "reveal",
    ],
    "state_management": [
        "state",
        "state management",
        "global state",
        "context",
        "store",
        "redux",
        "zustand",
    ],
    "routing": [
        "routing",
        "router",
        "navigation",
        "route",
        "link",
    ],
    "forms_validation": [
        "validation",
        "form validation",
        "validator",
        "schema",
        "yup",
        "zod",
    ],
    "date_time": [
        "date",
        "time",
        "datetime",
        "timezone",
        "moment",
        "dayjs",
    ],
}


def detect_library_keywords(user_feedback: str) -> list[dict[str, Any]]:
    """
    Detect library-related keywords in user feedback.

    Args:
        user_feedback: User's feedback or refinement request

    Returns:
        List of detected keyword matches with:
        - keyword: str (matched keyword)
        - category: str (library category)
        - query: str (search query to use)
    """
    if not user_feedback:
        return []

    user_feedback_lower = user_feedback.lower()
    matches = []
    seen_categories = set()  # Avoid duplicate categories

    # Check each category's keywords
    for category, keywords in LIBRARY_KEYWORDS.items():
        for keyword in keywords:
            # Use word boundary matching to avoid partial matches
            pattern = r"\b" + re.escape(keyword) + r"\b"
            if re.search(pattern, user_feedback_lower):
                # Found a match
                if category not in seen_categories:
                    matches.append(
                        {
                            "keyword": keyword,
                            "category": category,
                            "query": keyword,  # Use the keyword as search query
                        }
                    )
                    seen_categories.add(category)
                    logger.debug(
                        f"Keyword detected",
                        keyword=keyword,
                        category=category,
                        feedback=user_feedback,
                    )

    if matches:
        logger.info(
            f"Library keywords detected",
            count=len(matches),
            categories=[m["category"] for m in matches],
        )

    return matches


def should_trigger_library_search(user_feedback: str) -> bool:
    """
    Determine if library search should be triggered based on feedback.

    Args:
        user_feedback: User's feedback

    Returns:
        True if library search should be triggered
    """
    if not user_feedback:
        return False

    # Don't trigger on approval keywords
    approval_keywords = ["approve", "approved", "looks good", "next", "continue", "skip"]
    if user_feedback.lower().strip() in approval_keywords:
        return False

    # Detect keywords
    matches = detect_library_keywords(user_feedback)
    return len(matches) > 0


def extract_search_query(user_feedback: str, default_category: str = "ui_components") -> str:
    """
    Extract the best search query from user feedback.

    Args:
        user_feedback: User's feedback
        default_category: Default category if no keywords detected

    Returns:
        Search query string
    """
    matches = detect_library_keywords(user_feedback)

    if not matches:
        # No keywords detected, use feedback as-is
        return user_feedback.strip()

    # Use the first detected keyword as the query
    return matches[0]["query"]


def get_category_from_feedback(user_feedback: str) -> str:
    """
    Get the library category from user feedback.

    Args:
        user_feedback: User's feedback

    Returns:
        Category string (e.g., "ui_components", "authentication")
    """
    matches = detect_library_keywords(user_feedback)

    if not matches:
        return "ui_components"  # Default category

    return matches[0]["category"]


__all__ = [
    "detect_library_keywords",
    "should_trigger_library_search",
    "extract_search_query",
    "get_category_from_feedback",
    "LIBRARY_KEYWORDS",
]
