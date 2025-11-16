"""
Library selection workflow.

Presents top-ranked library options to users and processes their selections.
"""

from typing import Any

from src.utils.logger import get_logger

logger = get_logger(__name__)


def format_library_option(library: dict[str, Any], rank: int) -> str:
    """
    Format a single library option for display.

    Args:
        library: Library dictionary with metadata
        rank: Display rank (1, 2, 3)

    Returns:
        Formatted string for display
    """
    name = library.get("library_name", "Unknown")
    score = library.get("ranking_score", 0)
    stars = library.get("stars", 0)
    license_type = library.get("license", "Unknown")
    bundle_size = library.get("bundle_size", "Unknown")
    description = library.get("description", "")
    github_url = library.get("github_url", "")
    npm_url = library.get("npm_url", "")

    # Determine source link
    primary_link = github_url or npm_url or ""

    # Format stars
    if stars >= 1000:
        stars_display = f"{stars // 1000}K+"
    else:
        stars_display = str(stars) if stars else "N/A"

    # Recommendation badge
    badge = " ⭐ Recommended" if rank == 1 else ""

    # Build formatted output
    output = f"{rank}. {name}{badge}\n"
    output += f"   📦 Source: {primary_link}\n" if primary_link else ""
    output += f"   ⭐ Stars: {stars_display}\n" if stars else ""
    output += f"   📄 License: {license_type}\n"
    output += f"   📏 Bundle: {bundle_size}\n"
    output += f"   💡 Score: {score}/100\n\n"

    if description:
        # Truncate description to 100 chars
        desc_short = description[:100] + "..." if len(description) > 100 else description
        output += f"   {desc_short}\n\n"

    return output


def present_library_options(libraries: list[dict[str, Any]], query: str, max_options: int = 3) -> str:
    """
    Format library options for presentation to user.

    Args:
        libraries: List of ranked libraries
        query: Original search query
        max_options: Maximum options to show (default: 3)

    Returns:
        Formatted presentation string
    """
    if not libraries:
        return f"🔍 No libraries found for '{query}'. Try a different search or skip."

    # Take top N options
    top_libraries = libraries[:max_options]

    output = f"🔍 Found {len(libraries)} libraries for '{query}'\n\n"
    output += f"✅ Top {len(top_libraries)} options:\n\n"

    for rank, library in enumerate(top_libraries, start=1):
        output += format_library_option(library, rank)

    output += "\nWhich would you like? (1, 2, 3, or 'skip')"

    return output


def process_library_selection(
    user_input: str,
    libraries: list[dict[str, Any]],
    query: str,
) -> dict[str, Any]:
    """
    Process user's library selection.

    Args:
        user_input: User's choice (1, 2, 3, skip, etc.)
        libraries: List of ranked libraries
        query: Original search query

    Returns:
        Selection result dictionary with:
        - selected: bool (True if library selected)
        - library: dict or None (selected library)
        - message: str (confirmation message)
        - install_command: str or None (npm install command)
    """
    user_input_clean = user_input.strip().lower()

    # Handle skip
    if user_input_clean in ["skip", "no", "none", "pass"]:
        logger.info(f"User skipped library selection for '{query}'")
        return {
            "selected": False,
            "library": None,
            "message": "✅ Skipped library selection. Continuing...",
            "install_command": None,
        }

    # Handle numeric selection
    try:
        choice = int(user_input_clean)

        if choice < 1 or choice > len(libraries):
            return {
                "selected": False,
                "library": None,
                "message": f"❌ Invalid choice. Please select 1-{len(libraries)} or 'skip'.",
                "install_command": None,
            }

        selected_library = libraries[choice - 1]
        library_name = selected_library.get("library_name", "Unknown")
        npm_name = selected_library.get("npm_name") or library_name

        # Generate install command
        install_cmd = f"npm install {npm_name}"

        logger.info(f"User selected library: {library_name}", query=query, choice=choice)

        message = f"✅ {library_name} added!\n"
        message += f"   Installation: {install_cmd}\n"
        message += f"   This library will be included in your documentation."

        return {
            "selected": True,
            "library": selected_library,
            "message": message,
            "install_command": install_cmd,
        }

    except ValueError:
        return {
            "selected": False,
            "library": None,
            "message": f"❌ Invalid input '{user_input}'. Please enter a number (1, 2, 3) or 'skip'.",
            "install_command": None,
        }


def create_library_suggestion_message(query: str, category: str = "ui_components") -> dict[str, Any]:
    """
    Create WebSocket message for library suggestion.

    Args:
        query: Search query
        category: Library category

    Returns:
        WebSocket message dictionary
    """
    return {
        "type": "library_search",
        "query": query,
        "category": category,
        "status": "searching",
        "message": f"🔍 Searching for '{query}' libraries...",
    }


def create_library_options_message(
    query: str,
    libraries: list[dict[str, Any]],
    formatted_text: str,
) -> dict[str, Any]:
    """
    Create WebSocket message with library options.

    Args:
        query: Search query
        libraries: List of libraries
        formatted_text: Formatted presentation text

    Returns:
        WebSocket message dictionary
    """
    return {
        "type": "library_options",
        "query": query,
        "libraries": [
            {
                "library_name": lib.get("library_name"),
                "ranking_score": lib.get("ranking_score"),
                "stars": lib.get("stars"),
                "license": lib.get("license"),
                "bundle_size": lib.get("bundle_size"),
                "description": lib.get("description"),
                "github_url": lib.get("github_url"),
                "npm_url": lib.get("npm_url"),
            }
            for lib in libraries[:3]
        ],
        "formatted_text": formatted_text,
        "awaiting_selection": True,
    }


def create_library_selection_message(
    result: dict[str, Any],
    query: str,
) -> dict[str, Any]:
    """
    Create WebSocket message for selection result.

    Args:
        result: Selection result from process_library_selection()
        query: Search query

    Returns:
        WebSocket message dictionary
    """
    return {
        "type": "library_selected",
        "query": query,
        "selected": result["selected"],
        "library": result.get("library"),
        "message": result["message"],
        "install_command": result.get("install_command"),
    }


__all__ = [
    "format_library_option",
    "present_library_options",
    "process_library_selection",
    "create_library_suggestion_message",
    "create_library_options_message",
    "create_library_selection_message",
]
