"""
PostgreSQL LISTEN/NOTIFY job listener for Design Agent.

This worker listens for new job notifications from PostgreSQL and triggers
the job processor when ANYON inserts new design jobs.
"""

import asyncio
import json
import signal
from typing import NoReturn

import asyncpg
from asyncpg import Connection

from src.config import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class JobListener:
    """
    PostgreSQL LISTEN/NOTIFY job listener.

    Listens for new design job notifications and triggers job processing.
    """

    def __init__(self) -> None:
        """Initialize job listener."""
        self.connection: Connection | None = None
        self.is_running: bool = False
        self.should_stop: bool = False

    async def connect(self) -> None:
        """
        Connect to PostgreSQL and start listening.

        Raises:
            Exception: If connection fails
        """
        try:
            logger.info("Connecting to PostgreSQL for LISTEN/NOTIFY", url=settings.database_url)

            # Parse the SQLAlchemy URL and convert to asyncpg format
            # Format: postgresql+asyncpg://user:pass@host:port/dbname -> postgresql://user:pass@host:port/dbname
            from sqlalchemy.engine.url import make_url

            parsed_url = make_url(settings.database_url)

            # Build asyncpg-compatible DSN
            # asyncpg expects: postgresql://user:password@host:port/database
            asyncpg_dsn = f"postgresql://{parsed_url.username}:{parsed_url.password}@{parsed_url.host}:{parsed_url.port or 5432}/{parsed_url.database}"

            logger.debug("Connecting to asyncpg", dsn=asyncpg_dsn.replace(parsed_url.password or '', '***'))

            self.connection = await asyncpg.connect(asyncpg_dsn)

            # Start listening on the channel
            await self.connection.add_listener("new_design_job", self._handle_notification)

            logger.info("Successfully connected and listening for new design jobs")

        except Exception as e:
            logger.error("Failed to connect to PostgreSQL", error=str(e))
            raise

    async def disconnect(self) -> None:
        """Disconnect from PostgreSQL."""
        if self.connection is not None:
            try:
                await self.connection.remove_listener("new_design_job", self._handle_notification)
                await self.connection.close()
                logger.info("Disconnected from PostgreSQL")
            except Exception as e:
                logger.error("Error during disconnect", error=str(e))
            finally:
                self.connection = None

    async def _handle_notification(
        self, connection: Connection, pid: int, channel: str, payload: str
    ) -> None:
        """
        Handle incoming job notification.

        Args:
            connection: PostgreSQL connection
            pid: Process ID that sent the notification
            channel: Channel name ('new_design_job')
            payload: JSON payload with job details
        """
        try:
            logger.info(
                "Received job notification",
                channel=channel,
                pid=pid,
                payload=payload,
            )

            # Parse JSON payload
            job_data = json.loads(payload)
            job_id = job_data.get("job_id")
            project_id = job_data.get("project_id")
            user_id = job_data.get("user_id")

            logger.info(
                "Processing new design job",
                job_id=job_id,
                project_id=project_id,
                user_id=user_id,
            )

            # Import here to avoid circular dependency
            from src.workers.job_processor import process_job

            # Trigger job processing (run in background to not block listener)
            asyncio.create_task(process_job(job_id))

        except json.JSONDecodeError as e:
            logger.error("Failed to parse notification payload", error=str(e), payload=payload)
        except Exception as e:
            logger.error("Error handling notification", error=str(e), payload=payload)

    async def run(self) -> NoReturn:
        """
        Run the job listener loop.

        This is a long-running process that listens for notifications.
        It will automatically reconnect if the connection is lost.
        """
        self.is_running = True
        self.should_stop = False

        logger.info("Starting job listener")

        while not self.should_stop:
            try:
                # Connect if not connected
                if self.connection is None or self.connection.is_closed():
                    await self.connect()

                # Keep connection alive
                await asyncio.sleep(1)

            except asyncio.CancelledError:
                logger.info("Job listener cancelled")
                break
            except Exception as e:
                logger.error(
                    "Error in job listener loop, reconnecting in 5 seconds",
                    error=str(e),
                )
                await self.disconnect()
                await asyncio.sleep(5)

        await self.disconnect()
        self.is_running = False
        logger.info("Job listener stopped")

    def stop(self) -> None:
        """Stop the job listener gracefully."""
        logger.info("Stopping job listener")
        self.should_stop = True


# Global job listener instance
job_listener = JobListener()


async def start_listener() -> None:
    """
    Start the job listener.

    This is the main entry point for running the listener as a worker.
    """
    # Setup signal handlers for graceful shutdown (Unix/Linux only)
    import sys

    if sys.platform != 'win32':
        # Unix/Linux signal handling
        loop = asyncio.get_running_loop()

        def signal_handler(sig: signal.Signals) -> None:
            logger.info("Received signal, initiating graceful shutdown", signal=sig.name)
            job_listener.stop()

        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, lambda s=sig: signal_handler(s))

        logger.info("Signal handlers registered for graceful shutdown")
    else:
        # Windows: rely on KeyboardInterrupt handling (Ctrl+C)
        logger.info("Running on Windows - use Ctrl+C for graceful shutdown")

    # Run listener
    await job_listener.run()


async def main() -> None:
    """Main entry point for running job listener directly."""
    from src.database.connection import db_manager
    from src.utils.logger import configure_logging

    # Configure logging
    configure_logging()

    # Initialize database engine
    db_manager.initialize_async_engine()

    logger.info("Design Agent Job Listener starting")

    try:
        await start_listener()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, shutting down")
    except Exception as e:
        logger.error("Fatal error in job listener", error=str(e))
        raise
    finally:
        await db_manager.close()
        logger.info("Design Agent Job Listener stopped")


if __name__ == "__main__":
    asyncio.run(main())
