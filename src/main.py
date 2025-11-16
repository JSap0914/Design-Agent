"""
FastAPI application for Design Agent.

Provides:
- REST API endpoints for job management
- WebSocket endpoint for real-time progress updates and user feedback
- Health check and status endpoints
"""

from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import uuid

from src.database.connection import db_manager
from src.database.models import DesignJob, DesignProgress
from src.utils.logger import get_logger, configure_logging
from src.config import settings
from sqlalchemy import select
from typing import Optional

configure_logging()
logger = get_logger(__name__)


# ============================================================================
# Lifespan Context Manager (replaces deprecated startup/shutdown events)
# ============================================================================


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    logger.info("Starting Design Agent API server")
    db_manager.initialize_async_engine()
    logger.info("Database connection initialized")

    # Register WebSocket manager for progress broadcasting
    from src.workers.progress_updater import set_websocket_manager

    set_websocket_manager(manager)
    logger.info("WebSocket manager registered for real-time updates")

    yield

    # Shutdown
    logger.info("Shutting down Design Agent API server")
    await db_manager.close()
    logger.info("Database connection closed")


# ============================================================================
# FastAPI App
# ============================================================================

app = FastAPI(
    title="ANYON Design Agent API",
    description="AI-powered design automation system with real-time WebSocket updates",
    version="0.3.0",  # Week 3
    lifespan=lifespan,
)

# CORS middleware for ANYON frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Pydantic Models
# ============================================================================


class JobStatusResponse(BaseModel):
    """Job status response."""

    job_id: str
    status: str
    current_phase: int | None
    phase_name: str | None
    progress_percent: float | None
    screen_count: int | None
    completed_screens: int | None


class UserFeedbackMessage(BaseModel):
    """User feedback sent via WebSocket."""

    type: str  # "feedback" or "approval"
    screen_name: str | None
    feedback: str  # "approve", "Move button to bottom", etc.


class ProgressUpdateMessage(BaseModel):
    """Progress update sent to client via WebSocket."""

    type: str  # "progress", "ascii_ui", "error", "complete"
    job_id: str
    current_phase: int | None = None
    phase_name: str | None = None
    progress_percent: float | None = None
    screen_name: str | None = None
    ascii_ui: str | None = None
    message: str | None = None
    error: str | None = None


# ============================================================================
# WebSocket Connection Manager
# ============================================================================


class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""

    def __init__(self):
        # job_id -> list of WebSocket connections
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, job_id: str, websocket: WebSocket):
        """Register a new WebSocket connection for a job."""
        await websocket.accept()
        if job_id not in self.active_connections:
            self.active_connections[job_id] = []
        self.active_connections[job_id].append(websocket)
        logger.info(f"WebSocket connected for job {job_id}", connection_count=len(self.active_connections[job_id]))

    def disconnect(self, job_id: str, websocket: WebSocket):
        """Remove a WebSocket connection."""
        if job_id in self.active_connections:
            self.active_connections[job_id].remove(websocket)
            if not self.active_connections[job_id]:
                del self.active_connections[job_id]
            logger.info(f"WebSocket disconnected for job {job_id}")

    async def send_message(self, job_id: str, message: dict[str, Any]):
        """Send a message to all connections for a job."""
        if job_id in self.active_connections:
            disconnected = []
            for connection in self.active_connections[job_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending WebSocket message: {e}")
                    disconnected.append(connection)

            # Clean up disconnected clients
            for conn in disconnected:
                self.disconnect(job_id, conn)

    async def broadcast_progress(self, job_id: str, progress_data: dict[str, Any]):
        """Broadcast progress update to all connected clients."""
        message = ProgressUpdateMessage(
            type="progress",
            job_id=job_id,
            current_phase=progress_data.get("current_phase"),
            phase_name=progress_data.get("phase_name"),
            progress_percent=progress_data.get("progress_percent"),
            message=f"Phase {progress_data.get('current_phase')}: {progress_data.get('phase_name')}",
        )
        await self.send_message(job_id, message.model_dump())

    async def broadcast_ascii_ui(self, job_id: str, screen_name: str, ascii_ui: str):
        """Broadcast ASCII UI update to connected clients."""
        message = ProgressUpdateMessage(
            type="ascii_ui", job_id=job_id, screen_name=screen_name, ascii_ui=ascii_ui, message=f"ASCII UI for {screen_name}"
        )
        await self.send_message(job_id, message.model_dump())


manager = ConnectionManager()


# ============================================================================
# REST API Endpoints
# ============================================================================


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "healthy", "service": "Design Agent API", "version": "0.3.0"}


