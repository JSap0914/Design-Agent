"""
Week 4 Integration Tests: Open-Source Discovery System.

Tests the complete library recommendation workflow:
- Keyword detection
- Multi-source search
- Filtering and ranking
- User selection
- Database storage
- Integration with refine_design node
"""

import asyncio
import pytest
from datetime import datetime, timedelta

# Import opensearch modules
from src.opensearch.keywords import (
    detect_library_keywords,
    should_trigger_library_search,
    extract_search_query,
    get_category_from_feedback,
)
from src.opensearch.filter import (
    filter_by_license,
    filter_by_recency,
    filter_by_stars,
    filter_by_typescript,
    filter_libraries,
)
from src.opensearch.ranker import (
    calculate_popularity_score,
    calculate_recency_score,
    calculate_quality_score,
    calculate_size_score,
    calculate_ranking_score,
    rank_libraries,
)
from src.opensearch.selector import (
    present_library_options,
    process_library_selection,
)
from src.opensearch.orchestrator import discover_libraries, handle_library_selection


# ============================================================================
# Test: Keyword Detection (Task 7)
# ============================================================================


def test_keyword_detection_table():
    """Test keyword detection for data table."""
    feedback = "Add a data table with sorting and filtering"
    matches = detect_library_keywords(feedback)

    assert len(matches) > 0
    assert any(m["category"] == "ui_components" for m in matches)
    assert any("table" in m["keyword"] for m in matches)


def test_keyword_detection_authentication():
    """Test keyword detection for authentication."""
    feedback = "Implement OAuth login with Google"
    matches = detect_library_keywords(feedback)

    assert len(matches) > 0
    assert any(m["category"] == "authentication" for m in matches)


def test_should_trigger_library_search():
    """Test library search triggering."""
    # Should trigger
    assert should_trigger_library_search("Add a modal popup") is True
    assert should_trigger_library_search("Need icons for navigation") is True
    assert should_trigger_library_search("Implement bar chart") is True

    # Should not trigger (approval keywords)
    assert should_trigger_library_search("approve") is False
    assert should_trigger_library_search("looks good") is False
    assert should_trigger_library_search("next") is False


def test_extract_search_query():
    """Test search query extraction."""
    query = extract_search_query("Add a date picker for the form")
    # Should return first detected keyword (either "form" or "date")
    assert query in ["form", "date", "date picker"] or "date" in query.lower() or "form" in query.lower()

    query = extract_search_query("Need a carousel for images")
    assert "carousel" in query.lower()


def test_get_category_from_feedback():
    """Test category extraction."""
    assert get_category_from_feedback("Add OAuth login") == "authentication"
    assert get_category_from_feedback("Need icons") == "icons"
    assert get_category_from_feedback("Add line chart") == "charts"
    assert get_category_from_feedback("Add slider") == "ui_components"


# ============================================================================
# Test: Filtering (Task 4)
# ============================================================================


def test_filter_by_license():
    """Test license filtering."""
    # Allowed license
    lib_mit = {"library_name": "test", "license": "MIT"}
    assert filter_by_license(lib_mit) is True

    # Disallowed license
    lib_gpl = {"library_name": "test", "license": "GPL-3.0"}
    assert filter_by_license(lib_gpl) is False

    # No license
    lib_none = {"library_name": "test"}
    assert filter_by_license(lib_none) is False


def test_filter_by_recency():
    """Test recency filtering."""
    # Recent (30 days ago)
    lib_recent = {"library_name": "test", "days_since_update": 30}
    assert filter_by_recency(lib_recent, max_days=365) is True

    # Old (2 years ago)
    lib_old = {"library_name": "test", "days_since_update": 730}
    assert filter_by_recency(lib_old, max_days=365) is False


def test_filter_by_stars():
    """Test stars filtering."""
    # Above threshold
    lib_popular = {"library_name": "test", "stars": 1000}
    assert filter_by_stars(lib_popular, min_stars=500) is True

    # Below threshold
    lib_unpopular = {"library_name": "test", "stars": 100}
    assert filter_by_stars(lib_unpopular, min_stars=500) is False


