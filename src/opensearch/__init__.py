"""
Open-source library discovery system.

Multi-source search, filtering, ranking, and user selection for
real-time library recommendations during Phase 3 refinement.
"""

from src.opensearch.searcher import search_github, search_npm, search_web, search_all_sources
from src.opensearch.filter import filter_libraries
from src.opensearch.ranker import calculate_ranking_score, rank_libraries
from src.opensearch.selector import (
    present_library_options,
    process_library_selection,
    create_library_suggestion_message,
    create_library_options_message,
    create_library_selection_message,
)
from src.opensearch.orchestrator import discover_libraries, handle_library_selection
from src.opensearch.cache import get_cached_results, cache_results, clear_cache_for_query, clear_all_cache

__all__ = [
    # Search
    "search_github",
    "search_npm",
    "search_web",
    "search_all_sources",
    # Filter & Rank
    "filter_libraries",
    "calculate_ranking_score",
    "rank_libraries",
    # Selection
    "present_library_options",
    "process_library_selection",
    "create_library_suggestion_message",
    "create_library_options_message",
    "create_library_selection_message",
    # Orchestration (recommended for integration)
    "discover_libraries",
    "handle_library_selection",
    # Cache
    "get_cached_results",
    "cache_results",
    "clear_cache_for_query",
    "clear_all_cache",
]
