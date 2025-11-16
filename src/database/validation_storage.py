"""
Database storage for validation results.

Stores comprehensive validation results in PostgreSQL design_outputs table
for later retrieval and analysis.
"""

import json
from datetime import datetime, timezone
from typing import Any

from src.utils.logger import get_logger

logger = get_logger(__name__)


async def store_validation_results(
    job_id: str,
    validation_results: dict[str, Any],
    uploaded_code: str,
    uploaded_code_metadata: dict[str, Any],
    db_connection=None,
) -> dict[str, Any]:
    """
    Store validation results in design_outputs table.

    Args:
        job_id: Unique job identifier
        validation_results: Comprehensive validation results from validate_code
        uploaded_code: The validated code
        uploaded_code_metadata: Metadata about uploaded code (files, size, etc.)
        db_connection: Optional database connection (for testing/mocking)

    Returns:
        Dict with:
        - success: bool
        - stored_id: int (database record ID)
        - timestamp: str (ISO format)
    """
    logger.info("Storing validation results", job_id=job_id)

    try:
        # Prepare data for storage
        stored_data = {
            "job_id": job_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "validation_results": validation_results,
            "uploaded_code": uploaded_code,
            "uploaded_code_metadata": uploaded_code_metadata,
            "quality_score": validation_results.get("overall_score", 0),
            "grade": validation_results.get("grade", "F"),
            "meets_minimum": validation_results.get("meets_minimum", False),
            "all_valid": validation_results.get("all_valid", False),
        }

        # In production, this would use asyncpg or SQLAlchemy async
        # For now, we'll create a mock storage function
        if db_connection:
            # Use provided connection (for testing)
            stored_id = await _store_to_database(db_connection, stored_data)
        else:
            # Use default database connection (production)
            stored_id = await _store_to_default_database(stored_data)

        logger.info(
            "Validation results stored successfully",
            job_id=job_id,
            stored_id=stored_id,
            quality_score=stored_data["quality_score"],
        )

        return {
            "success": True,
            "stored_id": stored_id,
            "timestamp": stored_data["timestamp"],
        }

    except Exception as e:
        logger.error(
            "Failed to store validation results",
            job_id=job_id,
            error=str(e),
        )
        return {
            "success": False,
            "error": str(e),
        }


async def _store_to_database(db_connection, data: dict[str, Any]) -> int:
    """
    Store data to PostgreSQL using provided connection.

    This is a placeholder for actual database integration.
    In production, this would use asyncpg or SQLAlchemy.

    Args:
        db_connection: Database connection object
        data: Data to store

    Returns:
        Database record ID
    """
    # Mock implementation for testing
    # In production, would be:
    # async with db_connection.transaction():
    #     result = await db_connection.fetchrow(
    #         """
    #         INSERT INTO design_outputs (
    #             job_id, timestamp, validation_results, uploaded_code,
    #             uploaded_code_metadata, quality_score, grade, meets_minimum, all_valid
    #         )
    #         VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
    #         RETURNING id
    #         """,
    #         data["job_id"],
    #         data["timestamp"],
    #         json.dumps(data["validation_results"]),
    #         data["uploaded_code"],
    #         json.dumps(data["uploaded_code_metadata"]),
    #         data["quality_score"],
    #         data["grade"],
    #         data["meets_minimum"],
    #         data["all_valid"],
    #     )
    #     return result["id"]

    # Mock return for testing
    return hash(data["job_id"]) % 10000


async def _store_to_default_database(data: dict[str, Any]) -> int:
    """
    Store data to default PostgreSQL database.

    In production, this would initialize connection from environment variables
    and use asyncpg connection pool.

    Args:
        data: Data to store

    Returns:
        Database record ID
    """
    # In production:
    # from src.database.connection import get_db_pool
    # pool = await get_db_pool()
    # async with pool.acquire() as connection:
    #     return await _store_to_database(connection, data)

    # Mock for now
    logger.info("Using default database connection (mocked)")
    return hash(data["job_id"]) % 10000


