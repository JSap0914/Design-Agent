"""
Phase 6: Document Generation Node.

Generates 6 comprehensive documentation files in parallel:
1. Design_System_v0.9.md
2. UX_Flow_v0.9.md
3. Screen_Specifications_v0.9.md
4. Google_AI_Studio_Prompts_v0.9.md
5. Design_Guidelines_v0.9.md
6. Open_Source_Recommendations_v0.9.md

Week 6: Complete document generation for Tech Spec Agent handoff.
"""

import asyncio
from pathlib import Path
from typing import Dict
from datetime import datetime

from src.langgraph.state import DesignAgentState
from src.llm.client import generate_text_async
from src.llm.prompts import (
    DESIGN_SYSTEM_GENERATION_PROMPT,
    UX_FLOW_GENERATION_PROMPT,
    SCREEN_SPECS_GENERATION_PROMPT,
    GOOGLE_AI_PROMPTS_GENERATION_PROMPT,
    DESIGN_GUIDELINES_GENERATION_PROMPT,
    OPEN_SOURCE_RECOMMENDATIONS_GENERATION_PROMPT,
)
from src.database.document_storage import store_all_documents
from src.config import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


async def generate_design_system_document(state: DesignAgentState) -> str:
    """
    Generate Design_System_v0.9.md document.

    Includes:
    - Color palette (Primary, Secondary, Semantic)
    - Typography system (fonts, sizes, weights)
    - Spacing system (8pt grid)
    - Border radius, shadows, icon style guide
    - Open-source component libraries section
    """
    logger.info("Generating Design System document", job_id=state["job_id"])

    design_system = state.get("design_system", {})
    selected_libraries = state.get("selected_open_source", [])

    prompt = DESIGN_SYSTEM_GENERATION_PROMPT.format(
        design_system=design_system,
        selected_libraries=selected_libraries,
        version=settings.document_version,
    )

    content = await generate_text_async(prompt)
    logger.info("Design System document generated", job_id=state["job_id"])
    return content


async def generate_ux_flow_document(state: DesignAgentState) -> str:
    """
    Generate UX_Flow_v0.9.md document.

    Includes:
    - Screen sitemap and navigation flows
    - User actions → System responses
    - Edge cases (loading, error, empty, offline)
    """
    logger.info("Generating UX Flow document", job_id=state["job_id"])

    extracted_screens = state.get("extracted_screens", [])
    selected_designs = state.get("selected_designs", {})
    design_decisions = state.get("design_decisions", [])

    prompt = UX_FLOW_GENERATION_PROMPT.format(
        extracted_screens=extracted_screens,
        selected_designs=selected_designs,
        design_decisions=design_decisions,
        version=settings.document_version,
    )

    content = await generate_text_async(prompt)
    logger.info("UX Flow document generated", job_id=state["job_id"])
    return content


async def generate_screen_specifications_document(state: DesignAgentState) -> str:
    """
    Generate Screen_Specifications_v0.9.md document.

    Includes:
    - Final ASCII UI for each screen
    - Layout structure with measurements
    - Element details (sizes, colors, spacing)
    - Interaction specifications and state variations
    - Design decision logs
    - Implementation libraries per screen
    """
    logger.info("Generating Screen Specifications document", job_id=state["job_id"])

    selected_designs = state.get("selected_designs", {})
    design_decisions = state.get("design_decisions", [])
    design_system = state.get("design_system", {})
    selected_libraries = state.get("selected_open_source", [])

    prompt = SCREEN_SPECS_GENERATION_PROMPT.format(
        selected_designs=selected_designs,
        design_decisions=design_decisions,
        design_system=design_system,
        selected_libraries=selected_libraries,
        version=settings.document_version,
    )

    content = await generate_text_async(prompt)
    logger.info("Screen Specifications document generated", job_id=state["job_id"])
    return content


async def generate_google_ai_prompts_document(state: DesignAgentState) -> str:
    """
    Generate Google_AI_Studio_Prompts_v0.9.md document.

    Includes:
    - Screen-by-screen generation prompts
    - Visual style specifications
    - Expected outputs for manual design phase
    """
    logger.info("Generating Google AI Studio Prompts document", job_id=state["job_id"])

    selected_designs = state.get("selected_designs", {})
    design_system = state.get("design_system", {})

    prompt = GOOGLE_AI_PROMPTS_GENERATION_PROMPT.format(
        selected_designs=selected_designs,
        design_system=design_system,
        version=settings.document_version,
    )

    content = await generate_text_async(prompt)
    logger.info("Google AI Studio Prompts document generated", job_id=state["job_id"])
    return content


async def generate_design_guidelines_document(state: DesignAgentState) -> str:
    """
    Generate Design_Guidelines_v0.9.md document.

    Includes:
    - Design philosophy
    - Accessibility standards (WCAG AA)
    - Responsive principles
    - Animation guidelines
    - Dark mode policy
    - Open-source usage guidelines
    """
    logger.info("Generating Design Guidelines document", job_id=state["job_id"])

    design_system = state.get("design_system", {})
    design_decisions = state.get("design_decisions", [])

    prompt = DESIGN_GUIDELINES_GENERATION_PROMPT.format(
        design_system=design_system,
        design_decisions=design_decisions,
        version=settings.document_version,
    )

    content = await generate_text_async(prompt)
    logger.info("Design Guidelines document generated", job_id=state["job_id"])
    return content


