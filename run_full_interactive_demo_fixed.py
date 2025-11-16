"""
Design Agent - Full Interactive Demonstration (Fixed)
Runs complete workflow with open-source library discovery and proper pause handling
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.config import settings
from src.database.connection import db_manager
from src.database.models import DesignJob, DesignOutput, DesignDecision, OpenSourceSelection
from src.langgraph.workflow import create_workflow
from src.langgraph.state import DesignAgentState
from src.langgraph.checkpointer import create_checkpointer
from sqlalchemy import select


def print_header(text, char="="):
    """Print formatted header"""
    print(f"\n{char * 80}")
    print(text)
    print(f"{char * 80}\n")


def print_section(text):
    """Print formatted section"""
    print(f"\n{'-' * 80}")
    print(text)
    print(f"{'-' * 80}\n")


def display_phase_output(node_name, state_data):
    """Display output for each phase"""

    # Phase 1: Show extracted screens
    if node_name == "extract_screens" and state_data.get("extracted_screens"):
        screens = state_data["extracted_screens"]
        print(f"[Mobile] Extracted {len(screens)} screens from PRD:\n")
        for i, screen in enumerate(screens, 1):
            print(f"   {i}. {screen}")
        print(f"\n[OK] Screen extraction complete")

    # Phase 2: Show design options
    elif node_name == "generate_options" and state_data.get("design_options"):
        options = state_data["design_options"]
        print(f"[Design] Generated design options:\n")
        for screen_name, screen_options in list(options.items())[:2]:
            print(f"\n   {screen_name}:")
            for i, opt in enumerate(screen_options, 1):
                preview = opt[:80] + "..." if len(opt) > 80 else opt
                print(f"      Option {i}: {preview}")
        print(f"\n   ... (showing 2 of {len(options)} screens)")
        print(f"\n[OK] Auto-selecting Option 1 for all screens")

    # Phase 3: Show ASCII UIs
    elif node_name == "create_ascii_ui" and state_data.get("selected_designs"):
        designs = state_data["selected_designs"]
        print(f"[UI] Created ASCII UI mockups for {len(designs)} screens\n")
        for i, (screen_name, ascii_ui) in enumerate(list(designs.items())[:2]):
            print(f"\n{'─' * 80}")
            print(f"   {screen_name}")
            print(f"{'─' * 80}\n")
            print(ascii_ui)
        if len(designs) > 2:
            print(f"\n   ... (showing 2 of {len(designs)} screens)")
        print(f"\n[OK] ASCII UI creation complete")

    # Phase 3: Refinement progress
    elif node_name == "refine_design":
        completed = state_data.get("completed_screens", 0)
        total = len(state_data.get("extracted_screens", []))
        if completed > 0:
            print(f"[OK] Refinement progress: {completed}/{total} screens approved")

    # Phase 4: Show design system
    elif node_name == "generate_design_system" and state_data.get("design_system"):
        ds = state_data["design_system"]
        print(f"[Design] Design System extracted:\n")
        if "colors" in ds:
            print(f"   Colors:")
            for color_type, color_value in list(ds["colors"].items())[:5]:
                print(f"      {color_type}: {color_value}")
        if "typography" in ds:
            print(f"\n   Typography:")
            for typo_name, typo_value in list(ds["typography"].items())[:5]:
                print(f"      {typo_name}: {typo_value}")
        if "spacing" in ds:
            print(f"\n   Spacing:")
            print(f"      Base unit: {ds['spacing'].get('base_unit', 'N/A')}")
        if "component_libraries" in ds and ds["component_libraries"]:
            print(f"\n   Component Libraries: {len(ds['component_libraries'])} selected")
        print(f"\n[OK] Design System extraction complete")

    # Phase 5: Pause
    elif node_name == "pause_for_google_ai":
        print(f"[PAUSED]  Workflow paused for manual design creation\n")
        print(f"   For this demo, skipping to document generation...")

    # Phase 6: Show documents
    elif node_name == "generate_documents" and state_data.get("generated_documents"):
        docs = state_data["generated_documents"]
        print(f"[Doc] Generated {len(docs)} documents:\n")
        for doc_type in docs.keys():
            print(f"   [OK] {doc_type}")
        print(f"\n[OK] Document generation complete")

    # Package complete
    elif node_name == "package_for_dev":
        print(f"[Package] Packaging complete - Ready for Tech Spec Agent")
        print(f"\n   Package includes:")
        print(f"   - 6 documentation files")
        print(f"   - Design decisions log")
        print(f"   - Open-source library selections")
        print(f"   - Validation report")


async def get_user_input_for_library_selection(state_data):
    """Get user input for library selection"""
    options = state_data.get("pending_library_options", [])
    query = state_data.get("pending_library_query", "")

    print(f"\n[Search] Searching for '{query}' libraries...\n")

    if not options:
        print("[WARN]  No libraries found, continuing...")
        return "skip"

    print(f"[OK] Found {len(options)} options:\n")
    for i, lib in enumerate(options[:3], 1):
        print(f"{i}. {lib.get('library_name', 'Unknown')} ⭐")
        print(f"   [Package] GitHub: {lib.get('github_url', 'N/A')}")
        print(f"   ⭐ Stars: {lib.get('stars', 0):,}")
        print(f"   [Doc] License: {lib.get('license', 'N/A')}")
        print(f"   [Size] Bundle: {lib.get('bundle_size', 'N/A')}")
        print(f"   [Score] Score: {lib.get('ranking_score', 0)}/100")
        print(f"   {lib.get('description', '')}\n")

    user_input = input("\nWhich would you like? (1, 2, 3, or 'skip'): ").strip()
    return user_input


async def get_user_input_for_feedback(state_data):
    """Get user feedback for design refinement"""
    current_screen = state_data.get("current_screen_name", "")

    print(f"\n[Mobile] Current screen: {current_screen}\n")

    current_design = state_data.get("selected_designs", {}).get(current_screen, "")
    if current_design:
        print(current_design)

    print(f"\n{'─' * 80}")
    print("Provide feedback or type 'approve' to continue")
    print("Examples:")
    print("  - 'approve' → Move to next screen")
    print("  - 'add a date picker for due date' → Triggers library search")
    print("  - 'move button to bottom' → Modifies design")
    print(f"{'─' * 80}\n")

    user_input = input("Your feedback: ").strip()
    return user_input


async def run_full_interactive_demo():
    """Run complete interactive workflow demonstration"""

    print_header("ANYON Design Agent - Full Interactive Workflow Demonstration")

    # Step 1: Load sample PRD and TRD
    print_section("Step 1: Loading Sample PRD and TRD")

    prd_path = Path("test_data/sample_prd.md")
    trd_path = Path("test_data/sample_trd.md")

    if not prd_path.exists() or not trd_path.exists():
        print(f"[ERROR] ERROR: Sample files not found!")
        print(f"   Expected: {prd_path.absolute()}")
        print(f"   Expected: {trd_path.absolute()}")
        return

    prd_content = prd_path.read_text(encoding='utf-8')
    trd_content = trd_path.read_text(encoding='utf-8')

    print(f"[OK] PRD loaded: {len(prd_content)} characters")
    print(f"[OK] TRD loaded: {len(trd_content)} characters")
    print(f"\nProject: Task Management Mobile App")
    print(f"Platform: React Native (from TRD)")
    print(f"Screens: 8 screens specified in PRD")

    # Step 2: Initialize database
    print_section("Step 2: Initializing Database")

    db_manager.initialize_async_engine()
    print("[OK] Database initialized")

    # Step 3: Create design job
    print_section("Step 3: Creating Design Job")

    async with db_manager.get_async_session() as session:
        job = DesignJob(
            project_id=f"demo-project-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            user_id="demo-user",
            prd_content=prd_content,
            trd_content=trd_content,
            status="pending"
        )
        session.add(job)
        await session.commit()
        await session.refresh(job)
        job_id = str(job.job_id)

        print(f"[OK] Job created successfully")
        print(f"   Job ID: {job_id}")
        print(f"   Project: {job.project_id}")

    # Step 4: Create initial state
    print_section("Step 4: Creating Workflow State")

    initial_state = DesignAgentState(
        job_id=job_id,
        project_id=job.project_id,
        user_id=job.user_id,
        prd_content=prd_content,
        trd_content=trd_content,
        extracted_screens=[],
        design_options={},
        selected_designs={},
        design_decisions=[],
        design_options_metadata={},
        selected_options={},
        uploaded_code=None,
        validation_results={},
        design_system={},
        generated_documents={},
        open_source_selections=[],
        current_phase=0,
        error_message=None,
        pause_for_upload=False,
        user_wants_pause=False,
        user_feedback="select option 1",
        auto_select_option_1=True,
    )

    print("[OK] Initial state created")
    print(f"   Mode: Auto-select Option 1 for design options")
    print(f"   Interactive: Library discovery enabled")

    # Step 5: Run workflow
    print_header("Step 5: Running LangGraph Workflow (Phases 1-6)", "=")

    graph = create_workflow()
    checkpointer = create_checkpointer()
    workflow = graph.compile(checkpointer=checkpointer)

    config = {
        "configurable": {
            "thread_id": f"demo-{job_id}"
        }
    }

    phase_names = {
        "extract_screens": "Phase 1: Screen Extraction",
        "generate_options": "Phase 2: Design Options Generation",
        "create_ascii_ui": "Phase 3: ASCII UI Creation",
        "refine_design": "Phase 3: Design Refinement (Interactive)",
        "generate_design_system": "Phase 4: Design System Extraction",
        "pause_for_google_ai": "Phase 5: Pause for Manual Design",
        "receive_code": "Phase 5: Code Upload",
        "validate_code": "Phase 5: Code Validation",
        "generate_documents": "Phase 6: Document Generation",
        "package_for_dev": "Phase 6: Package for Handoff",
    }

    try:
        current_state = initial_state
        final_state = None
        workflow_complete = False

        while not workflow_complete:
            # Run workflow until it pauses or completes
            async for output in workflow.astream(current_state, config):
                if not output:
                    continue

                node_name = list(output.keys())[0]
                state_data = list(output.values())[0]
                final_state = state_data

                phase_name = phase_names.get(node_name, node_name)
                print_header(phase_name)

                # Display phase-specific output
                display_phase_output(node_name, state_data)

            # Check if workflow paused for user input
            awaiting_library = final_state.get("awaiting_library_selection", False)
            awaiting_feedback = final_state.get("awaiting_feedback", False)

            if awaiting_library:
                # Get library selection from user
                user_input = await get_user_input_for_library_selection(final_state)
                # Update state and continue
                current_state = {"user_feedback": user_input}

            elif awaiting_feedback:
                # Get design feedback from user
                user_input = await get_user_input_for_feedback(final_state)
                # Update state and continue
                current_state = {"user_feedback": user_input}

            else:
                # Workflow completed
                workflow_complete = True

        print_header("Workflow Execution Complete!", "=")

    except Exception as e:
        print(f"\n[ERROR] ERROR during workflow execution:")
        print(f"   {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return

    # Step 6: Show outputs from database
    print_section("Step 6: Retrieving Outputs from Database")

    output_dir = Path("docs/output")
    output_dir.mkdir(parents=True, exist_ok=True)

    async with db_manager.get_async_session() as session:
        # Get all outputs
        result = await session.execute(
            select(DesignOutput)
            .where(DesignOutput.job_id == job_id)
            .order_by(DesignOutput.created_at)
        )
        outputs = result.scalars().all()

        if outputs:
            print(f"[Package] Generated Documents ({len(outputs)}):\n")
            for output in outputs:
                print(f"\n{'=' * 80}")
                print(f"Document: {output.document_type}")
                print(f"File: {output.file_name}")
                print(f"Size: {len(output.content):,} characters")
                print(f"{'=' * 80}")
                preview = output.content[:500]
                print(f"\n{preview}")
                if len(output.content) > 500:
                    print(f"\n... (truncated, {len(output.content) - 500:,} more characters)")

                file_path = output_dir / output.file_name
                file_path.write_text(output.content, encoding='utf-8')
                print(f"\n[Saved] Saved to: {file_path}")
        else:
            print("[WARN]  No documents found in database")

        # Get library selections
        result = await session.execute(
            select(OpenSourceSelection)
            .where(OpenSourceSelection.job_id == job_id)
            .order_by(OpenSourceSelection.created_at)
        )
        libraries = result.scalars().all()

        if libraries:
            print(f"\n\n[Library] Open-Source Library Selections ({len(libraries)}):\n")
            for lib in libraries:
                print(f"   [OK] {lib.library_name}")
                print(f"      Category: {lib.category}")
                print(f"      Stars: {lib.stars:,}")
                print(f"      Score: {lib.ranking_score}/100\n")

    # Final summary
    print_header("DEMONSTRATION COMPLETE!", "=")
    print("[OK] Summary:")
    print(f"   - Loaded PRD and TRD for Task Management App")
    print(f"   - Extracted screens from requirements")
    print(f"   - Generated design options (auto-selected Option 1)")
    print(f"   - Created ASCII UI mockups")
    print(f"   - Interactive refinement with library discovery")
    print(f"   - Extracted Design System")
    print(f"   - Generated 6 comprehensive documents")
    print(f"   - Stored all data in PostgreSQL")
    print(f"\n[Folder] Output Location: {output_dir.absolute()}")


if __name__ == "__main__":
    print("\n")
    print("=" * 80)
    print("          ANYON Design Agent - Full Demo (Fixed)                         ")
    print("=" * 80)
    print("\n")

    input("Press ENTER to start... ")

    asyncio.run(run_full_interactive_demo())