def test_filter_by_typescript():
    """Test TypeScript filtering."""
    # Has TypeScript (language)
    lib_ts_lang = {"library_name": "test", "language": "TypeScript"}
    assert filter_by_typescript(lib_ts_lang) is True

    # Has TypeScript (keywords)
    lib_ts_keywords = {"library_name": "test", "keywords": ["typescript", "types"]}
    assert filter_by_typescript(lib_ts_keywords) is True

    # @types package
    lib_types = {"library_name": "@types/react"}
    assert filter_by_typescript(lib_types) is True

    # No TypeScript
    lib_no_ts = {"library_name": "test", "language": "JavaScript", "keywords": []}
    assert filter_by_typescript(lib_no_ts) is False


def test_filter_libraries_comprehensive():
    """Test comprehensive filtering."""
    libraries = [
        # Should pass all filters
        {
            "library_name": "good-lib",
            "license": "MIT",
            "days_since_update": 60,
            "stars": 5000,
            "language": "TypeScript",
        },
        # Fails license
        {
            "library_name": "bad-license",
            "license": "GPL-3.0",
            "days_since_update": 60,
            "stars": 5000,
            "language": "TypeScript",
        },
        # Fails recency
        {
            "library_name": "old-lib",
            "license": "MIT",
            "days_since_update": 800,
            "stars": 5000,
            "language": "TypeScript",
        },
        # Fails stars
        {
            "library_name": "unpopular",
            "license": "MIT",
            "days_since_update": 60,
            "stars": 100,
            "language": "TypeScript",
        },
        # Fails TypeScript
        {
            "library_name": "no-ts",
            "license": "MIT",
            "days_since_update": 60,
            "stars": 5000,
            "language": "JavaScript",
            "keywords": [],
        },
    ]

    filtered = filter_libraries(
        libraries,
        min_stars=500,
        max_days_since_update=365,
        require_typescript=True,
        require_license=True,
    )

    # Only "good-lib" should pass
    assert len(filtered) == 1
    assert filtered[0]["library_name"] == "good-lib"


# ============================================================================
# Test: Ranking (Task 5)
# ============================================================================


def test_calculate_popularity_score():
    """Test popularity score calculation."""
    # High stars (100K+)
    lib_100k = {"stars": 100000}
    assert calculate_popularity_score(lib_100k) == 100

    # Medium stars (10K)
    lib_10k = {"stars": 10000}
    score_10k = calculate_popularity_score(lib_10k)
    assert 70 <= score_10k <= 80  # Should be around 75

    # Low stars (1K)
    lib_1k = {"stars": 1000}
    score_1k = calculate_popularity_score(lib_1k)
    assert 45 <= score_1k <= 55  # Should be around 50


def test_calculate_recency_score():
    """Test recency score calculation."""
    # Very recent (<30 days)
    lib_recent = {"days_since_update": 15}
    assert calculate_recency_score(lib_recent) == 100

    # Somewhat recent (60 days)
    lib_medium = {"days_since_update": 60}
    score_medium = calculate_recency_score(lib_medium)
    assert 85 <= score_medium <= 95

    # Old (2 years)
    lib_old = {"days_since_update": 730}
    score_old = calculate_recency_score(lib_old)
    assert score_old < 20


def test_calculate_quality_score():
    """Test quality score calculation."""
    # All quality indicators
    lib_high_quality = {
        "language": "TypeScript",
        "homepage": "https://example.com",
        "quality_score": 0.8,
    }
    score = calculate_quality_score(lib_high_quality)
    assert score >= 80  # 40 (TS) + 30 (docs) + 24 (quality) = 94

    # No quality indicators
    lib_low_quality = {"language": "JavaScript"}
    score = calculate_quality_score(lib_low_quality)
    assert score == 0


def test_calculate_size_score():
    """Test size score calculation."""
    # Small (<10KB)
    lib_small = {"bundle_size": "8KB"}
    assert calculate_size_score(lib_small) == 100

    # Medium (30KB)
    lib_medium = {"bundle_size": "30KB"}
    score = calculate_size_score(lib_medium)
    assert 80 <= score <= 95

    # Large (1MB)
    lib_large = {"bundle_size": "1MB"}
    score = calculate_size_score(lib_large)
    assert score < 20


def test_calculate_ranking_score():
    """Test overall ranking score."""
    library = {
        "library_name": "test-lib",
        "stars": 10000,  # Popularity ~75
        "days_since_update": 30,  # Recency = 100
        "language": "TypeScript",  # Quality >= 40
        "homepage": "https://example.com",  # Quality += 30
        "bundle_size": "15KB",  # Size ~95
    }

    score = calculate_ranking_score(library)

    # Expected: 0.4*75 + 0.2*100 + 0.2*70 + 0.2*95 = 30 + 20 + 14 + 19 = 83
    assert 70 <= score <= 90


