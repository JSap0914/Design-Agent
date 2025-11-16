"""
Multi-source open-source library search.

Searches GitHub, npm Registry, and web for relevant libraries
based on user's feature requests during Phase 3 refinement.
"""

import asyncio
from datetime import datetime
from typing import Any
import os

import httpx
from src.utils.logger import get_logger

logger = get_logger(__name__)


# ============================================================================
# GitHub API Search
# ============================================================================


async def search_github(
    query: str,
    language: str = "typescript",
    min_stars: int = 500,
    max_results: int = 10,
) -> list[dict[str, Any]]:
    """
    Search GitHub repositories via REST API v3.

    Args:
        query: Search query (e.g., "data table react")
        language: Programming language filter (default: typescript)
        min_stars: Minimum GitHub stars (default: 500)
        max_results: Maximum results to return (default: 10)

    Returns:
        List of repository dictionaries with metadata
    """
    try:
        url = "https://api.github.com/search/repositories"
        github_query = f"{query} language:{language} stars:>={min_stars}"

        params = {
            "q": github_query,
            "sort": "stars",
            "order": "desc",
            "per_page": max_results,
        }

        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        github_token = os.getenv("GITHUB_TOKEN")
        if github_token:
            headers["Authorization"] = f"Bearer {github_token}"

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()

            data = response.json()
            repositories = data.get("items", [])

            results = []
            for repo in repositories:
                updated_at = datetime.fromisoformat(repo["updated_at"].replace("Z", "+00:00"))
                days_since_update = (datetime.now(updated_at.tzinfo) - updated_at).days

                result = {
                    "source": "github",
                    "library_name": repo["full_name"],
                    "github_url": repo["html_url"],
                    "description": repo.get("description", ""),
                    "stars": repo["stargazers_count"],
                    "language": repo.get("language", ""),
                    "license": repo.get("license", {}).get("spdx_id") if repo.get("license") else None,
                    "last_update": repo["updated_at"],
                    "days_since_update": days_since_update,
                    "topics": repo.get("topics", []),
                    "homepage": repo.get("homepage"),
                }
                results.append(result)

            logger.info(f"GitHub search completed", query=query, results_count=len(results))
            return results

    except Exception as e:
        logger.error(f"GitHub search failed: {e}", query=query)
        return []


# ============================================================================
# npm Registry API Search
# ============================================================================


async def search_npm(query: str, max_results: int = 10) -> list[dict[str, Any]]:
    """
    Search npm Registry for packages.

    Args:
        query: Search query (e.g., "data table react")
        max_results: Maximum results to return (default: 10)

    Returns:
        List of package dictionaries with metadata
    """
    try:
        url = "https://registry.npmjs.org/-/v1/search"
        params = {"text": query, "size": max_results}

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()

            data = response.json()
            packages = data.get("objects", [])

            results = []
            for pkg_obj in packages:
                pkg = pkg_obj.get("package", {})
                links = pkg.get("links", {})
                score_obj = pkg_obj.get("score", {})

                result = {
                    "source": "npm",
                    "library_name": pkg.get("name", ""),
                    "npm_url": links.get("npm", f"https://www.npmjs.com/package/{pkg.get('name', '')}"),
                    "github_url": links.get("repository"),
                    "homepage": links.get("homepage"),
                    "description": pkg.get("description", ""),
                    "version": pkg.get("version", ""),
                    "keywords": pkg.get("keywords", []),
                    "last_update": pkg.get("date"),
                    "npm_score": score_obj.get("final", 0),
                    "quality_score": score_obj.get("detail", {}).get("quality", 0),
                    "popularity_score": score_obj.get("detail", {}).get("popularity", 0),
                }
                results.append(result)

            logger.info(f"npm search completed", query=query, results_count=len(results))
            return results

    except Exception as e:
        logger.error(f"npm search failed: {e}", query=query)
        return []


# ============================================================================
# Web Search API
# ============================================================================


async def search_web(query: str, year: int = 2025, max_results: int = 5) -> list[dict[str, Any]]:
    """
    Search web for recent articles about libraries.

    Args:
        query: Search query
        year: Filter by year (default: 2025)
        max_results: Maximum results to return

    Returns:
        List of web search results
    """
    try:
        google_api_key = os.getenv("GOOGLE_SEARCH_API_KEY")
        google_cx = os.getenv("GOOGLE_SEARCH_CX")
        brave_api_key = os.getenv("BRAVE_API_KEY")

        if google_api_key and google_cx:
            return await _search_google(query, year, max_results, google_api_key, google_cx)
        elif brave_api_key:
            return await _search_brave(query, year, max_results, brave_api_key)
        else:
            logger.warning("No web search API keys configured")
            return []

    except Exception as e:
        logger.error(f"Web search failed: {e}", query=query)
        return []


async def _search_google(query: str, year: int, max_results: int, api_key: str, cx: str) -> list[dict]:
    """Search using Google Custom Search API."""
    url = "https://www.googleapis.com/customsearch/v1"
    search_query = f"best {query} library {year}"
    params = {"key": api_key, "cx": cx, "q": search_query, "num": max_results}

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        items = response.json().get("items", [])

        return [
            {"source": "google", "title": item.get("title", ""), "url": item.get("link", ""), "snippet": item.get("snippet", "")}
            for item in items
        ]


async def _search_brave(query: str, year: int, max_results: int, api_key: str) -> list[dict]:
    """Search using Brave Search API."""
    url = "https://api.search.brave.com/res/v1/web/search"
    search_query = f"best {query} library {year}"
    headers = {"Accept": "application/json", "X-Subscription-Token": api_key}
    params = {"q": search_query, "count": max_results}

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url, headers=headers, params=params)
        response.raise_for_status()
        web_results = response.json().get("web", {}).get("results", [])

        return [
            {"source": "brave", "title": item.get("title", ""), "url": item.get("url", ""), "snippet": item.get("description", "")}
            for item in web_results
        ]


# ============================================================================
# Combined Multi-Source Search
# ============================================================================


async def search_all_sources(query: str, category: str = "ui_components", language: str = "typescript") -> list[dict[str, Any]]:
    """
    Search all sources in parallel and combine results.

    Args:
        query: Search query
        category: Library category
        language: Programming language filter

    Returns:
        Combined list of results from all sources
    """
    logger.info(f"Starting multi-source search", query=query, category=category)

    github_task = search_github(query, language=language)
    npm_task = search_npm(query)
    web_task = search_web(query)

    github_results, npm_results, web_results = await asyncio.gather(
        github_task, npm_task, web_task, return_exceptions=True
    )

    # Handle exceptions
    if isinstance(github_results, Exception):
        github_results = []
    if isinstance(npm_results, Exception):
        npm_results = []
    if isinstance(web_results, Exception):
        web_results = []

    all_results = github_results + npm_results + web_results

    logger.info(f"Multi-source search completed", total_results=len(all_results))
    return all_results


__all__ = ["search_github", "search_npm", "search_web", "search_all_sources"]
