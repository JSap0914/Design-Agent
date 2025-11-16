"""
Library ranking algorithm.

Calculates 0-100 scores based on:
- Popularity (40%): GitHub stars + npm downloads
- Recency (20%): Days since last update
- Quality (20%): TypeScript support, documentation, tests
- Size (20%): Bundle size
"""

import math
from typing import Any

from src.utils.logger import get_logger

logger = get_logger(__name__)


def calculate_popularity_score(library: dict[str, Any]) -> float:
    """
    Calculate popularity score (0-100) based on stars and downloads.

    Logarithmic scale:
    - 1K stars = 50 points
    - 10K stars = 75 points
    - 100K+ stars = 100 points

    Args:
        library: Library dictionary

    Returns:
        Popularity score (0-100)
    """
    stars = library.get("stars", 0)
    npm_popularity = library.get("popularity_score", 0)

    if stars > 0:
        # Logarithmic scale for GitHub stars
        # log10(1000) = 3 -> 50, log10(10000) = 4 -> 75, log10(100000) = 5 -> 100
        if stars >= 100000:
            star_score = 100
        elif stars >= 10000:
            star_score = 75 + (25 * (math.log10(stars) - 4))
        elif stars >= 1000:
            star_score = 50 + (25 * (math.log10(stars) - 3))
        else:
            star_score = 50 * (math.log10(max(stars, 10)) / 3)

        return min(100, star_score)

    elif npm_popularity > 0:
        # npm popularity score is already 0-1, convert to 0-100
        return npm_popularity * 100

    return 0


def calculate_recency_score(library: dict[str, Any]) -> float:
    """
    Calculate recency score (0-100) based on days since last update.

    - <30 days = 100
    - 30-90 days = 80-100 (linear decay)
    - 90-180 days = 50-80 (linear decay)
    - 180-365 days = 20-50 (linear decay)
    - >365 days = 0-20 (linear decay)

    Args:
        library: Library dictionary with 'days_since_update'

    Returns:
        Recency score (0-100)
    """
    days = library.get("days_since_update")

    if days is None:
        # Try parsing last_update
        if "last_update" in library:
            from datetime import datetime
            try:
                last_update_str = library["last_update"]
                last_update = datetime.fromisoformat(last_update_str.replace("Z", "+00:00"))
                days = (datetime.now(last_update.tzinfo) - last_update).days
            except:
                return 50  # Default if can't parse

    if days is None:
        return 50  # Default if no data

    if days < 30:
        return 100
    elif days < 90:
        return 100 - (20 * (days - 30) / 60)
    elif days < 180:
        return 80 - (30 * (days - 90) / 90)
    elif days < 365:
        return 50 - (30 * (days - 180) / 185)
    else:
        return max(0, 20 - (20 * (days - 365) / 365))


def calculate_quality_score(library: dict[str, Any]) -> float:
    """
    Calculate quality score (0-100) based on TypeScript, docs, tests.

    - TypeScript support: +40 points
    - Has documentation (homepage/README): +30 points
    - npm quality score: +30 points

    Args:
        library: Library dictionary

    Returns:
        Quality score (0-100)
    """
    score = 0

    # TypeScript support (+40)
    language = library.get("language", "").lower()
    keywords = library.get("keywords", [])
    topics = library.get("topics", [])

    has_typescript = (
        "typescript" in language
        or "typescript" in keywords
        or "typescript" in topics
        or library.get("library_name", "").startswith("@types/")
    )

    if has_typescript:
        score += 40

    # Documentation (+30)
    has_docs = bool(library.get("homepage") or library.get("description"))
    if has_docs:
        score += 30

    # npm quality score (+30)
    npm_quality = library.get("quality_score", 0)
    if npm_quality > 0:
        score += npm_quality * 30

    return min(100, score)


def calculate_size_score(library: dict[str, Any]) -> float:
    """
    Calculate size score (0-100) based on bundle size.

    - <10KB = 100
    - 10-50KB = 80-100 (linear)
    - 50-100KB = 50-80 (linear)
    - 100-200KB = 20-50 (linear)
    - >200KB = 0-20 (linear)

    Args:
        library: Library dictionary with 'bundle_size'

    Returns:
        Size score (0-100)
    """
    bundle_size_str = library.get("bundle_size")

    if not bundle_size_str:
        return 50  # Default if no size data

    # Parse size string (e.g., "15KB", "1.2MB")
    try:
        size_str = bundle_size_str.upper().replace(" ", "")

        if "MB" in size_str:
            size_kb = float(size_str.replace("MB", "")) * 1024
        elif "KB" in size_str:
            size_kb = float(size_str.replace("KB", ""))
        elif "B" in size_str:
            size_kb = float(size_str.replace("B", "")) / 1024
        else:
            return 50

        if size_kb < 10:
            return 100
        elif size_kb < 50:
            return 100 - (20 * (size_kb - 10) / 40)
        elif size_kb < 100:
            return 80 - (30 * (size_kb - 50) / 50)
        elif size_kb < 200:
            return 50 - (30 * (size_kb - 100) / 100)
        else:
            return max(0, 20 - (20 * (size_kb - 200) / 200))

    except Exception as e:
        logger.warning(f"Could not parse bundle size: {bundle_size_str}", error=str(e))
        return 50


def calculate_ranking_score(library: dict[str, Any]) -> float:
    """
    Calculate overall ranking score (0-100).

    Formula:
    - Popularity (40%)
    - Recency (20%)
    - Quality (20%)
    - Size (20%)

    Args:
        library: Library dictionary

    Returns:
        Overall score (0-100)
    """
    popularity = calculate_popularity_score(library)
    recency = calculate_recency_score(library)
    quality = calculate_quality_score(library)
    size = calculate_size_score(library)

    overall = (
        popularity * 0.40 +
        recency * 0.20 +
        quality * 0.20 +
        size * 0.20
    )

    score = round(overall, 1)

    logger.debug(
        f"Ranking: {library.get('library_name')}",
        score=score,
        popularity=round(popularity, 1),
        recency=round(recency, 1),
        quality=round(quality, 1),
        size=round(size, 1),
    )

    return score


def rank_libraries(libraries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Rank and sort libraries by score (highest first).

    Adds 'ranking_score' field to each library.

    Args:
        libraries: List of library dictionaries

    Returns:
        Sorted list with ranking scores
    """
    logger.info(f"Ranking {len(libraries)} libraries")

    # Calculate scores
    for library in libraries:
        library["ranking_score"] = calculate_ranking_score(library)

    # Sort by score (highest first)
    ranked = sorted(libraries, key=lambda x: x["ranking_score"], reverse=True)

    logger.info(
        f"Ranking complete",
        top_score=ranked[0]["ranking_score"] if ranked else 0,
        top_library=ranked[0].get("library_name") if ranked else None,
    )

    return ranked


__all__ = [
    "calculate_popularity_score",
    "calculate_recency_score",
    "calculate_quality_score",
    "calculate_size_score",
    "calculate_ranking_score",
    "rank_libraries",
]
