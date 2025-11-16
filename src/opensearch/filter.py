"""
Library filtering logic.

Filters search results by license, recency, stars, TypeScript support,
and tech stack compatibility.
"""

from datetime import datetime, timedelta
from typing import Any

from src.utils.logger import get_logger

logger = get_logger(__name__)

# Allowed open-source licenses
ALLOWED_LICENSES = ["MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause", "ISC"]


def filter_by_license(library: dict[str, Any]) -> bool:
    """
    Filter by allowed licenses (MIT, Apache 2.0, BSD, ISC).

    Args:
        library: Library dictionary with 'license' field

    Returns:
        True if license is allowed, False otherwise
    """
    license_id = library.get("license")

    if not license_id:
        logger.debug(f"No license found for {library.get('library_name')}")
        return False

    is_allowed = license_id in ALLOWED_LICENSES

    if not is_allowed:
        logger.debug(
            f"License {license_id} not allowed for {library.get('library_name')}",
            allowed=ALLOWED_LICENSES
        )

    return is_allowed


def filter_by_recency(library: dict[str, Any], max_days: int = 365) -> bool:
    """
    Filter by recency (updated within last N days).

    Args:
        library: Library dictionary with 'days_since_update' or 'last_update'
        max_days: Maximum days since last update (default: 365 = 12 months)

    Returns:
        True if recently updated, False otherwise
    """
    # Check if days_since_update is already calculated (GitHub results)
    if "days_since_update" in library:
        days = library["days_since_update"]
        is_recent = days <= max_days

        if not is_recent:
            logger.debug(
                f"Library too old: {library.get('library_name')} ({days} days)",
                max_days=max_days
            )

        return is_recent

    # Parse last_update timestamp (npm results)
    if "last_update" in library:
        try:
            last_update_str = library["last_update"]
            last_update = datetime.fromisoformat(last_update_str.replace("Z", "+00:00"))
            days_since = (datetime.now(last_update.tzinfo) - last_update).days

            is_recent = days_since <= max_days

            if not is_recent:
                logger.debug(
                    f"Library too old: {library.get('library_name')} ({days_since} days)"
                )

            return is_recent
        except Exception as e:
            logger.warning(f"Could not parse last_update: {e}")
            return False

    logger.debug(f"No recency data for {library.get('library_name')}")
    return False


def filter_by_stars(library: dict[str, Any], min_stars: int = 500) -> bool:
    """
    Filter by minimum GitHub stars.

    Args:
        library: Library dictionary with 'stars' field
        min_stars: Minimum required stars (default: 500)

    Returns:
        True if meets minimum stars, False otherwise
    """
    stars = library.get("stars", 0)

    has_enough_stars = stars >= min_stars

    if not has_enough_stars:
        logger.debug(
            f"Not enough stars: {library.get('library_name')} ({stars} < {min_stars})"
        )

    return has_enough_stars


def filter_by_typescript(library: dict[str, Any]) -> bool:
    """
    Filter by TypeScript support.

    Checks:
    - Language is TypeScript
    - Package has 'types' in keywords
    - Has @types/* equivalent

    Args:
        library: Library dictionary

    Returns:
        True if has TypeScript support, False otherwise
    """
    # Check language field (GitHub)
    language = library.get("language", "").lower()
    if "typescript" in language:
        return True

    # Check keywords (npm)
    keywords = library.get("keywords", [])
    if isinstance(keywords, list):
        keyword_str = " ".join(keywords).lower()
        if "typescript" in keyword_str or "types" in keyword_str:
            return True

    # Check topics (GitHub)
    topics = library.get("topics", [])
    if isinstance(topics, list):
        if "typescript" in topics or "types" in topics:
            return True

    # Check if it's a @types/* package
    library_name = library.get("library_name", "")
    if library_name.startswith("@types/"):
        return True

    logger.debug(f"No TypeScript support detected for {library_name}")
    return False


def filter_by_tech_stack(library: dict[str, Any], tech_stack: list[str]) -> bool:
    """
    Filter by tech stack compatibility.

    Args:
        library: Library dictionary
        tech_stack: List of required technologies (e.g., ["react", "typescript"])

    Returns:
        True if compatible with tech stack, False otherwise
    """
    if not tech_stack:
        return True  # No specific requirements

    tech_stack_lower = [tech.lower() for tech in tech_stack]

    # Check library name
    library_name = library.get("library_name", "").lower()

    # Check keywords
    keywords = library.get("keywords", [])
    if isinstance(keywords, list):
        keywords_lower = [k.lower() for k in keywords]
    else:
        keywords_lower = []

    # Check topics
    topics = library.get("topics", [])
    if isinstance(topics, list):
        topics_lower = [t.lower() for t in topics]
    else:
        topics_lower = []

    # Check description
    description = library.get("description", "").lower()

    # Combined search space
    search_space = library_name + " " + " ".join(keywords_lower) + " " + " ".join(topics_lower) + " " + description

    # Check if any required tech is mentioned
    for tech in tech_stack_lower:
        if tech in search_space:
            return True

    logger.debug(
        f"Not compatible with tech stack: {library.get('library_name')}",
        required=tech_stack
    )
    return False


def filter_libraries(
    libraries: list[dict[str, Any]],
    min_stars: int = 500,
    max_days_since_update: int = 365,
    require_typescript: bool = True,
    tech_stack: list[str] | None = None,
    require_license: bool = True,
) -> list[dict[str, Any]]:
    """
    Apply all filters to library list.

    Args:
        libraries: List of library dictionaries
        min_stars: Minimum GitHub stars (default: 500)
        max_days_since_update: Maximum days since last update (default: 365)
        require_typescript: Require TypeScript support (default: True)
        tech_stack: Required technologies (default: None)
        require_license: Require allowed license (default: True)

    Returns:
        Filtered list of libraries
    """
    logger.info(
        f"Filtering {len(libraries)} libraries",
        min_stars=min_stars,
        max_days=max_days_since_update,
        require_typescript=require_typescript,
        require_license=require_license,
    )

    filtered = []

    for library in libraries:
        # Apply filters
        if require_license and not filter_by_license(library):
            continue

        if not filter_by_recency(library, max_days=max_days_since_update):
            continue

        # Only filter by stars if we have star data (GitHub results)
        if "stars" in library and not filter_by_stars(library, min_stars=min_stars):
            continue

        if require_typescript and not filter_by_typescript(library):
            continue

        if tech_stack and not filter_by_tech_stack(library, tech_stack):
            continue

        filtered.append(library)

    logger.info(
        f"Filtering complete: {len(filtered)}/{len(libraries)} libraries passed",
        pass_rate=f"{len(filtered)/len(libraries)*100:.1f}%" if libraries else "0%"
    )

    return filtered


__all__ = [
    "filter_by_license",
    "filter_by_recency",
    "filter_by_stars",
    "filter_by_typescript",
    "filter_by_tech_stack",
    "filter_libraries",
]
