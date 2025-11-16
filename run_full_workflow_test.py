"""
Full Design Agent Workflow Test
Tests the complete Phase 1-6 workflow with sample PRD and TRD.
"""

import asyncio
import uuid
from pathlib import Path

from src.database.connection import db_manager
from src.database.models import DesignJob, DesignProgress

# Simple logging setup for test script
import logging
logging.basicConfig(level=logging.WARNING)  # Suppress verbose logs


async def run_workflow_test():
    """Run full Design Agent workflow test."""

    print("=" * 70)
    print("Design Agent - Full Workflow Test")
    print("=" * 70)
    print()

    # Initialize database
    print("1. Initializing database...")
    db_manager.initialize_async_engine()
    print("   [OK] Database initialized")
    print()

    # Load sample PRD and TRD
    print("2. Loading sample PRD and TRD...")
    prd_path = Path("test_data/sample_prd.md")
    trd_path = Path("test_data/sample_trd.md")

    if not prd_path.exists() or not trd_path.exists():
        print("   [ERROR] Sample files not found!")
        print(f"   Expected: {prd_path.absolute()}")
        print(f"   Expected: {trd_path.absolute()}")
        return False

    prd_content = prd_path.read_text(encoding='utf-8')
    trd_content = trd_path.read_text(encoding='utf-8')

    print(f"   [OK] Loaded PRD ({len(prd_content)} characters)")
    print(f"   [OK] Loaded TRD ({len(trd_content)} characters)")
    print()

    # Create design job
    print("3. Creating design job in database...")
    job_id = uuid.uuid4()

    async with db_manager.get_async_session() as session:
        job = DesignJob(
            job_id=job_id,
            project_id="test-task-manager",
            user_id="test-user",
            prd_content=prd_content,
            trd_content=trd_content,
            status="pending"
        )
        session.add(job)
        await session.commit()
        await session.refresh(job)

        print(f"   [OK] Created job: {job_id}")
        print(f"   [OK] Status: {job.status}")
        print()

    # Test Phase 1: Screen Extraction
    print("4. Testing Phase 1: Screen Extraction...")
    try:
        from src.agents.phase1_screen_extractor import extract_screens_from_prd

        screens = await extract_screens_from_prd(prd_content, trd_content)

        print(f"   [OK] Extracted {len(screens)} screens:")
        for i, screen in enumerate(screens, 1):
            print(f"      {i}. {screen}")
        print()

        # Update progress
        async with db_manager.get_async_session() as session:
            progress = DesignProgress(
                job_id=job_id,
                current_phase=1,
                phase_name="Screen Extraction",
                progress_percent=16,
                screen_count=len(screens),
                completed_screens=0,
                status_message=f"Extracted {len(screens)} screens from PRD"
            )
            session.add(progress)
            await session.commit()
            print(f"   [OK] Progress updated: Phase 1 - 16% complete")
            print()

    except Exception as e:
        print(f"   [ERROR] Phase 1 failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Test Phase 2: Generate Design Options
    print("5. Testing Phase 2: Generate Design Options...")
    try:
        from src.agents.phase2_option_generator import generate_layout_options

        # Test with first screen
        test_screen = screens[0]
        options = await generate_layout_options(
            screen_name=test_screen,
            prd_content=prd_content,
            trd_content=trd_content
        )

        print(f"   [OK] Generated {len(options)} layout options for '{test_screen}':")
        for i, option in enumerate(options, 1):
            preview = option[:100].replace('\n', ' ')
            print(f"      Option {i}: {preview}...")
        print()

        # Update progress
        async with db_manager.get_async_session() as session:
            # Update existing progress
            from sqlalchemy import select
            result = await session.execute(
                select(DesignProgress).where(DesignProgress.job_id == job_id)
            )
            progress = result.scalar_one()
            progress.current_phase = 2
            progress.phase_name = "Design Options"
            progress.progress_percent = 33
            progress.status_message = f"Generated {len(options)} options for {test_screen}"
            await session.commit()
            print(f"   [OK] Progress updated: Phase 2 - 33% complete")
            print()

    except Exception as e:
        print(f"   [ERROR] Phase 2 failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Test Phase 3: ASCII UI Generation
    print("6. Testing Phase 3: ASCII UI Generation...")
    try:
        from src.agents.phase3_ascii_generator import generate_ascii_ui

        # Use first option
        ascii_ui = await generate_ascii_ui(
            screen_name=test_screen,
            layout_description=options[0],
            prd_content=prd_content,
            trd_content=trd_content
        )

        print(f"   [OK] Generated ASCII UI for '{test_screen}':")
        print()
        print("   " + "-" * 50)
        # Show first 20 lines
        lines = ascii_ui.split('\n')[:20]
        for line in lines:
            print(f"   {line}")
        if len(ascii_ui.split('\n')) > 20:
            print(f"   ... ({len(ascii_ui.split('\n')) - 20} more lines)")
        print("   " + "-" * 50)
        print()

        # Update progress
        async with db_manager.get_async_session() as session:
            result = await session.execute(
                select(DesignProgress).where(DesignProgress.job_id == job_id)
            )
            progress = result.scalar_one()
            progress.current_phase = 3
            progress.phase_name = "ASCII UI Design"
            progress.progress_percent = 50
            progress.completed_screens = 1
            progress.status_message = f"Created ASCII UI for {test_screen}"
            await session.commit()
            print(f"   [OK] Progress updated: Phase 3 - 50% complete")
            print()

    except Exception as e:
        print(f"   [ERROR] Phase 3 failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Test Phase 4: Design System Extraction
    print("7. Testing Phase 4: Design System Extraction...")
    try:
        from src.agents.phase4_design_system import extract_design_system

        design_system = await extract_design_system(
            approved_designs={test_screen: ascii_ui},
            trd_content=trd_content
        )

        print(f"   [OK] Extracted Design System:")
        print(f"      - Colors: {len(design_system.get('colors', {}))} defined")
        print(f"      - Typography: {len(design_system.get('typography', {}))} styles")
        print(f"      - Spacing: {design_system.get('spacing', {}).get('base_unit', 'N/A')}")
        print()

        # Update progress
        async with db_manager.get_async_session() as session:
            result = await session.execute(
                select(DesignProgress).where(DesignProgress.job_id == job_id)
            )
            progress = result.scalar_one()
            progress.current_phase = 4
            progress.phase_name = "Design System"
            progress.progress_percent = 66
            progress.status_message = "Design system extracted from approved designs"
            await session.commit()
            print(f"   [OK] Progress updated: Phase 4 - 66% complete")
            print()

    except Exception as e:
        print(f"   [ERROR] Phase 4 failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Simulate Phase 5: Code Validation (would be skipped in automated test)
    print("8. Simulating Phase 5: Code Validation...")
    print("   [SKIP] Phase 5 requires user-uploaded code from Google AI Studio")
    print("   [INFO] In real workflow, system pauses here for manual design")
    print()

    async with db_manager.get_async_session() as session:
        result = await session.execute(
            select(DesignProgress).where(DesignProgress.job_id == job_id)
        )
        progress = result.scalar_one()
        progress.current_phase = 5
        progress.phase_name = "Code Validation"
        progress.progress_percent = 83
        progress.status_message = "Waiting for user upload (simulated skip)"
        await session.commit()
        print(f"   [OK] Progress updated: Phase 5 - 83% complete")
        print()

    # Test Phase 6: Document Generation
    print("9. Testing Phase 6: Document Generation...")
    try:
        from src.agents.phase6_document_generator import generate_all_documents

        documents = await generate_all_documents(
            job_id=job_id,
            prd_content=prd_content,
            trd_content=trd_content,
            extracted_screens=screens,
            approved_designs={test_screen: ascii_ui},
            design_system=design_system,
            design_decisions=[],
            selected_libraries=[]
        )

        print(f"   [OK] Generated {len(documents)} documents:")
        for doc_type, content in documents.items():
            print(f"      - {doc_type}: {len(content)} characters")
        print()

        # Update job status to completed
        async with db_manager.get_async_session() as session:
            result = await session.execute(
                select(DesignJob).where(DesignJob.job_id == job_id)
            )
            job = result.scalar_one()
            job.status = "completed"

            result = await session.execute(
                select(DesignProgress).where(DesignProgress.job_id == job_id)
            )
            progress = result.scalar_one()
            progress.current_phase = 6
            progress.phase_name = "Documentation"
            progress.progress_percent = 100
            progress.status_message = "All documents generated successfully"

            await session.commit()
            print(f"   [OK] Job completed: Phase 6 - 100% complete")
            print()

    except Exception as e:
        print(f"   [ERROR] Phase 6 failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Final status
    print("=" * 70)
    print("Workflow Test Results")
    print("=" * 70)
    print()
    print(f"Job ID: {job_id}")
    print(f"Status: COMPLETED")
    print()
    print("Phases Completed:")
    print("  [OK] Phase 1: Screen Extraction")
    print("  [OK] Phase 2: Design Options")
    print("  [OK] Phase 3: ASCII UI Generation")
    print("  [OK] Phase 4: Design System Extraction")
    print("  [SKIP] Phase 5: Code Validation (requires manual upload)")
    print("  [OK] Phase 6: Document Generation")
    print()
    print(f"Screens Extracted: {len(screens)}")
    print(f"Layout Options Generated: {len(options)}")
    print(f"ASCII UIs Created: 1 (sample)")
    print(f"Documents Generated: {len(documents)}")
    print()
    print("=" * 70)
    print("Full workflow test PASSED!")
    print("=" * 70)

    return True


if __name__ == "__main__":
    try:
        result = asyncio.run(run_workflow_test())
        exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n\nTest cancelled by user")
        exit(1)
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
