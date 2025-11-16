"""
Pytest configuration and fixtures for Design Agent tests.

Provides mocked LLM responses for deterministic testing without API keys.
"""

import pytest
from src.database.connection import db_manager


@pytest.fixture(scope="session", autouse=True)
def initialize_db():
    """Initialize database engine once for all tests."""
    db_manager.initialize_async_engine()
    yield
    # Cleanup after all tests


@pytest.fixture(scope="function")
async def async_session():
    """
    Provide an async database session for testing.

    Creates a new session for each test, automatically rolls back after test completes.
    """
    async with db_manager.get_async_session() as session:
        yield session
        # Rollback happens automatically when context manager exits


@pytest.fixture
def mock_llm_extract_screens(monkeypatch):
    """
    Mock LLM response for screen extraction (Phase 1).

    Returns deterministic screen list without calling real API.
    """
    from src.llm import client

    async def mock_complete_with_json(self, system_prompt, user_prompt, temperature=None, max_tokens=None):
        # Return mock screen extraction response
        return {
            "screens": [
                "Login Screen",
                "Registration Screen",
                "Task List Screen",
                "Task Detail Screen",
                "Create Task Screen",
                "User Profile Screen",
                "Settings Screen",
            ],
            "rationale": "Identified core authentication, task management, and user profile screens from PRD."
        }

    monkeypatch.setattr(client.LLMClient, "complete_with_json", mock_complete_with_json)


@pytest.fixture
def mock_llm_generate_options(monkeypatch):
    """
    Mock LLM response for layout options generation (Phase 2).

    Returns deterministic layout options without calling real API.
    """
    from src.llm import client

    async def mock_complete_with_json(self, system_prompt, user_prompt, temperature=None, max_tokens=None):
        # Return mock layout options response
        return {
            "screen_name": "Test Screen",
            "options": [
                {
                    "option_number": 1,
                    "layout_description": "Centered vertical layout with logo at top",
                    "key_features": ["Top brand logo", "Centered form", "CTA button"],
                    "pros": ["Clean design", "Familiar pattern"],
                    "cons": ["Less distinctive"],
                    "recommended": True
                },
                {
                    "option_number": 2,
                    "layout_description": "Split-screen design with imagery on left",
                    "key_features": ["Visual storytelling", "Asymmetric split"],
                    "pros": ["Strong branding", "Modern aesthetic"],
                    "cons": ["Requires quality imagery"],
                    "recommended": False
                },
                {
                    "option_number": 3,
                    "layout_description": "Card-based floating layout",
                    "key_features": ["Floating card", "Minimal background"],
                    "pros": ["Clean and modern"],
                    "cons": ["May feel generic"],
                    "recommended": False
                }
            ],
            "design_rationale": "Three distinct approaches balancing familiarity and innovation"
        }

    monkeypatch.setattr(client.LLMClient, "complete_with_json", mock_complete_with_json)


@pytest.fixture
def mock_llm_all_phases(monkeypatch):
    """
    Mock LLM responses for all phases.

    Provides appropriate mock responses based on the prompt content.
    """
    from src.llm import client

    async def mock_complete_with_json(self, system_prompt, user_prompt, temperature=None, max_tokens=None):
        # Detect which phase based on prompt content
        if "extract" in system_prompt.lower() or "screen" in system_prompt.lower():
            # Phase 1: Screen extraction
            return {
                "screens": [
                    "Login Screen",
                    "Registration Screen",
                    "Task List Screen",
                    "Task Detail Screen",
                    "Create Task Screen",
                    "User Profile Screen",
                    "Settings Screen",
                ],
                "rationale": "Mock screen extraction response"
            }
        elif "layout" in system_prompt.lower() or "option" in system_prompt.lower():
            # Phase 2: Layout options
            return {
                "options": [
                    {
                        "option_number": 1,
                        "layout_description": "Centered vertical layout",
                        "key_features": ["Top logo", "Form", "Button"],
                        "pros": ["Clean", "Familiar"],
                        "cons": ["Less distinctive"],
                        "recommended": True
                    },
                    {
                        "option_number": 2,
                        "layout_description": "Split-screen design",
                        "key_features": ["Visual imagery", "Asymmetric"],
                        "pros": ["Modern"],
                        "cons": ["Needs imagery"],
                        "recommended": False
                    }
                ],
                "design_rationale": "Mock layout options response"
            }
        else:
            # Default mock response
            return {"result": "mock response"}

    async def mock_complete(self, system_prompt, user_prompt, temperature=None, max_tokens=None):
        # For ASCII UI generation and refinement (Phase 3)
        if "ascii" in system_prompt.lower():
            # Return mock ASCII UI (40 chars wide for mobile)
            return """┌──────────────────────────────────────┐
│  📱 MyApp                    ☰       │
├──────────────────────────────────────┤
│                                      │
│  Welcome back!                       │
│                                      │
│  Email                               │
│  [___________________________]       │
│                                      │
│  Password                            │
│  [___________________________]       │
│                                      │
│         [    Sign In    ]            │
│                                      │
└──────────────────────────────────────┘"""
        else:
            return "Mock text response"

    monkeypatch.setattr(client.LLMClient, "complete_with_json", mock_complete_with_json)
    monkeypatch.setattr(client.LLMClient, "complete", mock_complete)