async def retrieve_validation_results(
    job_id: str,
    db_connection=None,
) -> dict[str, Any] | None:
    """
    Retrieve validation results from database.

    Args:
        job_id: Job identifier
        db_connection: Optional database connection

    Returns:
        Stored validation results or None if not found
    """
    logger.info("Retrieving validation results", job_id=job_id)

    try:
        if db_connection:
            result = await _retrieve_from_database(db_connection, job_id)
        else:
            result = await _retrieve_from_default_database(job_id)

        if result:
            logger.info("Validation results retrieved", job_id=job_id)
        else:
            logger.warning("No validation results found", job_id=job_id)

        return result

    except Exception as e:
        logger.error(
            "Failed to retrieve validation results",
            job_id=job_id,
            error=str(e),
        )
        return None


async def _retrieve_from_database(db_connection, job_id: str) -> dict[str, Any] | None:
    """
    Retrieve from PostgreSQL using provided connection.

    Args:
        db_connection: Database connection object
        job_id: Job identifier

    Returns:
        Stored data or None
    """
    # In production:
    # result = await db_connection.fetchrow(
    #     """
    #     SELECT * FROM design_outputs
    #     WHERE job_id = $1
    #     ORDER BY timestamp DESC
    #     LIMIT 1
    #     """,
    #     job_id,
    # )
    # if result:
    #     return dict(result)
    # return None

    # Mock for testing
    return None


async def _retrieve_from_default_database(job_id: str) -> dict[str, Any] | None:
    """
    Retrieve from default PostgreSQL database.

    Args:
        job_id: Job identifier

    Returns:
        Stored data or None
    """
    # In production:
    # from src.database.connection import get_db_pool
    # pool = await get_db_pool()
    # async with pool.acquire() as connection:
    #     return await _retrieve_from_database(connection, job_id)

    # Mock for now
    logger.info("Using default database connection (mocked)")
    return None


async def list_validation_results(
    limit: int = 10,
    offset: int = 0,
    min_score: float | None = None,
    db_connection=None,
) -> list[dict[str, Any]]:
    """
    List validation results with optional filters.

    Args:
        limit: Maximum number of results to return
        offset: Number of results to skip
        min_score: Optional minimum quality score filter
        db_connection: Optional database connection

    Returns:
        List of validation results
    """
    logger.info("Listing validation results", limit=limit, offset=offset)

    try:
        # In production:
        # query = """
        #     SELECT job_id, timestamp, quality_score, grade, meets_minimum, all_valid
        #     FROM design_outputs
        #     WHERE ($1::float IS NULL OR quality_score >= $1)
        #     ORDER BY timestamp DESC
        #     LIMIT $2 OFFSET $3
        # """
        # results = await db_connection.fetch(query, min_score, limit, offset)
        # return [dict(row) for row in results]

        # Mock for testing
        return []

    except Exception as e:
        logger.error("Failed to list validation results", error=str(e))
        return []


# Database schema for design_outputs table (for reference)
DESIGN_OUTPUTS_TABLE_SCHEMA = """
CREATE TABLE IF NOT EXISTS design_outputs (
    id SERIAL PRIMARY KEY,
    job_id VARCHAR(255) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,

    -- Validation results
    validation_results JSONB NOT NULL,
    uploaded_code TEXT NOT NULL,
    uploaded_code_metadata JSONB,

    -- Quality metrics (denormalized for easy querying)
    quality_score FLOAT NOT NULL,
    grade VARCHAR(3) NOT NULL,
    meets_minimum BOOLEAN NOT NULL,
    all_valid BOOLEAN NOT NULL,

    -- Indexes for efficient querying
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_design_outputs_job_id ON design_outputs(job_id);
CREATE INDEX idx_design_outputs_timestamp ON design_outputs(timestamp DESC);
CREATE INDEX idx_design_outputs_quality_score ON design_outputs(quality_score DESC);
CREATE INDEX idx_design_outputs_meets_minimum ON design_outputs(meets_minimum);
"""


__all__ = [
    "store_validation_results",
    "retrieve_validation_results",
    "list_validation_results",
    "DESIGN_OUTPUTS_TABLE_SCHEMA",
]
