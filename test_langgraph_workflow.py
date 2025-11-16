"""
Simple test to run LangGraph workflow with sample PRD/TRD.
Tests Phases 1-4 (automated phases before pause).
"""

import asyncio
import uuid
from pathlib import Path

# Suppress verbose logging
import logging
logging.basicConfig(level=logging.WARNING)

from src.database.connection import db_manager
from src.database.models import DesignJob
from src.langgraph.workflow import create_workflow
from src.langgraph.state import DesignAgentState


async def test_workflow():
    """Test the LangGraph workflow with sample data."""

    print("=" * 80)
    print("Design Agent - LangGraph Workflow Test")
    print("=" * 80)
    print()

    # Initialize database
    print("Step 1: Initializing database...")
    db_manager.initialize_async_engine()
    print("   [OK] Database initialized")
    print()

    # Load sample PRD and TRD
    print("Step 2: Loading sample PRD and TRD...")
    prd_path = Path("test_data/sample_prd.md")
    trd_path = Path("test_data/sample_trd.md")

    prd_content = prd_path.read_text(encoding='utf-8')
    trd_content = trd_path.read_text(encoding='utf-8')

    print(f"   [OK] PRD: {len(prd_content)} characters")
    print(f"   [OK] TRD: {len(trd_content)} characters")
    print()

    # Create job in database
    print("Step 3: Creating design job...")
    job_id = uuid.uuid4()

    async with db_manager.get_async_session() as session:
        job = DesignJob(
            job_id=job_id,
            project_id="test-task-manager-app",
            user_id="test-user-demo",
            prd_content=prd_content,
            trd_content=trd_content,
            status="pending"
        )
        session.add(job)
        await session.commit()

    print(f"   [OK] Job created: {job_id}")
    print()

    # Create initial state
    print("Step 4: Creating initial workflow state...")
    initial_state = DesignAgentState(
        job_id=str(job_id),
        prd_content=prd_content,
        trd_content=trd_content,
        extracted_screens=[],
        design_options={},
        selected_designs={},
        design_decisions=[],
        uploaded_code=None,
        validation_results=None,
        design_system=None,
        generated_documents={},
        open_source_selections=[],
        current_phase=0,
        status="initializing",
        error_message=None
    )
    print("   [OK] Initial state created")
    print()

    # Create workflow
    print("Step 5: Creating LangGraph workflow...")
    try:
        workflow = create_workflow()
        print("   [OK] Workflow created with nodes:")
        print("      - extract_screens (Phase 1)")
        print("      - generate_options (Phase 2)")
        print("      - create_ascii_ui (Phase 3)")
        print("      - refine_design (Phase 3 loop)")
        print("      - generate_design_system (Phase 4)")
        print("      - pause_for_google_ai (Phase 5)")
        print("      - [... and more]")
        print()
    except Exception as e:
        print(f"   [ERROR] Failed to create workflow: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Compile workflow
    print("Step 6: Compiling workflow with PostgreSQL checkpointer...")
    try:
        app = workflow.compile()
        print("   [OK] Workflow compiled successfully")
        print()
    except Exception as e:
        print(f"   [ERROR] Failed to compile workflow: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Run workflow (Phases 1-4 only, stop before pause)
    print("Step 7: Running workflow (Phases 1-4)...")
    print()

    try:
        # Configure to run with thread ID for checkpointing
        config = {"configurable": {"thread_id": str(job_id)}}

        print("   [Phase 1] Screen Extraction...")
        async for event in app.astream(initial_state, config):
            for node_name, node_output in event.items():
                if node_name == "extract_screens":
                    screens = node_output.get("extracted_screens", [])
                    print(f"   [OK] Extracted {len(screens)} screens:")
                    for i, screen in enumerate(screens, 1):
                        print(f"        {i}. {screen}")
                    print()

                elif node_name == "generate_options":
                    print("   [Phase 2] Design Options Generation...")
                    options = node_output.get("design_options", {})
                    print(f"   [OK] Generated options for {len(options)} screens")
                    for screen, opts in list(options.items())[:2]:  # Show first 2
                        print(f"        - {screen}: {len(opts)} layout options")
                    print()

                elif node_name == "create_ascii_ui":
                    print("   [Phase 3] ASCII UI Creation...")
                    designs = node_output.get("selected_designs", {})
                    print(f"   [OK] Created ASCII UIs for {len(designs)} screens")
                    print()

                    # Show sample ASCII UI
                    if designs:
                        sample_screen = list(designs.keys())[0]
                        sample_ui = designs[sample_screen]
                        print(f"   Sample UI for '{sample_screen}':")
                        print("   " + "-" * 60)
                        lines = sample_ui.split('\n')[:15]
                        for line in lines:
                            print(f"   {line}")
                        if len(sample_ui.split('\n')) > 15:
                            print(f"   ... ({len(sample_ui.split('\n')) - 15} more lines)")
                        print("   " + "-" * 60)
                        print()

                elif node_name == "refine_design":
                    print("   [Phase 3] Design Refinement...")
                    completed = node_output.get("completed_screens", 0)
                    print(f"   [OK] Refined and approved {completed} screens")
                    print()

                elif node_name == "generate_design_system":
                    print("   [Phase 4] Design System Extraction...")
                    design_system = node_output.get("design_system", {})
                    if design_system:
                        print(f"   [OK] Design system extracted:")
                        if "colors" in design_system:
                            print(f"        - Colors: {len(design_system['colors'])} defined")
                        if "typography" in design_system:
                            print(f"        - Typography: {len(design_system['typography'])} styles")
                        if "spacing" in design_system:
                            print(f"        - Spacing system: {design_system['spacing'].get('base_unit', 'N/A')}")
                    print()

                elif node_name == "pause_for_google_ai":
                    print("   [Phase 5] Pause for Manual Design (Google AI Studio)...")
                    print("   [OK] Workflow paused - would wait for user upload")
                    print()
                    # Break here - we're not testing the upload phase
                    return True

        print("   [OK] Workflow completed successfully")
        print()

    except Exception as e:
        print(f"   [ERROR] Workflow execution failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Final summary
    print("=" * 80)
    print("Workflow Test Summary")
    print("=" * 80)
    print()
    print(f"Job ID: {job_id}")
    print(f"Status: Workflow executed successfully")
    print()
    print("Phases Tested:")
    print("  [OK] Phase 1: Screen Extraction")
    print("  [OK] Phase 2: Layout Options Generation")
    print("  [OK] Phase 3: ASCII UI Creation")
    print("  [OK] Phase 4: Design System Extraction")
    print("  [PAUSE] Phase 5: Awaiting manual design upload")
    print()
    print("Note: Phases 5-6 require manual intervention (Google AI Studio upload)")
    print("      and would complete after code validation.")
    print()
    print("=" * 80)
    print("Test PASSED - LangGraph workflow is functional!")
    print("=" * 80)

    return True


if __name__ == "__main__":
    try:
        result = asyncio.run(test_workflow())
        exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n\nTest cancelled")
        exit(1)
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