# ============================================================================
# Week 4: HTTP API Mocking for Open-Source Discovery
# ============================================================================


@pytest.fixture
def mock_github_api(monkeypatch):
    """
    Mock GitHub API search responses.

    Returns deterministic repository data without calling real GitHub API.
    """
    import httpx
    from datetime import datetime, timezone

    async def mock_get(self, url, **kwargs):
        """Mock httpx.AsyncClient.get for GitHub API."""

        class MockResponse:
            def __init__(self, json_data, status_code=200):
                self._json_data = json_data
                self.status_code = status_code

            def json(self):
                return self._json_data

            def raise_for_status(self):
                if self.status_code >= 400:
                    raise httpx.HTTPStatusError("Error", request=None, response=self)

        # Check if this is a GitHub API call
        if "api.github.com/search/repositories" in url:
            # Return mock GitHub search results
            return MockResponse({
                "total_count": 3,
                "items": [
                    {
                        "full_name": "tanstack/table",
                        "html_url": "https://github.com/tanstack/table",
                        "description": "Headless UI for building powerful tables & datagrids",
                        "stargazers_count": 22000,
                        "language": "TypeScript",
                        "license": {"spdx_id": "MIT"},
                        "updated_at": (datetime.now(timezone.utc).isoformat()),
                        "topics": ["react", "table", "typescript"],
                        "homepage": "https://tanstack.com/table"
                    },
                    {
                        "full_name": "ag-grid/ag-grid",
                        "html_url": "https://github.com/ag-grid/ag-grid",
                        "description": "The best JavaScript Data Table for building Enterprise Applications",
                        "stargazers_count": 11000,
                        "language": "TypeScript",
                        "license": {"spdx_id": "MIT"},
                        "updated_at": (datetime.now(timezone.utc).isoformat()),
                        "topics": ["datagrid", "typescript"],
                        "homepage": "https://ag-grid.com"
                    },
                    {
                        "full_name": "rsuite/rsuite-table",
                        "html_url": "https://github.com/rsuite/rsuite-table",
                        "description": "A React table component",
                        "stargazers_count": 600,
                        "language": "TypeScript",
                        "license": {"spdx_id": "MIT"},
                        "updated_at": (datetime.now(timezone.utc).isoformat()),
                        "topics": ["react", "table"],
                        "homepage": None
                    }
                ]
            })

        # Default: empty response
        return MockResponse({"items": []})

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)


@pytest.fixture
def mock_npm_api(monkeypatch):
    """
    Mock npm Registry API search responses.

    Returns deterministic package data without calling real npm API.
    """
    import httpx
    from datetime import datetime, timezone

    async def mock_get(self, url, **kwargs):
        """Mock httpx.AsyncClient.get for npm API."""

        class MockResponse:
            def __init__(self, json_data, status_code=200):
                self._json_data = json_data
                self.status_code = status_code

            def json(self):
                return self._json_data

            def raise_for_status(self):
                if self.status_code >= 400:
                    raise httpx.HTTPStatusError("Error", request=None, response=self)

        # Check if this is an npm API call
        if "registry.npmjs.org/-/v1/search" in url:
            # Return mock npm search results
            return MockResponse({
                "objects": [
                    {
                        "package": {
                            "name": "@tanstack/react-table",
                            "version": "8.10.0",
                            "description": "Hooks for building lightweight, fast and extendable datagrids for React",
                            "keywords": ["react", "table", "datagrid", "typescript"],
                            "date": datetime.now(timezone.utc).isoformat(),
                            "links": {
                                "npm": "https://www.npmjs.com/package/@tanstack/react-table",
                                "homepage": "https://tanstack.com/table",
                                "repository": "https://github.com/tanstack/table"
                            }
                        },
                        "score": {
                            "final": 0.89,
                            "detail": {
                                "quality": 0.92,
                                "popularity": 0.88,
                                "maintenance": 0.87
                            }
                        }
                    },
                    {
                        "package": {
                            "name": "react-table",
                            "version": "7.8.0",
                            "description": "Hooks for building fast and extendable tables and datagrids for React",
                            "keywords": ["react", "table", "hooks"],
                            "date": (datetime.now(timezone.utc).isoformat()),
                            "links": {
                                "npm": "https://www.npmjs.com/package/react-table",
                                "repository": "https://github.com/tanstack/react-table"
                            }
                        },
                        "score": {
                            "final": 0.75,
                            "detail": {
                                "quality": 0.78,
                                "popularity": 0.72,
                                "maintenance": 0.75
                            }
                        }
                    }
                ],
                "total": 2
            })

        # Default: empty response
        return MockResponse({"objects": []})

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)


