"""
Redis caching for library search results.

Caches search results for 15 minutes to reduce API calls and improve response time.
"""

import hashlib
import json
import os
from typing import Any

from src.utils.logger import get_logger

logger = get_logger(__name__)

# Redis client (lazy initialization)
_redis_client = None


def _get_redis_client():
    """
    Get or create Redis client (lazy initialization).

    Returns:
        Redis client or None if Redis is not available
    """
    global _redis_client

    if _redis_client is not None:
        return _redis_client

    try:
        import redis

        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

        # Parse Redis URL and create client
        _redis_client = redis.from_url(
            redis_url,
            decode_responses=True,  # Automatically decode bytes to strings
            socket_connect_timeout=2,  # 2 second connection timeout
            socket_timeout=2,  # 2 second read timeout
        )

        # Test connection
        _redis_client.ping()
        logger.info("Redis client initialized", redis_url=redis_url)

        return _redis_client

    except ImportError:
        logger.warning("Redis library not installed, caching disabled")
        return None
    except Exception as e:
        logger.warning(f"Redis connection failed, caching disabled", error=str(e))
        return None


def _generate_cache_key(query: str, category: str, language: str, **kwargs) -> str:
    """
    Generate a unique cache key for search parameters.

    Args:
        query: Search query
        category: Library category
        language: Programming language
        **kwargs: Additional search parameters

    Returns:
        Unique cache key string
    """
    # Create a deterministic string from all parameters
    params = {
        "query": query,
        "category": category,
        "language": language,
        **kwargs,
    }

    # Sort keys for deterministic ordering
    param_str = json.dumps(params, sort_keys=True)

    # Hash to create shorter key
    hash_obj = hashlib.sha256(param_str.encode())
    hash_hex = hash_obj.hexdigest()[:16]  # Use first 16 chars of hash

    # Prefix with namespace
    return f"opensearch:library:{hash_hex}"


async def get_cached_results(
    query: str,
    category: str = "ui_components",
    language: str = "typescript",
    **kwargs,
) -> dict[str, Any] | None:
    """
    Get cached library search results.

    Args:
        query: Search query
        category: Library category
        language: Programming language
        **kwargs: Additional search parameters

    Returns:
        Cached results dictionary or None if not found/expired
    """
    redis_client = _get_redis_client()

    if not redis_client:
        # Redis not available
        return None

    try:
        cache_key = _generate_cache_key(query, category, language, **kwargs)
        cached_data = redis_client.get(cache_key)

        if cached_data:
            logger.info(f"Cache hit for library search", query=query, category=category)
            return json.loads(cached_data)
        else:
            logger.debug(f"Cache miss for library search", query=query, category=category)
            return None

    except Exception as e:
        logger.warning(f"Cache read failed", error=str(e), query=query)
        return None


async def cache_results(
    query: str,
    results: dict[str, Any],
    category: str = "ui_components",
    language: str = "typescript",
    ttl: int = 900,  # 15 minutes
    **kwargs,
) -> bool:
    """
    Cache library search results.

    Args:
        query: Search query
        results: Search results to cache
        category: Library category
        language: Programming language
        ttl: Time-to-live in seconds (default: 900 = 15 minutes)
        **kwargs: Additional search parameters

    Returns:
        True if successfully cached, False otherwise
    """
    redis_client = _get_redis_client()

    if not redis_client:
        # Redis not available
        return False

    try:
        cache_key = _generate_cache_key(query, category, language, **kwargs)
        cached_data = json.dumps(results)

        # Set with TTL
        redis_client.setex(cache_key, ttl, cached_data)

        logger.info(
            f"Cached library search results",
            query=query,
            category=category,
            ttl=ttl,
            result_count=len(results.get("libraries", [])),
        )

        return True

    except Exception as e:
        logger.warning(f"Cache write failed", error=str(e), query=query)
        return False


async def clear_cache_for_query(
    query: str,
    category: str = "ui_components",
    language: str = "typescript",
    **kwargs,
) -> bool:
    """
    Clear cached results for a specific query.

    Args:
        query: Search query
        category: Library category
        language: Programming language
        **kwargs: Additional search parameters

    Returns:
        True if successfully cleared, False otherwise
    """
    redis_client = _get_redis_client()

    if not redis_client:
        return False

    try:
        cache_key = _generate_cache_key(query, category, language, **kwargs)
        deleted = redis_client.delete(cache_key)

        logger.info(f"Cache cleared for query", query=query, deleted=bool(deleted))

        return bool(deleted)

    except Exception as e:
        logger.warning(f"Cache clear failed", error=str(e), query=query)
        return False


async def clear_all_cache() -> bool:
    """
    Clear all cached library search results.

    WARNING: This clears ALL opensearch:library:* keys.

    Returns:
        True if successfully cleared, False otherwise
    """
    redis_client = _get_redis_client()

    if not redis_client:
        return False

    try:
        # Find all keys with our prefix
        pattern = "opensearch:library:*"
        keys = redis_client.keys(pattern)

        if keys:
            deleted = redis_client.delete(*keys)
            logger.info(f"Cleared all library cache", key_count=deleted)
            return True
        else:
            logger.info("No cached library results to clear")
            return True

    except Exception as e:
        logger.warning(f"Cache clear all failed", error=str(e))
        return False


__all__ = [
    "get_cached_results",
    "cache_results",
    "clear_cache_for_query",
    "clear_all_cache",
]