@app.post("/api/jobs/create")
async def create_design_job(prd_content: str, trd_content: str, project_id: Optional[str] = None):
    """
    Create a new design job.

    Week 6: ANYON integration - Creates ticket in Kanban board.

    Args:
        prd_content: Product Requirements Document content
        trd_content: Technical Requirements Document content
        project_id: Optional ANYON project ID for integration

    Returns:
        Job information including job_id and ticket_id
    """
    try:
        import uuid
        from datetime import datetime
        from src.integration.anyon_client import AnyonClient

        # Generate job ID
        job_id = str(uuid.uuid4())

        # Create job in database
        async with db_manager.get_async_session() as session:
            from src.database.models import DesignJob

            new_job = DesignJob(
                job_id=uuid.UUID(job_id),
                status="pending",
                prd_content=prd_content,
                trd_content=trd_content,
                created_at=datetime.utcnow(),
            )
            session.add(new_job)
            await session.commit()

            logger.info("Design job created", job_id=job_id)

        # Create ANYON ticket if integration enabled
        ticket_id = None
        if settings.anyon_enable_integration and project_id:
            try:
                client = AnyonClient()
                # Extract PRD title for ticket
                prd_title = prd_content.split("\n")[0][:100]  # First line, max 100 chars
                ticket_response = await client.create_design_ticket(
                    project_id=project_id, prd_title=prd_title, job_id=job_id
                )
                ticket_id = ticket_response.get("ticket_id")

                # Update job with ticket_id
                async with db_manager.get_async_session() as session:
                    job_result = await session.execute(
                        select(DesignJob).where(DesignJob.job_id == uuid.UUID(job_id))
                    )
                    job = job_result.scalar_one()
                    job.anyon_ticket_id = ticket_id
                    await session.commit()

                logger.info("ANYON ticket created", job_id=job_id, ticket_id=ticket_id)

            except Exception as e:
                logger.error(f"Failed to create ANYON ticket: {e}", job_id=job_id)

        return {
            "success": True,
            "job_id": job_id,
            "ticket_id": ticket_id,
            "status": "pending",
            "message": "Design job created successfully",
        }

    except Exception as e:
        logger.error(f"Error creating design job: {e}")
        raise HTTPException(status_code=500, detail="Failed to create design job")


@app.post("/api/jobs/{job_id}/start")
async def start_design_job(job_id: str):
    """
    Start processing a design job.

    Initiates the LangGraph workflow execution.

    Args:
        job_id: Design job ID

    Returns:
        Start confirmation
    """
    try:
        job_uuid = uuid.UUID(job_id)

        # Update job status
        async with db_manager.get_async_session() as session:
            job_result = await session.execute(select(DesignJob).where(DesignJob.job_id == job_uuid))
            job = job_result.scalar_one_or_none()

            if not job:
                raise HTTPException(status_code=404, detail="Job not found")

            job.status = "in_progress"
            await session.commit()

        # Start workflow execution (background task)
        from src.workers.job_processor import start_job_processing

        asyncio.create_task(start_job_processing(job_id))

        logger.info("Design job started", job_id=job_id)

        return {
            "success": True,
            "job_id": job_id,
            "status": "in_progress",
            "message": "Design job started successfully",
        }

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job_id format")
    except Exception as e:
        logger.error(f"Error starting design job: {e}")
        raise HTTPException(status_code=500, detail="Failed to start design job")


