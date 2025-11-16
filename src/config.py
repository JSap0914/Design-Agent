"""
Configuration management for Design Agent using Pydantic Settings.

This module loads and validates all environment variables required by the application.
"""

from typing import List, Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application Configuration
    app_name: str = Field(default="ANYON Design Agent", alias="APP_NAME")
    app_version: str = Field(default="0.1.0", alias="APP_VERSION")
    environment: Literal["development", "staging", "production"] = Field(
        default="development", alias="ENVIRONMENT"
    )
    debug: bool = Field(default=False, alias="DEBUG")
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO", alias="LOG_LEVEL"
    )

    # Database Configuration - PostgreSQL
    database_url: str = Field(..., alias="DATABASE_URL")
    database_sync_url: str = Field(..., alias="DATABASE_SYNC_URL")
    database_pool_size: int = Field(default=10, alias="DATABASE_POOL_SIZE")
    database_max_overflow: int = Field(default=20, alias="DATABASE_MAX_OVERFLOW")
    database_pool_timeout: int = Field(default=30, alias="DATABASE_POOL_TIMEOUT")
    database_echo: bool = Field(default=False, alias="DATABASE_ECHO")

    # Redis Configuration
    redis_url: str = Field(..., alias="REDIS_URL")
    redis_max_connections: int = Field(default=50, alias="REDIS_MAX_CONNECTIONS")
    redis_socket_timeout: int = Field(default=5, alias="REDIS_SOCKET_TIMEOUT")
    redis_socket_connect_timeout: int = Field(
        default=5, alias="REDIS_SOCKET_CONNECT_TIMEOUT"
    )

    # LLM Configuration - Anthropic Claude
    anthropic_api_key: str = Field(..., alias="ANTHROPIC_API_KEY")
    anthropic_model: str = Field(
        default="claude-sonnet-4-5-20250929", alias="ANTHROPIC_MODEL"
    )
    anthropic_max_tokens: int = Field(default=4096, alias="ANTHROPIC_MAX_TOKENS")
    anthropic_temperature: float = Field(default=0.7, alias="ANTHROPIC_TEMPERATURE")

    # LLM Configuration - OpenAI (Fallback)
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4-turbo-preview", alias="OPENAI_MODEL")
    openai_max_tokens: int = Field(default=4096, alias="OPENAI_MAX_TOKENS")
    openai_temperature: float = Field(default=0.7, alias="OPENAI_TEMPERATURE")

    # GitHub Configuration (for open-source search)
    github_token: str | None = Field(default=None, alias="GITHUB_TOKEN")
    github_api_url: str = Field(default="https://api.github.com", alias="GITHUB_API_URL")

    # npm Registry Configuration
    npm_registry_url: str = Field(
        default="https://registry.npmjs.org", alias="NPM_REGISTRY_URL"
    )

    # Web Search Configuration
    web_search_provider: Literal["google", "brave", "bing"] = Field(
        default="google", alias="WEB_SEARCH_PROVIDER"
    )
    google_api_key: str | None = Field(default=None, alias="GOOGLE_API_KEY")
    google_search_engine_id: str | None = Field(default=None, alias="GOOGLE_SEARCH_ENGINE_ID")

    # LangGraph Configuration
    langgraph_checkpoint_schema: str = Field(
        default="design_agent", alias="LANGGRAPH_CHECKPOINT_SCHEMA"
    )
    langgraph_max_iterations: int = Field(default=50, alias="LANGGRAPH_MAX_ITERATIONS")
    langgraph_recursion_limit: int = Field(default=100, alias="LANGGRAPH_RECURSION_LIMIT")

    # Design Agent Configuration
    max_screens: int = Field(default=12, alias="MAX_SCREENS")
    min_screens: int = Field(default=3, alias="MIN_SCREENS")
    ascii_ui_width_mobile: int = Field(default=40, alias="ASCII_UI_WIDTH_MOBILE")
    ascii_ui_width_web: int = Field(default=80, alias="ASCII_UI_WIDTH_WEB")
    max_layout_options: int = Field(default=3, alias="MAX_LAYOUT_OPTIONS")
    min_layout_options: int = Field(default=2, alias="MIN_LAYOUT_OPTIONS")
    quality_score_threshold: int = Field(default=90, alias="QUALITY_SCORE_THRESHOLD")

    # BMAD Configuration
    require_multiple_options: bool = Field(default=True, alias="REQUIRE_MULTIPLE_OPTIONS")
    require_decision_rationale: bool = Field(default=True, alias="REQUIRE_DECISION_RATIONALE")
    min_contrast_ratio: float = Field(default=4.5, alias="MIN_CONTRAST_RATIO")
    min_touch_target_size: int = Field(default=48, alias="MIN_TOUCH_TARGET_SIZE")

    # Open-Source Search Configuration
    opensearch_cache_ttl: int = Field(default=900, alias="OPENSEARCH_CACHE_TTL")
    opensearch_min_stars: int = Field(default=500, alias="OPENSEARCH_MIN_STARS")
    opensearch_max_results: int = Field(default=10, alias="OPENSEARCH_MAX_RESULTS")
    opensearch_licenses: str = Field(default="MIT,Apache-2.0", alias="OPENSEARCH_LICENSES")
    opensearch_max_bundle_size_kb: int = Field(
        default=100, alias="OPENSEARCH_MAX_BUNDLE_SIZE_KB"
    )
    opensearch_recency_months: int = Field(default=12, alias="OPENSEARCH_RECENCY_MONTHS")

    # Job Processing Configuration
    job_poll_interval: float = Field(default=1.0, alias="JOB_POLL_INTERVAL")
    job_max_retries: int = Field(default=3, alias="JOB_MAX_RETRIES")
    job_retry_delay: int = Field(default=5, alias="JOB_RETRY_DELAY")
    job_timeout: int = Field(default=3600, alias="JOB_TIMEOUT")
    progress_update_interval: int = Field(default=5, alias="PROGRESS_UPDATE_INTERVAL")

    # Document Generation Configuration
    document_version: str = Field(default="0.9", alias="DOCUMENT_VERSION")
    document_format: Literal["markdown", "html", "pdf"] = Field(
        default="markdown", alias="DOCUMENT_FORMAT"
    )
    parallel_document_generation: bool = Field(
        default=True, alias="PARALLEL_DOCUMENT_GENERATION"
    )

    # Validation Configuration
    enable_typescript_validation: bool = Field(
        default=True, alias="ENABLE_TYPESCRIPT_VALIDATION"
    )
    enable_tailwind_validation: bool = Field(default=True, alias="ENABLE_TAILWIND_VALIDATION")
    enable_accessibility_validation: bool = Field(
        default=True, alias="ENABLE_ACCESSIBILITY_VALIDATION"
    )
    enable_design_system_validation: bool = Field(
        default=True, alias="ENABLE_DESIGN_SYSTEM_VALIDATION"
    )
    validation_strict_mode: bool = Field(default=False, alias="VALIDATION_STRICT_MODE")

    # WebSocket Configuration (Optional)
    enable_websocket: bool = Field(default=False, alias="ENABLE_WEBSOCKET")
    websocket_port: int = Field(default=8000, alias="WEBSOCKET_PORT")
    websocket_path: str = Field(default="/ws", alias="WEBSOCKET_PATH")

    # API Configuration (Optional)
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    api_reload: bool = Field(default=True, alias="API_RELOAD")
    api_workers: int = Field(default=4, alias="API_WORKERS")
    api_cors_origins: str = Field(default="*", alias="API_CORS_ORIGINS")

    # Monitoring Configuration
    enable_prometheus: bool = Field(default=False, alias="ENABLE_PROMETHEUS")
    prometheus_port: int = Field(default=9090, alias="PROMETHEUS_PORT")
    enable_langsmith: bool = Field(default=False, alias="ENABLE_LANGSMITH")
    langsmith_api_key: str | None = Field(default=None, alias="LANGSMITH_API_KEY")
    langsmith_project: str = Field(default="anyon-design-agent", alias="LANGSMITH_PROJECT")

    # Security Configuration
    secret_key: str = Field(..., alias="SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_expiration_minutes: int = Field(default=60, alias="JWT_EXPIRATION_MINUTES")

    # Rate Limiting
    rate_limit_enabled: bool = Field(default=False, alias="RATE_LIMIT_ENABLED")
    rate_limit_per_minute: int = Field(default=60, alias="RATE_LIMIT_PER_MINUTE")

    # Testing Configuration
    test_database_url: str | None = Field(default=None, alias="TEST_DATABASE_URL")
    test_redis_url: str | None = Field(default=None, alias="TEST_REDIS_URL")

    # ANYON Kanban API Integration (Week 6)
    anyon_api_base_url: str = Field(
        default="http://localhost:3000/api", alias="ANYON_API_BASE_URL"
    )
    anyon_api_key: str | None = Field(default=None, alias="ANYON_API_KEY")
    anyon_api_timeout: int = Field(default=30, alias="ANYON_API_TIMEOUT")
    anyon_enable_integration: bool = Field(default=False, alias="ANYON_ENABLE_INTEGRATION")

    @field_validator("opensearch_licenses")
    @classmethod
    def parse_licenses(cls, v: str) -> List[str]:
        """Parse comma-separated licenses into a list."""
        return [license.strip() for license in v.split(",")]

    @field_validator("api_cors_origins")
    @classmethod
    def parse_cors_origins(cls, v: str) -> List[str]:
        """Parse comma-separated CORS origins into a list."""
        if v == "*":
            return ["*"]
        return [origin.strip() for origin in v.split(",")]

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == "development"

    @property
    def is_staging(self) -> bool:
        """Check if running in staging environment."""
        return self.environment == "staging"


# Global settings instance
settings = Settings()


# Export for easy import
__all__ = ["settings", "Settings"]
