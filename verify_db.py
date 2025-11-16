"""
Quick script to verify PostgreSQL setup is working.
Run this after starting PostgreSQL to confirm everything is ready.
"""

import asyncio
import sys


async def verify_database():
    """Verify database connection and schema."""
    print("=" * 60)
    print("Design Agent Database Verification")
    print("=" * 60)
    print()

    # Test 1: Import modules
    print("1. Checking imports...")
    try:
        from src.database.connection import db_manager
        from src.config import settings
        print("   [OK] Imports successful")
    except Exception as e:
        print(f"   [X] Import failed: {e}")
        return False

    # Test 2: Initialize database engine
    print("\n2. Initializing database engine...")
    try:
        db_manager.initialize_async_engine()
        print(f"   [OK] Connected to: {settings.database_url}")
    except Exception as e:
        print(f"   [X] Connection failed: {e}")
        print("\nTroubleshooting:")
        print("  - Is PostgreSQL running? (docker ps)")
        print("  - Is the connection string correct in .env?")
        print("  - Default: postgresql+asyncpg://user:password@localhost:5432/anyon_db")
        return False

    # Test 3: Check if tables exist
    print("\n3. Checking database schema...")
    try:
        from sqlalchemy import text

        async with db_manager.get_async_session() as session:
            # Check for key tables
            result = await session.execute(text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema IN ('shared', 'design_agent')
                ORDER BY table_name
            """))

            tables = [row[0] for row in result.fetchall()]

            if len(tables) == 0:
                print("   [\!] No tables found - Run migrations:")
                print("     alembic upgrade head")
                return False

            print(f"   [OK] Found {len(tables)} tables:")
            for table in tables:
                print(f"     - {table}")

            # Check for required tables
            required_tables = [
                'design_jobs', 'design_progress', 'design_outputs',
                'design_decisions', 'open_source_selections',
                'sessions', 'checkpoints'
            ]

            missing = [t for t in required_tables if t not in tables]
            if missing:
                print(f"\n   [\!] Missing tables: {', '.join(missing)}")
                print("     Run: alembic upgrade head")
                return False

    except Exception as e:
        print(f"   [X] Schema check failed: {e}")
        return False

    # Test 4: Check views
    print("\n4. Checking ANYON read-only views...")
    try:
        async with db_manager.get_async_session() as session:
            result = await session.execute(text("""
                SELECT table_name
                FROM information_schema.views
                WHERE table_schema = 'shared'
                ORDER BY table_name
            """))

            views = [row[0] for row in result.fetchall()]
            print(f"   [OK] Found {len(views)} views:")
            for view in views:
                print(f"     - {view}")

            if len(views) < 3:
                print("   [\!] Expected 3 views (v_job_summary, v_session_history, v_design_analytics)")
                print("     Run: alembic upgrade head")

    except Exception as e:
        print(f"   [X] View check failed: {e}")

    # Test 5: Test write operation
    print("\n5. Testing database write operation...")
    try:
        import uuid
        from src.database.models import DesignJob

        async with db_manager.get_async_session() as session:
            # Create a test job
            test_job = DesignJob(
                job_id=uuid.uuid4(),
                project_id="verification-test",
                user_id="test-user",
                prd_content="# Test PRD",
                trd_content="# Test TRD",
                status="pending"
            )
            session.add(test_job)
            await session.commit()

            # Delete test job
            await session.delete(test_job)
            await session.commit()

            print("   [OK] Write operations working")

    except Exception as e:
        print(f"   [X] Write test failed: {e}")
        return False

    print("\n" + "=" * 60)
    print("[OK] All checks passed! Database is ready.")
    print("=" * 60)
    print("\nNext steps:")
    print("  1. Configure .env file with your API keys")
    print("  2. Start Redis: docker run --name redis-anyon -p 6379:6379 -d redis:7")
    print("  3. Run tests: pytest tests/test_session_history.py -v")
    print("  4. Start server: uvicorn src.main:app --reload")
    print()

    return True


if __name__ == "__main__":
    try:
        result = asyncio.run(verify_database())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n\nVerification cancelled.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
