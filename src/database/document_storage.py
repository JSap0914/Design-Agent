"""
Document storage helper for persisting generated documents to database.

Implements IMPLEMENTATION_PLAN.md Week 6 Task 6:
"Store all documents in design_outputs table"
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import DesignOutput
from src.database.connection import db_manager
from src.utils.logger import get_logger

logger = get_logger(__name__)


async def store_document(
    job_id: str,
    document_type: str,
    file_name: str,
    content: str,
    version: str = "0.9",
    metadata: Optional[dict] = None,
) -> DesignOutput:
    """
    Store a generated document in the design_outputs table.

    Args:
        job_id: Design job UUID
        document_type: Type of document (design_system, ux_flow, screen_specs, etc.)
        file_name: Name of the file (e.g., "Design_System_v0.9.md")
        content: Full document content as markdown
        version: Document version (default: "0.9")
        metadata: Optional metadata dictionary

    Returns:
        Created DesignOutput record

    Raises:
        Exception: If database insert fails
    """
    try:
        job_uuid = uuid.UUID(job_id)

        async with db_manager.get_async_session() as session:
            # Create DesignOutput record
            document = DesignOutput(
                job_id=job_uuid,
                document_type=document_type,
                file_name=file_name,
                content=content,
                version=version,
                metadata=metadata or {},
                created_at=datetime.utcnow(),
            )

            session.add(document)
            await session.commit()
            await session.refresh(document)

            logger.info(
                "Document stored in database",
                job_id=job_id,
                document_type=document_type,
                file_name=file_name,
                content_length=len(content),
            )

            return document

    except Exception as e:
        logger.error(
            f"Failed to store document in database: {e}",
            job_id=job_id,
            document_type=document_type,
        )
        raise


async def store_all_documents(
    job_id: str,
    documents: dict[str, tuple[str, str]],
    version: str = "0.9",
) -> list[DesignOutput]:
    """
    Store multiple documents in a single transaction.

    Args:
        job_id: Design job UUID
        documents: Dict of document_type -> (file_name, content)
        version: Document version

    Returns:
        List of created DesignOutput records

    Example:
        documents = {
            "design_system": ("Design_System_v0.9.md", "# Design System\\n..."),
            "ux_flow": ("UX_Flow_v0.9.md", "# UX Flow\\n..."),
            ...
        }
        results = await store_all_documents(job_id, documents)
    """
    try:
        job_uuid = uuid.UUID(job_id)
        created_documents = []

        async with db_manager.get_async_session() as session:
            for document_type, (file_name, content) in documents.items():
                document = DesignOutput(
                    job_id=job_uuid,
                    document_type=document_type,
                    file_name=file_name,
                    content=content,
                    version=version,
                    metadata={"content_length": len(content)},
                    created_at=datetime.utcnow(),
                )

                session.add(document)
                created_documents.append(document)

            await session.commit()

            # Refresh all to get database-generated IDs
            for doc in created_documents:
                await session.refresh(doc)

            logger.info(
                "All documents stored in database",
                job_id=job_id,
                document_count=len(created_documents),
            )

            return created_documents

    except Exception as e:
        logger.error(
            f"Failed to store documents in database: {e}",
            job_id=job_id,
            document_count=len(documents),
        )
        raise


async def get_document(
    job_id: str,
    document_type: str,
    version: str = "0.9",
) -> Optional[DesignOutput]:
    """
    Retrieve a document from the database.

    Args:
        job_id: Design job UUID
        document_type: Type of document
        version: Document version

    Returns:
        DesignOutput record or None if not found
    """
    try:
        from sqlalchemy import select

        job_uuid = uuid.UUID(job_id)

        async with db_manager.get_async_session() as session:
            result = await session.execute(
                select(DesignOutput).where(
                    DesignOutput.job_id == job_uuid,
                    DesignOutput.document_type == document_type,
                    DesignOutput.version == version,
                )
            )

            document = result.scalar_one_or_none()

            if document:
                logger.debug(
                    "Document retrieved from database",
                    job_id=job_id,
                    document_type=document_type,
                )

            return document

    except Exception as e:
        logger.error(
            f"Failed to retrieve document from database: {e}",
            job_id=job_id,
            document_type=document_type,
        )
        return None


async def get_all_documents(
    job_id: str,
    version: str = "0.9",
) -> list[DesignOutput]:
    """
    Retrieve all documents for a job.

    Args:
        job_id: Design job UUID
        version: Document version

    Returns:
        List of DesignOutput records
    """
    try:
        from sqlalchemy import select

        job_uuid = uuid.UUID(job_id)

        async with db_manager.get_async_session() as session:
            result = await session.execute(
                select(DesignOutput)
                .where(
                    DesignOutput.job_id == job_uuid,
                    DesignOutput.version == version,
                )
                .order_by(DesignOutput.created_at)
            )

            documents = result.scalars().all()

            logger.info(
                "All documents retrieved from database",
                job_id=job_id,
                document_count=len(documents),
            )

            return list(documents)

    except Exception as e:
        logger.error(
            f"Failed to retrieve documents from database: {e}",
            job_id=job_id,
        )
        return []


__all__ = [
    "store_document",
    "store_all_documents",
    "get_document",
    "get_all_documents",
]
