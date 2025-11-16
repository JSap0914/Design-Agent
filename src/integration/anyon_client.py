"""
ANYON Kanban API Client.

Provides integration with ANYON platform for ticket management and status updates.

Week 6: ANYON Platform Integration
- Creates design tickets: "Design in Progress"
- Updates ticket status during phases
- Attaches completed documentation
- Marks "Design Complete" with package handoff
"""

import aiohttp
from typing import Any, Dict, Optional
from pathlib import Path

from src.config import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class AnyonClient:
    """
    Client for interacting with ANYON Kanban API.

    Handles:
    - Creating new design tickets
    - Updating ticket status
    - Uploading attachments (6 documents + validated code)
    - Marking tickets complete for Tech Spec Agent handoff
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: int = 30,
    ):
        """
        Initialize ANYON API client.

        Args:
            base_url: ANYON API base URL (defaults to config)
            api_key: API authentication key (defaults to config)
            timeout: Request timeout in seconds
        """
        self.base_url = base_url or settings.anyon_api_base_url
        self.api_key = api_key or settings.anyon_api_key
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.enabled = settings.anyon_enable_integration

        logger.info(
            "ANYON client initialized",
            base_url=self.base_url,
            enabled=self.enabled,
        )

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make HTTP request to ANYON API.

        Args:
            method: HTTP method (GET, POST, PUT, PATCH)
            endpoint: API endpoint path
            data: JSON payload
            files: Files to upload

        Returns:
            API response as dictionary

        Raises:
            aiohttp.ClientError: On request failure
        """
        if not self.enabled:
            logger.warning("ANYON integration disabled, skipping request")
            return {"success": False, "message": "Integration disabled"}

        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = {}

        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                if files:
                    # Use multipart/form-data for file uploads
                    form_data = aiohttp.FormData()
                    if data:
                        for key, value in data.items():
                            form_data.add_field(key, str(value))
                    for file_key, file_info in files.items():
                        form_data.add_field(
                            file_key,
                            file_info["content"],
                            filename=file_info["filename"],
                            content_type=file_info.get("content_type", "text/plain"),
                        )

                    async with session.request(
                        method, url, data=form_data, headers=headers
                    ) as response:
                        response.raise_for_status()
                        return await response.json()
                else:
                    # Regular JSON request
                    headers["Content-Type"] = "application/json"
                    async with session.request(
                        method, url, json=data, headers=headers
                    ) as response:
                        response.raise_for_status()
                        return await response.json()

        except aiohttp.ClientError as e:
            logger.error(f"ANYON API request failed: {e}", url=url, method=method)
            raise

    async def create_design_ticket(
        self,
        project_id: str,
        prd_title: str,
        job_id: str,
    ) -> Dict[str, Any]:
        """
        Create new design ticket in ANYON Kanban.

        Initial status: "Design in Progress"

        Args:
            project_id: ANYON project ID
            prd_title: Title from PRD document
            job_id: Design Agent job ID

        Returns:
            Created ticket information
        """
        data = {
            "project_id": project_id,
            "title": f"Design: {prd_title}",
            "status": "design_in_progress",
            "type": "design",
            "metadata": {
                "design_agent_job_id": job_id,
                "phase": 1,
                "phase_name": "Screen Extraction",
            },
        }

        response = await self._make_request("POST", "/tickets", data=data)
        logger.info(
            "Design ticket created",
            project_id=project_id,
            ticket_id=response.get("ticket_id"),
            job_id=job_id,
        )
        return response

    async def update_ticket_status(
        self,
        ticket_id: str,
        status: str,
        phase: int,
        phase_name: str,
        progress_percent: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Update design ticket status with current phase information.

        Args:
            ticket_id: ANYON ticket ID
            status: Ticket status (design_in_progress, paused, design_complete)
            phase: Current phase number (1-6)
            phase_name: Human-readable phase name
            progress_percent: Optional progress percentage (0-100)

        Returns:
            Updated ticket information
        """
        data = {
            "status": status,
            "metadata": {
                "phase": phase,
                "phase_name": phase_name,
                "progress_percent": progress_percent,
            },
        }

        response = await self._make_request("PATCH", f"/tickets/{ticket_id}", data=data)
        logger.info(
            "Ticket status updated",
            ticket_id=ticket_id,
            status=status,
            phase=phase,
            phase_name=phase_name,
        )
        return response

    async def attach_document(
        self,
        ticket_id: str,
        file_path: Path,
        document_type: str,
    ) -> Dict[str, Any]:
        """
        Attach a document to design ticket.

        Args:
            ticket_id: ANYON ticket ID
            file_path: Path to document file
            document_type: Type of document (design_system, ux_flow, etc.)

        Returns:
            Attachment confirmation
        """
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        files = {
            "file": {
                "content": content,
                "filename": file_path.name,
                "content_type": "text/markdown",
            }
        }

        data = {"document_type": document_type}

        response = await self._make_request(
            "POST", f"/tickets/{ticket_id}/attachments", data=data, files=files
        )
        logger.info(
            "Document attached",
            ticket_id=ticket_id,
            file_name=file_path.name,
            document_type=document_type,
        )
        return response

    async def complete_design_ticket(
        self,
        ticket_id: str,
        job_id: str,
        quality_score: int,
        documents: Dict[str, Path],
    ) -> Dict[str, Any]:
        """
        Mark design ticket complete and attach all 6 documents.

        Final status: "Design Complete"
        Prepares handoff to Tech Spec Agent.

        Args:
            ticket_id: ANYON ticket ID
            job_id: Design Agent job ID
            quality_score: Final quality score (0-100)
            documents: Dictionary of document type -> file path

        Returns:
            Completion confirmation
        """
        # First, attach all documents
        for doc_type, file_path in documents.items():
            await self.attach_document(ticket_id, file_path, doc_type)

        # Mark ticket complete
        data = {
            "status": "design_complete",
            "metadata": {
                "design_agent_job_id": job_id,
                "quality_score": quality_score,
                "phase": 6,
                "phase_name": "Complete",
                "documents_attached": list(documents.keys()),
                "ready_for_tech_spec": True,
            },
        }

        response = await self._make_request("PATCH", f"/tickets/{ticket_id}", data=data)
        logger.info(
            "Design ticket marked complete",
            ticket_id=ticket_id,
            job_id=job_id,
            quality_score=quality_score,
            documents_count=len(documents),
        )
        return response

    async def pause_design_ticket(
        self,
        ticket_id: str,
        reason: str = "Awaiting Google AI Studio design creation",
    ) -> Dict[str, Any]:
        """
        Pause design ticket (waiting for manual design work).

        Status: "paused"

        Args:
            ticket_id: ANYON ticket ID
            reason: Reason for pause

        Returns:
            Pause confirmation
        """
        data = {
            "status": "paused",
            "metadata": {
                "pause_reason": reason,
                "phase": 5,
                "phase_name": "Paused for Manual Design",
            },
        }

        response = await self._make_request("PATCH", f"/tickets/{ticket_id}", data=data)
        logger.info("Design ticket paused", ticket_id=ticket_id, reason=reason)
        return response

    async def resume_design_ticket(
        self,
        ticket_id: str,
    ) -> Dict[str, Any]:
        """
        Resume paused design ticket.

        Status: "design_in_progress"

        Args:
            ticket_id: ANYON ticket ID

        Returns:
            Resume confirmation
        """
        data = {
            "status": "design_in_progress",
            "metadata": {
                "phase": 5,
                "phase_name": "Code Validation",
            },
        }

        response = await self._make_request("PATCH", f"/tickets/{ticket_id}", data=data)
        logger.info("Design ticket resumed", ticket_id=ticket_id)
        return response

    async def get_ticket_status(
        self,
        ticket_id: str,
    ) -> Dict[str, Any]:
        """
        Get current ticket status.

        Args:
            ticket_id: ANYON ticket ID

        Returns:
            Ticket information
        """
        response = await self._make_request("GET", f"/tickets/{ticket_id}")
        logger.debug("Ticket status retrieved", ticket_id=ticket_id)
        return response


__all__ = ["AnyonClient"]