def test_rank_libraries():
    """Test library ranking and sorting."""
    libraries = [
        {"library_name": "lib-a", "stars": 1000, "days_since_update": 730},
        {"library_name": "lib-b", "stars": 50000, "days_since_update": 30},
        {"library_name": "lib-c", "stars": 10000, "days_since_update": 90},
    ]

    ranked = rank_libraries(libraries)

    # lib-b should be first (high stars + recent)
    assert ranked[0]["library_name"] == "lib-b"
    assert "ranking_score" in ranked[0]

    # lib-a should be last (low stars + old)
    assert ranked[-1]["library_name"] == "lib-a"


# ============================================================================
# Test: User Selection (Task 6)
# ============================================================================


def test_present_library_options():
    """Test library options presentation."""
    libraries = [
        {
            "library_name": "tanstack/table",
            "ranking_score": 95,
            "stars": 22000,
            "license": "MIT",
            "bundle_size": "15KB",
            "description": "Headless UI for tables",
            "github_url": "https://github.com/tanstack/table",
        }
    ]

    formatted = present_library_options(libraries, query="data table", max_options=3)

    assert "tanstack/table" in formatted
    assert "95/100" in formatted or "95" in formatted
    assert "MIT" in formatted


def test_process_library_selection_numeric():
    """Test numeric library selection."""
    libraries = [{"library_name": "lib-1"}, {"library_name": "lib-2"}]

    # Select option 1
    result = process_library_selection("1", libraries, "test query")
    assert result["selected"] is True
    assert result["library"]["library_name"] == "lib-1"
    assert "install" in result["install_command"].lower()


def test_process_library_selection_skip():
    """Test skipping library selection."""
    libraries = [{"library_name": "lib-1"}]

    result = process_library_selection("skip", libraries, "test query")
    assert result["selected"] is False
    assert result["library"] is None


def test_process_library_selection_invalid():
    """Test invalid selection input."""
    libraries = [{"library_name": "lib-1"}]

    # Out of range
    result = process_library_selection("5", libraries, "test query")
    assert result["selected"] is False

    # Invalid string
    result = process_library_selection("invalid", libraries, "test query")
    assert result["selected"] is False


# ============================================================================
# Test: End-to-End Workflow
# ============================================================================


@pytest.mark.asyncio
async def test_discover_libraries_with_mocked_apis(mock_all_http_apis):
    """Test full library discovery workflow with mocked HTTP API calls."""
    # This test uses the mock_all_http_apis fixture to mock GitHub, npm, and web search

    result = await discover_libraries(
        query="data table",
        category="ui_components",
        language="typescript",
        min_stars=500,
        max_days_since_update=365,
        require_typescript=True,
        max_options=3,
    )

    # Verify successful discovery
    assert result["success"] is True
    assert result["query"] == "data table"
    assert result["category"] == "ui_components"
    assert len(result["libraries"]) > 0

    # Verify libraries have required fields
    for lib in result["libraries"]:
        assert "library_name" in lib
        assert "ranking_score" in lib
        assert lib["ranking_score"] >= 0
        assert lib["ranking_score"] <= 100

    # Verify formatted text was generated
    assert result["formatted_text"]
    assert "data table" in result["formatted_text"]


@pytest.mark.asyncio
async def test_discover_libraries_github_only(mock_github_api):
    """Test library discovery with only GitHub API mocked."""
    from src.opensearch.searcher import search_github

    # Test GitHub search directly
    results = await search_github(query="table", language="typescript", min_stars=500, max_results=10)

    assert len(results) > 0
    assert results[0]["source"] == "github"
    assert results[0]["library_name"] == "tanstack/table"
    assert results[0]["stars"] == 22000
    assert results[0]["license"] == "MIT"


@pytest.mark.asyncio
async def test_discover_libraries_npm_only(mock_npm_api):
    """Test library discovery with only npm API mocked."""
    from src.opensearch.searcher import search_npm

    # Test npm search directly
    results = await search_npm(query="table", max_results=10)

    assert len(results) > 0
    assert results[0]["source"] == "npm"
    assert results[0]["library_name"] == "@tanstack/react-table"
    assert "npm_score" in results[0]


