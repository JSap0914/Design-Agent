"""
Script to convert all test functions to use async with db_manager.get_async_session() pattern.
"""

import re
import sys

def fix_test_function(test_func_text):
    """Fix a single test function to use async with pattern."""
    # Check if it already has async with db_manager
    if 'async with db_manager.get_async_session()' in test_func_text:
        return test_func_text

    # Remove (async_session) parameter
    test_func_text = re.sub(
        r'(async def test_\w+)\(async_session\)',
        r'\1()',
        test_func_text
    )

    # Find the docstring end and insert async with block
    lines = test_func_text.split('\n')
    result = []
    inserted = False

    for i, line in enumerate(lines):
        result.append(line)

        # After docstring ("""), insert the async with block
        if not inserted and '"""' in line and i > 0:
            # Check if next line is not already the import
            if i + 1 < len(lines) and 'from src.database.connection import db_manager' not in lines[i + 1]:
                indent = '    '
                result.append(f'{indent}from src.database.connection import db_manager')
                result.append(f'{indent}')
                result.append(f'{indent}async with db_manager.get_async_session() as async_session:')
                inserted = True

                # Indent all remaining lines
                for j in range(i + 1, len(lines)):
                    if lines[j].strip():  # Non-empty line
                        lines[j] = '    ' + lines[j]

    if inserted:
        # Re-join after docstring insertion
        result_text = '\n'.join(result[:len(result) - len(lines) + i + 1])
        remaining = '\n'.join(lines[i + 1:])
        return result_text + '\n' + remaining

    return test_func_text

def process_file(filepath):
    """Process a single test file."""
    print(f"Processing {filepath}...")

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content

    # Split by test functions
    parts = re.split(r'(@pytest\.mark\.asyncio\s+async def test_\w+)', content)

    result = [parts[0]]  # First part (imports, helpers, etc.)

    # Process each test function
    for i in range(1, len(parts), 2):
        if i + 1 < len(parts):
            decorator = parts[i]
            func_body = parts[i + 1]

            # Find the end of this function (next @pytest or end of file)
            # This is the full function including signature and body
            full_func = decorator + func_body

            # Check if this function uses async_session parameter
            if '(async_session)' in full_func or 'async_session.' in full_func or 'await async_session.' in full_func:
                # Need to fix this function
                fixed = fix_with_simple_replace(full_func)
                result.append(fixed)
            else:
                result.append(full_func)

    content = ''.join(result)

    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  [OK] Fixed {filepath}")
        return True
    else:
        print(f"  [INFO] No changes for {filepath}")
        return False

def fix_with_simple_replace(func_text):
    """Simpler approach: just wrap the body in async with."""
    lines = func_text.split('\n')
    result = []
    doc_end_idx = -1

    # Find decorator and function def
    for i, line in enumerate(lines):
        result.append(line)
        if 'async def test_' in line:
            # Remove (async_session) parameter
            result[i] = re.sub(r'\(async_session\)', '()', result[i])

        # Find end of docstring
        if '"""' in line and i > 1 and doc_end_idx == -1:
            doc_end_idx = i

    if doc_end_idx != -1:
        # Insert async with block after docstring
        indent = '    '
        new_lines = result[:doc_end_idx + 1]
        new_lines.append(f'{indent}from src.database.connection import db_manager')
        new_lines.append(f'{indent}')
        new_lines.append(f'{indent}async with db_manager.get_async_session() as async_session:')

        # Indent remaining lines
        for i in range(doc_end_idx + 1, len(result)):
            if result[i].strip():  # Non-empty line
                new_lines.append('    ' + result[i])
            else:
                new_lines.append(result[i])

        return '\n'.join(new_lines)

    return func_text

def smart_fix_file(filepath):
    """Smarter file-level fix."""
    print(f"Processing {filepath}...")

    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    result = []
    i = 0
    changes = 0

    while i < len(lines):
        line = lines[i]

        # Check if this is a test function with async_session parameter
        if re.match(r'\s*async def test_\w+\(async_session\):', line):
            # Remove parameter
            fixed_line = re.sub(r'\(async_session\)', '()', line)
            result.append(fixed_line)
            i += 1

            # Add docstring
            if i < len(lines) and '"""' in lines[i]:
                result.append(lines[i])
                i += 1

            # Add async with block
            indent = '    '
            result.append(f'{indent}from src.database.connection import db_manager\n')
            result.append(f'{indent}\n')
            result.append(f'{indent}async with db_manager.get_async_session() as async_session:\n')

            # Indent all lines until next function or end
            while i < len(lines):
                next_line = lines[i]

                # Stop if we hit another test function or decorator
                if (re.match(r'@pytest\.mark\.asyncio', next_line) or
                    re.match(r'async def test_', next_line) or
                    re.match(r'def test_', next_line) or
                    re.match(r'# =====', next_line)):
                    break

                # Indent the line (add 4 spaces)
                if next_line.strip():
                    result.append('    ' + next_line)
                else:
                    result.append(next_line)
                i += 1

            changes += 1
        else:
            result.append(line)
            i += 1

    if changes > 0:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(result)
        print(f"  [OK] Fixed {changes} test functions in {filepath}")
        return True
    else:
        print(f"  [INFO] No changes needed for {filepath}")
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
    print("Converting test functions to async with pattern")
    print("=" * 60)
    print()

    for filepath in files:
        try:
            smart_fix_file(filepath)
        except Exception as e:
            print(f"  [ERROR] Error fixing {filepath}: {e}")
            import traceback
            traceback.print_exc()

    print()
    print("=" * 60)
    print("[OK] Done!")
    print("=" * 60)
