"""
Database connection management for Design Agent.

This module provides async database connection pooling and session management
using SQLAlchemy 2.0+ async API with asyncpg driver.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy import create_engine, event
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool, QueuePool

from src.config import settings
from src.database.models import Base
from src.utils.logger import get_logger

logger = get_logger(__name__)


class DatabaseManager:
    """
    Manages database connections and sessions.

    Provides async connection pooling and session management for PostgreSQL.
    """

    def __init__(self) -> None:
        """Initialize database manager."""
        self._async_engine: AsyncEngine | None = None
        self._async_session_factory: async_sessionmaker[AsyncSession] | None = None
        self._sync_engine: create_engine | None = None
        self._sync_session_factory: sessionmaker | None = None

    def initialize_async_engine(self) -> None:
        """
        Initialize async database engine and session factory.

        Uses asyncpg driver for async operations.
        """
        if self._async_engine is not None:
            logger.warning("Async engine already initialized")
            return

        logger.info("Initializing async database engine", database_url=settings.database_url)

        # Create async engine
        # Note: QueuePool is for sync engines. Async engines use NullPool or AsyncAdaptedQueuePool automatically
        self._async_engine = create_async_engine(
            settings.database_url,
            echo=settings.database_echo,
            pool_size=settings.database_pool_size,
            max_overflow=settings.database_max_overflow,
            pool_timeout=settings.database_pool_timeout,
            pool_pre_ping=True,  # Verify connections before using
            # poolclass is omitted - SQLAlchemy picks the right async pool automatically
        )

        # Create async session factory
        self._async_session_factory = async_sessionmaker(
            bind=self._async_engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )

        logger.info("Async database engine initialized successfully")

    def initialize_sync_engine(self) -> None:
        """
        Initialize sync database engine and session factory.

        Used for Alembic migrations and sync operations.
        """
        if self._sync_engine is not None:
            logger.warning("Sync engine already initialized")
            return

        logger.info("Initializing sync database engine", database_url=settings.database_sync_url)

        # Create sync engine
        self._sync_engine = create_engine(
            settings.database_sync_url,
            echo=settings.database_echo,
            pool_size=settings.database_pool_size,
            max_overflow=settings.database_max_overflow,
            pool_timeout=settings.database_pool_timeout,
            pool_pre_ping=True,
            poolclass=QueuePool,
        )

        # Create sync session factory
        self._sync_session_factory = sessionmaker(
            bind=self._sync_engine,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
        )

        logger.info("Sync database engine initialized successfully")

    @asynccontextmanager
    async def get_async_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Get async database session as async context manager.

        Usage:
            async with db_manager.get_async_session() as session:
                result = await session.execute(query)

        Yields:
            AsyncSession: Async database session
        """
        if self._async_session_factory is None:
            raise RuntimeError("Async engine not initialized. Call initialize_async_engine() first.")

        async with self._async_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    def get_sync_session(self) -> sessionmaker:
        """
        Get sync database session factory.

        Used for Alembic migrations and sync operations.

        Returns:
            sessionmaker: Sync session factory
        """
        if self._sync_session_factory is None:
            raise RuntimeError("Sync engine not initialized. Call initialize_sync_engine() first.")

        return self._sync_session_factory

    @property
    def async_engine(self) -> AsyncEngine:
        """
        Get async database engine.

        Returns:
            AsyncEngine: Async database engine
        """
        if self._async_engine is None:
            raise RuntimeError("Async engine not initialized. Call initialize_async_engine() first.")

        return self._async_engine

    @property
    def sync_engine(self) -> create_engine:
        """
        Get sync database engine.

        Returns:
            Engine: Sync database engine
        """
        if self._sync_engine is None:
            raise RuntimeError("Sync engine not initialized. Call initialize_sync_engine() first.")

        return self._sync_engine

    async def create_all_tables(self) -> None:
        """
        Create all database tables.

        Warning: Only use in development. Use Alembic migrations in production.
        """
        logger.warning("Creating all database tables (development only)")

        async with self._async_engine.begin() as conn:
            # Create schemas first
            await conn.execute("CREATE SCHEMA IF NOT EXISTS shared")
            await conn.execute("CREATE SCHEMA IF NOT EXISTS design_agent")

            # Create all tables
            await conn.run_sync(Base.metadata.create_all)

        logger.info("All database tables created successfully")

    async def drop_all_tables(self) -> None:
        """
        Drop all database tables.

        Warning: Destructive operation. Use with caution.
        """
        logger.warning("Dropping all database tables")

        async with self._async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

        logger.info("All database tables dropped successfully")

    async def close(self) -> None:
        """Close all database connections."""
        if self._async_engine is not None:
            await self._async_engine.dispose()
            logger.info("Async database engine disposed")

        if self._sync_engine is not None:
            self._sync_engine.dispose()
            logger.info("Sync database engine disposed")


# Global database manager instance
db_manager = DatabaseManager()


# Dependency injection for FastAPI
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency for database sessions.

    Usage:
        @app.get("/endpoint")
        async def endpoint(db: AsyncSession = Depends(get_db_session)):
            result = await db.execute(query)

    Yields:
        AsyncSession: Async database session
    """
    async with db_manager.get_async_session() as session:
        yield session


# Export for easy import
__all__ = ["db_manager", "get_db_session", "DatabaseManager"]