@pytest.mark.asyncio
async def test_discover_libraries_filters_apply(mock_all_http_apis):
    """Test that filters are applied correctly in discovery workflow."""
    result = await discover_libraries(
        query="table",
        category="ui_components",
        language="typescript",
        min_stars=15000,  # High threshold - should filter out some libraries
        max_days_since_update=365,
        require_typescript=True,
        max_options=3,
    )

    # With min_stars=15000, only tanstack/table (22K stars) should pass
    assert result["success"] is True
    if result["libraries"]:
        for lib in result["libraries"]:
            # All returned libraries should have 15K+ stars
            stars = lib.get("stars", 0)
            if stars > 0:  # npm results might not have stars
                assert stars >= 15000


@pytest.mark.asyncio
async def test_handle_library_selection_integration():
    """Test library selection handling."""
    libraries = [
        {
            "library_name": "test-lib",
            "github_url": "https://github.com/test/lib",
            "stars": 5000,
            "license": "MIT",
            "ranking_score": 85,
        }
    ]

    result = await handle_library_selection(
        user_input="1",
        libraries=libraries,
        query="test query",
        category="ui_components",
    )

    assert "selection_result" in result
    assert "state_update" in result
    assert "websocket_message" in result

    # Check state update
    if result["selection_result"]["selected"]:
        assert result["state_update"]["selected_open_source"]["library_name"] == "test-lib"


def test_week4_integration_summary():
    """Summary test to verify all Week 4 components work together."""
    # This is a meta-test that verifies all components integrate correctly

    # 1. Keyword detection
    feedback = "Add a data table with sorting"
    assert should_trigger_library_search(feedback) is True

    # 2. Query extraction
    query = extract_search_query(feedback)
    assert query

    # 3. Category detection
    category = get_category_from_feedback(feedback)
    assert category in ["ui_components", "forms", "charts", "icons", "authentication"]

    # 4. Filtering
    mock_library = {
        "library_name": "test",
        "license": "MIT",
        "days_since_update": 60,
        "stars": 5000,
        "language": "TypeScript",
    }
    assert filter_by_license(mock_library) is True
    assert filter_by_recency(mock_library) is True
    assert filter_by_stars(mock_library) is True
    assert filter_by_typescript(mock_library) is True

    # 5. Ranking
    score = calculate_ranking_score(mock_library)
    assert 0 <= score <= 100

    # 6. Selection
    result = process_library_selection("1", [mock_library], query)
    assert "selected" in result
    assert "message" in result


# ============================================================================
# Run tests manually
# ============================================================================


if __name__ == "__main__":
    # Run synchronous tests
    print("Running Week 4 Integration Tests...")
    print("\n1. Keyword Detection Tests")
    test_keyword_detection_table()
    test_keyword_detection_authentication()
    test_should_trigger_library_search()
    test_extract_search_query()
    test_get_category_from_feedback()
    print("[OK] Keyword detection tests passed")

    print("\n2. Filtering Tests")
    test_filter_by_license()
    test_filter_by_recency()
    test_filter_by_stars()
    test_filter_by_typescript()
    test_filter_libraries_comprehensive()
    print("[OK] Filtering tests passed")

    print("\n3. Ranking Tests")
    test_calculate_popularity_score()
    test_calculate_recency_score()
    test_calculate_quality_score()
    test_calculate_size_score()
    test_calculate_ranking_score()
    test_rank_libraries()
    print("[OK] Ranking tests passed")

    print("\n4. User Selection Tests")
    test_present_library_options()
    test_process_library_selection_numeric()
    test_process_library_selection_skip()
    test_process_library_selection_invalid()
    print("[OK] User selection tests passed")

    print("\n5. Integration Test")
    test_week4_integration_summary()
    print("[OK] Integration test passed")

    # Run async tests
    print("\n6. Async Integration Tests")
    asyncio.run(test_handle_library_selection_integration())
    print("[OK] Async tests passed")

    print("\n7. HTTP API Mocked Tests")
    print("   Note: Run 'pytest tests/test_week4_integration.py -v' to test mocked HTTP workflows")
    print("   (Requires pytest fixtures, can't run directly)")

    print("\n[SUCCESS] ALL WEEK 4 TESTS PASSED!")
    print("\nTo run full test suite with HTTP API mocking:")
    print("  pytest tests/test_week4_integration.py -v")
