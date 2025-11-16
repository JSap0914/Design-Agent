"""
Database operations for open-source library selections.

Stores selected libraries in the open_source_selections table.
"""

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import OpenSourceSelection
from src.database.connection import DatabaseManager
from src.utils.logger import get_logger

logger = get_logger(__name__)

db_manager = DatabaseManager()


async def store_library_selection(
    job_id: str | uuid.UUID,
    category: str,
    library_name: str,
    github_url: str | None = None,
    npm_url: str | None = None,
    stars: int | None = None,
    license_type: str | None = None,
    bundle_size: str | None = None,
    version: str | None = None,
    ranking_score: float | None = None,
    rationale: str = "",
    alternatives: list[dict[str, Any]] | None = None,
) -> uuid.UUID | None:
    """
    Store a library selection in the database.

    Args:
        job_id: Design job UUID
        category: Library category (ui_components, forms, etc.)
        library_name: Full library name (e.g., tanstack/table, react-day-picker)
        github_url: GitHub repository URL
        npm_url: npm package URL
        stars: GitHub stars count
        license_type: License identifier (MIT, Apache-2.0, etc.)
        bundle_size: Bundle size string (e.g., "15KB")
        version: Package version
        ranking_score: 0-100 ranking score
        rationale: Why this library was selected
        alternatives: Other options presented to user

    Returns:
        UUID of created selection record, or None if failed
    """
    try:
        # Convert job_id to UUID if string
        if isinstance(job_id, str):
            job_uuid = uuid.UUID(job_id)
        else:
            job_uuid = job_id

        async with db_manager.get_async_session() as session:
            # Create selection record
            selection = OpenSourceSelection(
                job_id=job_uuid,
                category=category,
                library_name=library_name,
                github_url=github_url,
                npm_url=npm_url,
                stars=stars,
                license=license_type,
                bundle_size=bundle_size,
                version=version,
                ranking_score=ranking_score,
                rationale=rationale,
                alternatives={"alternatives": alternatives} if alternatives else None,
            )

            session.add(selection)
            await session.commit()
            await session.refresh(selection)

            logger.info(
                f"Library selection stored in database",
                selection_id=str(selection.selection_id),
                job_id=str(job_uuid),
                library=library_name,
                category=category,
            )

            return selection.selection_id

    except Exception as e:
        logger.error(f"Failed to store library selection", error=str(e), library=library_name)
        return None


async def get_library_selections(job_id: str | uuid.UUID) -> list[dict[str, Any]]:
    """
    Get all library selections for a job.

    Args:
        job_id: Design job UUID

    Returns:
        List of library selection dictionaries
    """
    try:
        # Convert job_id to UUID if string
        if isinstance(job_id, str):
            job_uuid = uuid.UUID(job_id)
        else:
            job_uuid = job_id

        async with db_manager.get_async_session() as session:
            # Query selections
            result = await session.execute(
                select(OpenSourceSelection).where(OpenSourceSelection.job_id == job_uuid)
            )
            selections = result.scalars().all()

            # Convert to dictionaries
            selections_data = [
                {
                    "selection_id": str(sel.selection_id),
                    "category": sel.category,
                    "library_name": sel.library_name,
                    "github_url": sel.github_url,
                    "npm_url": sel.npm_url,
                    "stars": sel.stars,
                    "license": sel.license,
                    "bundle_size": sel.bundle_size,
                    "version": sel.version,
                    "ranking_score": sel.ranking_score,
                    "rationale": sel.rationale,
                    "alternatives": sel.alternatives.get("alternatives") if sel.alternatives else [],
                    "timestamp": sel.timestamp.isoformat() if sel.timestamp else None,
                }
                for sel in selections
            ]

            logger.info(
                f"Retrieved library selections",
                job_id=str(job_uuid),
                count=len(selections_data),
            )

            return selections_data

    except Exception as e:
        logger.error(f"Failed to get library selections", error=str(e), job_id=str(job_id))
        return []


async def delete_library_selection(selection_id: str | uuid.UUID) -> bool:
    """
    Delete a library selection.

    Args:
        selection_id: Selection UUID

    Returns:
        True if deleted successfully, False otherwise
    """
    try:
        # Convert to UUID if string
        if isinstance(selection_id, str):
            selection_uuid = uuid.UUID(selection_id)
        else:
            selection_uuid = selection_id

        async with db_manager.get_async_session() as session:
            # Find selection
            result = await session.execute(
                select(OpenSourceSelection).where(
                    OpenSourceSelection.selection_id == selection_uuid
                )
            )
            selection = result.scalar_one_or_none()

            if not selection:
                logger.warning(f"Selection not found for deletion", selection_id=str(selection_id))
                return False

            # Delete
            await session.delete(selection)
            await session.commit()

            logger.info(f"Library selection deleted", selection_id=str(selection_id))
            return True

    except Exception as e:
        logger.error(f"Failed to delete library selection", error=str(e), selection_id=str(selection_id))
        return False


__all__ = [
    "store_library_selection",
    "get_library_selections",
    "delete_library_selection",
]