@pytest.fixture
def mock_web_search_api(monkeypatch):
    """
    Mock web search API responses (Google/Brave).

    Returns deterministic search results without calling real search APIs.
    """
    import httpx

    async def mock_get(self, url, **kwargs):
        """Mock httpx.AsyncClient.get for web search APIs."""

        class MockResponse:
            def __init__(self, json_data, status_code=200):
                self._json_data = json_data
                self.status_code = status_code

            def json(self):
                return self._json_data

            def raise_for_status(self):
                if self.status_code >= 400:
                    raise httpx.HTTPStatusError("Error", request=None, response=self)

        # Check if this is a Google Custom Search call
        if "googleapis.com/customsearch" in url:
            return MockResponse({
                "items": [
                    {
                        "title": "Best React Table Libraries 2025",
                        "link": "https://example.com/best-react-tables",
                        "snippet": "Top data table libraries for React including TanStack Table, AG Grid..."
                    }
                ]
            })

        # Check if this is a Brave Search call
        if "api.search.brave.com" in url:
            return MockResponse({
                "web": {
                    "results": [
                        {
                            "title": "Top React Table Components",
                            "url": "https://example.com/react-table-comparison",
                            "description": "Comparison of popular React table libraries"
                        }
                    ]
                }
            })

        # Default: empty response
        return MockResponse({"items": []})

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)


@pytest.fixture
def mock_all_http_apis(monkeypatch):
    """
    Mock all HTTP APIs for Week 4 (GitHub, npm, web search).

    Comprehensive fixture that handles all external API calls.
    """
    import httpx
    from datetime import datetime, timezone

    async def mock_get(self, url, **kwargs):
        """Mock httpx.AsyncClient.get for all APIs."""

        class MockResponse:
            def __init__(self, json_data, status_code=200):
                self._json_data = json_data
                self.status_code = status_code

            def json(self):
                return self._json_data

            def raise_for_status(self):
                if self.status_code >= 400:
                    raise httpx.HTTPStatusError("Error", request=None, response=self)

        # GitHub API
        if "api.github.com/search/repositories" in url:
            return MockResponse({
                "total_count": 3,
                "items": [
                    {
                        "full_name": "tanstack/table",
                        "html_url": "https://github.com/tanstack/table",
                        "description": "Headless UI for building powerful tables",
                        "stargazers_count": 22000,
                        "language": "TypeScript",
                        "license": {"spdx_id": "MIT"},
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                        "topics": ["react", "table", "typescript"],
                        "homepage": "https://tanstack.com/table"
                    },
                    {
                        "full_name": "ag-grid/ag-grid",
                        "html_url": "https://github.com/ag-grid/ag-grid",
                        "description": "The best JavaScript Data Table",
                        "stargazers_count": 11000,
                        "language": "TypeScript",
                        "license": {"spdx_id": "MIT"},
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                        "topics": ["datagrid"],
                        "homepage": "https://ag-grid.com"
                    }
                ]
            })

        # npm API
        elif "registry.npmjs.org/-/v1/search" in url:
            return MockResponse({
                "objects": [
                    {
                        "package": {
                            "name": "@tanstack/react-table",
                            "version": "8.10.0",
                            "description": "Hooks for building datagrids for React",
                            "keywords": ["react", "table", "typescript"],
                            "date": datetime.now(timezone.utc).isoformat(),
                            "links": {
                                "npm": "https://www.npmjs.com/package/@tanstack/react-table",
                                "homepage": "https://tanstack.com/table",
                                "repository": "https://github.com/tanstack/table"
                            }
                        },
                        "score": {
                            "final": 0.89,
                            "detail": {"quality": 0.92, "popularity": 0.88, "maintenance": 0.87}
                        }
                    }
                ]
            })

        # Google Custom Search
        elif "googleapis.com/customsearch" in url:
            return MockResponse({
                "items": [{
                    "title": "Best React Table Libraries 2025",
                    "link": "https://example.com/tables",
                    "snippet": "Top table libraries..."
                }]
            })

        # Brave Search
        elif "api.search.brave.com" in url:
            return MockResponse({
                "web": {
                    "results": [{
                        "title": "React Table Components",
                        "url": "https://example.com/react-tables",
                        "description": "Comparison of table libraries"
                    }]
                }
            })

        # Default: empty response
        return MockResponse({"items": [], "objects": []})

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)


# Export fixtures
__all__ = [
    "mock_llm_extract_screens",
    "mock_llm_generate_options",
    "mock_llm_all_phases",
    "mock_github_api",
    "mock_npm_api",
    "mock_web_search_api",
    "mock_all_http_apis",
]