async def generate_open_source_recommendations_document(state: DesignAgentState) -> str:
    """
    Generate Open_Source_Recommendations_v0.9.md document.

    Includes:
    - Category-based library recommendations (UI, Auth, Forms, Icons, etc.)
    - Detailed library information (GitHub stars, license, bundle size)
    - Selection rationale and decision logs
    - Installation scripts and dependency management
    - Version management guidelines
    """
    logger.info("Generating Open Source Recommendations document", job_id=state["job_id"])

    selected_libraries = state.get("selected_open_source", [])
    library_search_logs = state.get("library_search_logs", [])

    prompt = OPEN_SOURCE_RECOMMENDATIONS_GENERATION_PROMPT.format(
        selected_libraries=selected_libraries,
        library_search_logs=library_search_logs,
        version=settings.document_version,
    )

    content = await generate_text_async(prompt)
    logger.info("Open Source Recommendations document generated", job_id=state["job_id"])
    return content


async def save_document(file_path: Path, content: str) -> None:
    """
    Save generated document to file.

    Args:
        file_path: Path to save document
        content: Document content
    """
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    logger.debug(f"Document saved: {file_path}")


async def generate_documents(state: DesignAgentState) -> DesignAgentState:
    """
    Phase 6: Generate all 6 documentation files in parallel.

    Strategy:
    - Use asyncio.gather() for parallel generation (5-10x faster)
    - LLM client supports async operations
    - Save all documents to docs/generated_outputs/

    Updates state:
    - generated_documents: Dict[str, str] (doc_type -> file_path)
    - current_phase: 6
    - phase_name: "Document Generation"

    Args:
        state: Current workflow state

    Returns:
        Updated state with generated documents
    """
    logger.info("=== Phase 6: Document Generation ===", job_id=state["job_id"])

    try:
        # Parallel document generation using asyncio.gather()
        if settings.parallel_document_generation:
            logger.info("Generating 6 documents in parallel...", job_id=state["job_id"])

            results = await asyncio.gather(
                generate_design_system_document(state),
                generate_ux_flow_document(state),
                generate_screen_specifications_document(state),
                generate_google_ai_prompts_document(state),
                generate_design_guidelines_document(state),
                generate_open_source_recommendations_document(state),
                return_exceptions=True,
            )

            # Check for errors
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Document generation failed for document {i}: {result}")
                    raise result

            (
                design_system_content,
                ux_flow_content,
                screen_specs_content,
                google_ai_prompts_content,
                design_guidelines_content,
                open_source_recommendations_content,
            ) = results

        else:
            # Sequential generation (slower, for debugging)
            logger.info("Generating 6 documents sequentially...", job_id=state["job_id"])

            design_system_content = await generate_design_system_document(state)
            ux_flow_content = await generate_ux_flow_document(state)
            screen_specs_content = await generate_screen_specifications_document(state)
            google_ai_prompts_content = await generate_google_ai_prompts_document(state)
            design_guidelines_content = await generate_design_guidelines_document(state)
            open_source_recommendations_content = await generate_open_source_recommendations_document(state)

        # Save all documents
        job_id = state["job_id"]
        output_dir = Path(f"docs/generated_outputs/{job_id}")
        version = settings.document_version

        document_paths = {
            "design_system": output_dir / f"Design_System_v{version}.md",
            "ux_flow": output_dir / f"UX_Flow_v{version}.md",
            "screen_specifications": output_dir / f"Screen_Specifications_v{version}.md",
            "google_ai_prompts": output_dir / f"Google_AI_Studio_Prompts_v{version}.md",
            "design_guidelines": output_dir / f"Design_Guidelines_v{version}.md",
            "open_source_recommendations": output_dir / f"Open_Source_Recommendations_v{version}.md",
        }

        # Save all documents to filesystem in parallel
        await asyncio.gather(
            save_document(document_paths["design_system"], design_system_content),
            save_document(document_paths["ux_flow"], ux_flow_content),
            save_document(document_paths["screen_specifications"], screen_specs_content),
            save_document(document_paths["google_ai_prompts"], google_ai_prompts_content),
            save_document(document_paths["design_guidelines"], design_guidelines_content),
            save_document(document_paths["open_source_recommendations"], open_source_recommendations_content),
        )

        # Persist documents to database (IMPLEMENTATION_PLAN.md Week 6 Task 6)
        documents_for_db = {
            "design_system": (f"Design_System_v{version}.md", design_system_content),
            "ux_flow": (f"UX_Flow_v{version}.md", ux_flow_content),
            "screen_specifications": (f"Screen_Specifications_v{version}.md", screen_specs_content),
            "google_ai_prompts": (f"Google_AI_Studio_Prompts_v{version}.md", google_ai_prompts_content),
            "design_guidelines": (f"Design_Guidelines_v{version}.md", design_guidelines_content),
            "open_source_recommendations": (f"Open_Source_Recommendations_v{version}.md", open_source_recommendations_content),
        }

        await store_all_documents(job_id, documents_for_db, version)
        logger.info("All documents persisted to database", job_id=job_id)

        # Convert paths to strings for state serialization
        generated_documents = {key: str(path) for key, path in document_paths.items()}

        logger.info(
            "✅ Phase 6 complete: All 6 documents generated and stored",
            job_id=state["job_id"],
            output_dir=str(output_dir),
        )

        return {
            **state,
            "generated_documents": generated_documents,
            "current_phase": 6,
            "phase_name": "Document Generation",
        }

    except Exception as e:
        logger.error(f"Document generation failed: {e}", job_id=state["job_id"])
        return {
            **state,
            "error": f"Document generation failed: {str(e)}",
            "current_phase": 6,
            "phase_name": "Document Generation (Failed)",
        }


__all__ = ["generate_documents"]
