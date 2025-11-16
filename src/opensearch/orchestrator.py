"""
Open-source discovery orchestrator.

Coordinates the full search → filter → rank → present → select workflow.
"""

from typing import Any

from src.opensearch.searcher import search_all_sources
from src.opensearch.filter import filter_libraries
from src.opensearch.ranker import rank_libraries
from src.opensearch.translator import translate_library_descriptions
from src.opensearch.selector import (
    present_library_options,
    process_library_selection,
    create_library_suggestion_message,
    create_library_options_message,
    create_library_selection_message,
)
from src.opensearch.cache import get_cached_results, cache_results
from src.utils.logger import get_logger

logger = get_logger(__name__)


async def discover_libraries(
    query: str,
    category: str = "ui_components",
    language: str = "typescript",
    min_stars: int = 500,
    max_days_since_update: int = 365,
    require_typescript: bool = True,
    tech_stack: list[str] | None = None,
    max_options: int = 3,
) -> dict[str, Any]:
    """
    Complete library discovery workflow.

    Workflow:
    1. Search GitHub, npm, web (parallel)
    2. Filter by license, recency, stars, TypeScript, tech stack
    3. Rank by weighted score (0-100)
    4. Return top N options

    Args:
        query: Search query (e.g., "data table react")
        category: Library category (ui_components, forms, icons, charts, etc.)
        language: Programming language filter (default: typescript)
        min_stars: Minimum GitHub stars (default: 500)
        max_days_since_update: Maximum days since last update (default: 365)
        require_typescript: Require TypeScript support (default: True)
        tech_stack: Required technologies (default: None)
        max_options: Maximum options to return (default: 3)

    Returns:
        Dictionary with:
        - success: bool
        - query: str
        - category: str
        - libraries: list[dict] (top ranked libraries)
        - formatted_text: str (presentation text)
        - error: str | None
    """
    try:
        logger.info(f"Starting library discovery", query=query, category=category)

        # Step 0: Check cache
        cached_result = await get_cached_results(
            query=query,
            category=category,
            language=language,
            min_stars=min_stars,
            max_days=max_days_since_update,
        )

        if cached_result:
            logger.info(f"Returning cached library results", query=query, category=category)
            return cached_result

        # Step 1: Multi-source search
        logger.debug(f"Searching all sources for '{query}'")
        raw_results = await search_all_sources(query, category=category, language=language)

        if not raw_results:
            logger.warning(f"No results found for '{query}'")
            return {
                "success": False,
                "query": query,
                "category": category,
                "libraries": [],
                "formatted_text": f"🔍 No libraries found for '{query}'. Try a different search or skip.",
                "error": "No results found",
            }

        logger.debug(f"Found {len(raw_results)} raw results")

        # Step 2: Filter
        logger.debug("Filtering libraries")
        filtered = filter_libraries(
            raw_results,
            min_stars=min_stars,
            max_days_since_update=max_days_since_update,
            require_typescript=require_typescript,
            tech_stack=tech_stack,
            require_license=True,
        )

        if not filtered:
            logger.warning(f"No libraries passed filters for '{query}'")
            return {
                "success": False,
                "query": query,
                "category": category,
                "libraries": [],
                "formatted_text": f"🔍 Found {len(raw_results)} libraries, but none met the quality criteria. Try relaxing filters or skip.",
                "error": "No libraries passed filters",
            }

        logger.debug(f"{len(filtered)} libraries passed filters")

        # Step 3: Rank
        logger.debug("Ranking libraries")
        ranked = rank_libraries(filtered)

        # Step 3.5: Translate non-English descriptions
        logger.debug("Translating non-English descriptions")
        ranked = await translate_library_descriptions(ranked)

        # Step 4: Format for presentation
        top_libraries = ranked[:max_options]
        formatted_text = present_library_options(top_libraries, query, max_options=max_options)

        logger.info(
            f"Library discovery complete",
            query=query,
            total_results=len(raw_results),
            filtered_count=len(filtered),
            top_count=len(top_libraries),
        )

        # Prepare result
        result = {
            "success": True,
            "query": query,
            "category": category,
            "libraries": top_libraries,
            "formatted_text": formatted_text,
            "error": None,
        }

        # Cache the result (15 minute TTL)
        await cache_results(
            query=query,
            results=result,
            category=category,
            language=language,
            ttl=900,  # 15 minutes
            min_stars=min_stars,
            max_days=max_days_since_update,
        )

        return result

    except Exception as e:
        logger.error(f"Library discovery failed", query=query, error=str(e))
        return {
            "success": False,
            "query": query,
            "category": category,
            "libraries": [],
            "formatted_text": f"❌ Search failed for '{query}': {str(e)}",
            "error": str(e),
        }


async def handle_library_selection(
    user_input: str,
    libraries: list[dict[str, Any]],
    query: str,
    category: str,
) -> dict[str, Any]:
    """
    Process user's library selection and prepare state update.

    Args:
        user_input: User's choice (1, 2, 3, skip, etc.)
        libraries: List of ranked libraries
        query: Original search query
        category: Library category

    Returns:
        Dictionary with:
        - selection_result: dict (from process_library_selection)
        - state_update: dict (fields to update in DesignAgentState)
        - websocket_message: dict (message to broadcast)
    """
    # Process selection
    selection_result = process_library_selection(user_input, libraries, query)

    # Prepare state update
    state_update = {}

    if selection_result["selected"]:
        # Add to selected_open_source list
        selected_library = selection_result["library"]
        recommendation = {
            "category": category,
            "library_name": selected_library.get("library_name", ""),
            "github_url": selected_library.get("github_url"),
            "npm_url": selected_library.get("npm_url"),
            "stars": selected_library.get("stars"),
            "license": selected_library.get("license"),
            "bundle_size": selected_library.get("bundle_size"),
            "version": selected_library.get("version"),
            "ranking_score": selected_library.get("ranking_score"),
            "rationale": f"Selected by user from search query '{query}' for {category}",
            "alternatives": [
                {
                    "library_name": lib.get("library_name"),
                    "ranking_score": lib.get("ranking_score"),
                }
                for lib in libraries
                if lib != selected_library
            ],
        }

        state_update = {
            "selected_open_source": recommendation,  # Will be appended by node
        }

        logger.info(
            f"Library selected",
            library=selected_library.get("library_name"),
            query=query,
            category=category,
        )
    else:
        logger.info(f"Library selection skipped", query=query, category=category)

    # Create WebSocket message
    websocket_message = create_library_selection_message(selection_result, query)

    return {
        "selection_result": selection_result,
        "state_update": state_update,
        "websocket_message": websocket_message,
    }


__all__ = [
    "discover_libraries",
    "handle_library_selection",
]