@app.get("/api/jobs/{job_id}/status", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """
    Get current status of a design job.

    ANYON can poll this endpoint for status updates.
    """
    try:
        job_uuid = uuid.UUID(job_id)

        async with db_manager.get_async_session() as session:
            # Get job info
            job_result = await session.execute(select(DesignJob).where(DesignJob.job_id == job_uuid))
            job = job_result.scalar_one_or_none()

            if not job:
                raise HTTPException(status_code=404, detail="Job not found")

            # Get progress info
            progress_result = await session.execute(select(DesignProgress).where(DesignProgress.job_id == job_uuid))
            progress = progress_result.scalar_one_or_none()

            return JobStatusResponse(
                job_id=str(job.job_id),
                status=job.status,
                current_phase=progress.current_phase if progress else None,
                phase_name=progress.phase_name if progress else None,
                progress_percent=progress.progress_percent if progress else None,
                screen_count=progress.screen_count if progress else None,
                completed_screens=progress.completed_screens if progress else None,
            )

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job_id format")
    except Exception as e:
        logger.error(f"Error fetching job status: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/jobs/{job_id}/package")
async def get_job_package(job_id: str):
    """
    Get completed design package information.

    Week 6: Returns package paths and download links.

    Args:
        job_id: Design job ID

    Returns:
        Package information including paths to all documents
    """
    try:
        job_uuid = uuid.UUID(job_id)

        async with db_manager.get_async_session() as session:
            job_result = await session.execute(select(DesignJob).where(DesignJob.job_id == job_uuid))
            job = job_result.scalar_one_or_none()

            if not job:
                raise HTTPException(status_code=404, detail="Job not found")

            if job.status != "completed":
                raise HTTPException(status_code=400, detail="Job not completed yet")

            # Get package information from state (stored in validation_storage)
            from src.database.validation_storage import ValidationStorage

            storage = ValidationStorage()
            state = await storage.get_job_state(job_id)

            if not state:
                raise HTTPException(status_code=404, detail="Job state not found")

            package_info = {
                "job_id": job_id,
                "status": "completed",
                "package_path": state.get("package_path"),
                "package_zip_path": state.get("package_zip_path"),
                "generated_documents": state.get("generated_documents", {}),
                "validation_report": f"{state.get('package_path')}/validation_report.md" if state.get("package_path") else None,
                "quality_score": state.get("validation_results", {}).get("quality_score", 0),
                "anyon_ticket_id": state.get("anyon_ticket_id"),
            }

            logger.info("Package info retrieved", job_id=job_id)
            return package_info

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job_id format")
    except Exception as e:
        logger.error(f"Error fetching job package: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/jobs/{job_id}/download")
async def download_job_package(job_id: str):
    """
    Download completed design package as ZIP file.

    Week 6: Provides ZIP download for all deliverables.

    Args:
        job_id: Design job ID

    Returns:
        ZIP file download
    """
    try:
        from fastapi.responses import FileResponse
        from pathlib import Path

        job_uuid = uuid.UUID(job_id)

        async with db_manager.get_async_session() as session:
            job_result = await session.execute(select(DesignJob).where(DesignJob.job_id == job_uuid))
            job = job_result.scalar_one_or_none()

            if not job:
                raise HTTPException(status_code=404, detail="Job not found")

            if job.status != "completed":
                raise HTTPException(status_code=400, detail="Job not completed yet")

            # Get ZIP path
            zip_path = Path(f"docs/generated_outputs/{job_id}/design_package_{job_id}.zip")

            if not zip_path.exists():
                raise HTTPException(status_code=404, detail="Package ZIP not found")

            logger.info("Package download requested", job_id=job_id)

            return FileResponse(
                path=str(zip_path),
                media_type="application/zip",
                filename=f"design_package_{job_id}.zip",
            )

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job_id format")
    except Exception as e:
        logger.error(f"Error downloading job package: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================================================
# WebSocket Endpoints
# ============================================================================


@app.websocket("/ws/design/{job_id}")
async def websocket_endpoint(websocket: WebSocket, job_id: str):
    """
    WebSocket endpoint for real-time design updates and user feedback.

    Flow:
    1. Client (ANYON frontend) connects with job_id
    2. Server sends real-time progress updates
    3. Server sends ASCII UI updates during Phase 3
    4. Client can send user feedback during refinement
    5. Server processes feedback and sends updated ASCII UI
    """
    await manager.connect(job_id, websocket)

    try:
        # Send initial connection confirmation
        await websocket.send_json(
            {
                "type": "connected",
                "job_id": job_id,
                "message": "WebSocket connection established. Listening for updates...",
            }
        )

        # Start listening for messages from client
        while True:
            try:
                # Wait for message from client (user feedback)
                data = await websocket.receive_json()
                message_type = data.get("type")

                if message_type == "feedback":
                    # User provided feedback during Phase 3 refinement
                    screen_name = data.get("screen_name")
                    feedback = data.get("feedback")

                    logger.info(
                        f"Received user feedback via WebSocket",
                        job_id=job_id,
                        screen_name=screen_name,
                        feedback=feedback,
                    )

                    # Send acknowledgment
                    await websocket.send_json(
                        {
                            "type": "feedback_received",
                            "job_id": job_id,
                            "screen_name": screen_name,
                            "feedback": feedback,
                            "message": f"Processing feedback: {feedback}",
                        }
                    )

                    # Resume workflow with injected feedback
                    try:
                        from src.langgraph.workflow import compile_workflow
                        from src.langgraph.checkpointer import get_checkpointer

                        workflow = compile_workflow()
                        config = {"configurable": {"thread_id": job_id}}

                        # Get current state from checkpoint
                        checkpointer = get_checkpointer()
                        current_state = await workflow.aget_state(config)

                        if current_state:
                            # Inject user feedback into state
                            updated_values = {"user_feedback": feedback}

                            # Update state and resume workflow
                            await workflow.aupdate_state(config, updated_values)

                            # Stream next step (refine_design will process feedback)
                            async for event in workflow.astream(None, config):
                                # Broadcast progress updates as workflow continues
                                if isinstance(event, dict):
                                    await manager.send_message(job_id, {"type": "workflow_event", "data": event})

                            logger.info(f"Workflow resumed with feedback for job {job_id}")
                        else:
                            logger.warning(f"No checkpoint found for job {job_id}, cannot inject feedback")

                    except Exception as feedback_error:
                        logger.error(f"Error injecting feedback: {feedback_error}")
                        await websocket.send_json(
                            {"type": "error", "job_id": job_id, "error": str(feedback_error)}
                        )

                elif message_type == "ping":
                    # Heartbeat to keep connection alive
                    await websocket.send_json({"type": "pong", "job_id": job_id})

                else:
                    logger.warning(f"Unknown WebSocket message type: {message_type}")

            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected normally for job {job_id}")
                break
            except Exception as e:
                logger.error(f"Error processing WebSocket message: {e}")
                await websocket.send_json(
                    {
                        "type": "error",
                        "job_id": job_id,
                        "error": str(e),
                        "message": "Error processing your request",
                    }
                )

    except WebSocketDisconnect:
        logger.info(f"Client disconnected from WebSocket: {job_id}")
    except Exception as e:
        logger.error(f"WebSocket error for job {job_id}: {e}")
    finally:
        manager.disconnect(job_id, websocket)


# ============================================================================
# Progress Broadcasting Helper
# ============================================================================


async def broadcast_progress_update(job_id: str, progress_data: dict[str, Any]):
    """
    Broadcast progress update to all connected WebSocket clients.

    Called by job_processor or progress_updater to send real-time updates.
    """
    await manager.broadcast_progress(job_id, progress_data)


async def broadcast_ascii_ui_update(job_id: str, screen_name: str, ascii_ui: str):
    """
    Broadcast ASCII UI update to connected clients.

    Called by create_ascii_ui or refine_design nodes.
    """
    await manager.broadcast_ascii_ui(job_id, screen_name, ascii_ui)


# ============================================================================
# Export for Workers
# ============================================================================

__all__ = ["app", "broadcast_progress_update", "broadcast_ascii_ui_update", "manager"]
