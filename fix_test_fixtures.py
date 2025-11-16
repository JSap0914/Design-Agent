"""
Script to fix async fixture issues in Week 7 test files.
Converts @pytest.fixture async functions to regular helper functions.
"""

import re
import sys

def fix_test_file(filepath):
    """Fix a single test file."""
    print(f"Fixing {filepath}...")

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content

    # Step 1: Replace fixture definitions with helper functions
    content = re.sub(
        r'@pytest\.fixture\s+async def (\w+)\(async_session([^)]*)\):',
        r'async def create_\1(async_session\2):',
        content
    )

    # Step 2: Replace "sample_job" fixture parameter in test signatures
    content = re.sub(
        r'(async def test_\w+\(async_session), sample_job\)',
        r'\1)',
        content
    )

    # Step 3: Replace "sample_session" fixture parameter in test signatures
    content = re.sub(
        r'(async def test_\w+\(async_session), sample_session\)',
        r'\1)',
        content
    )

    # Step 4: Replace "sample_job, sample_session" fixture parameters
    content = re.sub(
        r'(async def test_\w+\(async_session), sample_job, sample_session\)',
        r'\1)',
        content
    )

    # Step 5: Add helper calls at start of tests that use sample_job
    # This is more complex - need to find tests and add the helper call

    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  [OK] Fixed {filepath}")
        return True
    else:
        print(f"  [INFO] No changes needed for {filepath}")
        return False

def add_helper_calls(filepath):
    """Add helper function calls at the start of test functions."""
    print(f"Adding helper calls to {filepath}...")

    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    result = []
    i = 0
    changes = 0

    while i < len(lines):
        line = lines[i]
        result.append(line)

        # Check if this is a test function definition
        if re.match(r'\s*async def test_\w+\(async_session\):', line):
            # Get the docstring (next line)
            i += 1
            if i < len(lines):
                result.append(lines[i])  # docstring

            # Check next non-empty line - if it doesn't create fixtures, add them
            i += 1
            if i < len(lines):
                next_line = lines[i]

                # If it's not already creating sample_job/sample_session, add them
                if 'create_sample_job' not in next_line and 'create_sample_session' not in next_line:
                    # Look ahead to see if sample_job or sample_session are used
                    test_body = ''.join(lines[i:min(i+50, len(lines))])

                    indent = '    '  # Standard pytest indent

                    if 'sample_session' in test_body:
                        result.append(f'{indent}sample_job = await create_sample_job(async_session)\n')
                        result.append(f'{indent}sample_session = await create_sample_session(async_session, sample_job)\n')
                        result.append('\n')
                        changes += 1
                    elif 'sample_job' in test_body:
                        result.append(f'{indent}sample_job = await create_sample_job(async_session)\n')
                        result.append('\n')
                        changes += 1

                result.append(next_line)
            i += 1
            continue

        i += 1

    if changes > 0:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(result)
        print(f"  [OK] Added {changes} helper calls to {filepath}")
        return True
    else:
        print(f"  [INFO] No helper calls needed in {filepath}")
        return False

if __name__ == '__main__':
    files = [
        'tests/test_session_history.py',
        'tests/test_job_processor.py',
        'tests/test_progress_updater.py',
        'tests/test_analytics_functions.py',
        'tests/test_week7_integration.py',
    ]

    print("=" * 60)
    print("Fixing async fixture issues in Week 7 test files")
    print("=" * 60)
    print()

    # Step 1: Fix fixture definitions
    for filepath in files:
        try:
            fix_test_file(filepath)
        except Exception as e:
            print(f"  [ERROR] Error fixing {filepath}: {e}")

    print()
    print("=" * 60)
    print("Adding helper function calls")
    print("=" * 60)
    print()

    # Step 2: Add helper calls
    for filepath in files:
        try:
            add_helper_calls(filepath)
        except Exception as e:
            print(f"  [ERROR] Error adding helpers to {filepath}: {e}")

    print()
    print("=" * 60)
    print("[OK] Done! Test files have been fixed.")
    print("=" * 60)
