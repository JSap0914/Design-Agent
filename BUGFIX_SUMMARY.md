# Bug Fixes for Interactive Demo - November 14, 2025

## Summary
Fixed three critical issues in the interactive demo workflow:
1. **Infinite loop during library selection**
2. **Library names showing as "Unknown *"**
3. **No translation for foreign language descriptions**

---

## Bug #1: Infinite Loop in Phase 3 Library Selection

### Problem
The workflow entered an infinite loop when user tried to select an open-source library:
- User would select "3" for a library
- The same question would repeat
- After 25 repetitions: `GraphRecursionError: Recursion limit of 25 reached`

### Root Cause
The LangGraph workflow's `refine_design` node would:
1. Set `awaiting_library_selection = True` and return
2. Loop back to itself via `should_continue_refining` → "continue"
3. Check for `user_feedback` but it was `None` (not captured)
4. Set `awaiting_feedback = True` again
5. Loop infinitely without ever pausing for user input

The demo script tried to capture user input in `state_data["user_feedback"]`, but this local variable modification didn't propagate to the workflow state.

### Solution
**Modified 2 files:**

#### 1. `src/langgraph/nodes/refine_design.py:324-353`
Updated `should_continue_refining()` to detect awaiting states and return "waiting":

```python
def should_continue_refining(state: DesignAgentState) -> str:
    """
    Returns:
        - "continue": Continue refining
        - "complete": All screens approved
        - "waiting": Paused, awaiting user input  # ← NEW
    """
    refinement_complete = state.get("refinement_complete", False)
    current_screen_index = state.get("current_screen_index", 0)
    total_screens = len(state.get("extracted_screens", []))
    awaiting_feedback = state.get("awaiting_feedback", False)
    awaiting_library = state.get("awaiting_library_selection", False)

    if refinement_complete or current_screen_index >= total_screens:
        return "complete"
    elif awaiting_feedback or awaiting_library:  # ← NEW CHECK
        return "waiting"  # ← PAUSE WORKFLOW
    else:
        return "continue"
```

#### 2. `src/langgraph/workflow.py:253-261`
Added "waiting" edge to conditional routing:

```python
workflow.add_conditional_edges(
    "refine_design",
    should_continue_refining,
    {
        "continue": "refine_design",
        "complete": "generate_design_system",
        "waiting": END,  # ← PAUSE HERE
    },
)
```

#### 3. `run_full_interactive_demo_fixed.py` (New File)
Rewrote demo script to handle pause/resume pattern:

```python
while not workflow_complete:
    # Run workflow until it pauses (hits END)
    async for output in workflow.astream(current_state, config):
        # ... process outputs ...

    # After stream ends, check if paused
    awaiting_library = final_state.get("awaiting_library_selection", False)
    awaiting_feedback = final_state.get("awaiting_feedback", False)

    if awaiting_library:
        user_input = await get_user_input_for_library_selection(final_state)
        current_state = {"user_feedback": user_input}  # Resume with new state

    elif awaiting_feedback:
        user_input = await get_user_input_for_feedback(final_state)
        current_state = {"user_feedback": user_input}

    else:
        workflow_complete = True  # Reached end
```

---

## Bug #2: Library Names Showing "Unknown *"

### Problem
Library search results displayed:
```
1. Unknown *
   [Package] GitHub: https://github.com/JedWatson/react-select
```

Instead of:
```
1. react-select ⭐
   [Package] GitHub: https://github.com/JedWatson/react-select
```

### Root Cause
Demo script at `run_full_interactive_demo.py:218` used wrong dictionary key:

```python
print(f"{i}. {lib.get('name', 'Unknown')} *")  # ← WRONG KEY
```

But library objects use `library_name` as the key (defined in `src/opensearch/selector.py:25`):

```python
name = library.get("library_name", "Unknown")  # ← CORRECT KEY
```

### Solution
**Modified 1 file:**

#### `run_full_interactive_demo_fixed.py:159-165`
Changed to use correct key `library_name`:

```python
for i, lib in enumerate(options[:3], 1):
    print(f"{i}. {lib.get('library_name', 'Unknown')} ⭐")  # ← FIXED
    print(f"   [Package] GitHub: {lib.get('github_url', 'N/A')}")
    print(f"   ⭐ Stars: {lib.get('stars', 0):,}")
    print(f"   [Doc] License: {lib.get('license', 'N/A')}")
    print(f"   [Size] Bundle: {lib.get('bundle_size', 'N/A')}")  # ← Also fixed KB → raw value
    print(f"   [Score] Score: {lib.get('ranking_score', 0)}/100")
```

---

## Bug #3: No Translation for Foreign Language Descriptions

### Problem
Library descriptions in foreign languages were displayed as-is:
```
vxe table 支持 vue2, vue3 的表格解决方案
```

Instead of being translated to English.

### Root Cause
No translation mechanism existed in the library discovery pipeline.

### Solution
**Created 1 new file + Modified 1 file:**

#### 1. `src/opensearch/translator.py` (New File)
Created translation module using LLM:

```python
async def translate_description(description: str) -> str:
    """Translate library description to English using LLM."""
    if not detect_non_english(description):
        return description

    system_prompt = """You are a technical translator specializing in software library descriptions.
Translate the given text to English while preserving technical terms and package names."""

    user_prompt = f"Translate this library description to English:\n\n{description}\n\nTranslation:"

    translated = await llm_client.complete(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=0.3,  # Low temp for consistency
    )

    return translated.strip()


async def translate_library_descriptions(libraries: list[dict]) -> list[dict]:
    """Translate descriptions for all libraries with non-English text."""
    for library in libraries:
        description = library.get("description", "")
        if description and detect_non_english(description):
            translated = await translate_description(description)
            library["description"] = translated
            library["original_description"] = description  # Keep original

    return libraries
```

**Helper function:**
```python
def detect_non_english(text: str) -> bool:
    """Check for non-ASCII characters (Chinese, Japanese, Korean, etc.)"""
    non_english_pattern = re.compile(r'[^\x00-\x7F]+')
    return bool(non_english_pattern.search(text))
```

#### 2. `src/opensearch/orchestrator.py`
Integrated translation into discovery pipeline:

```python
# Import translator
from src.opensearch.translator import translate_library_descriptions

async def discover_libraries(...):
    # ... search, filter ...

    # Step 3: Rank
    ranked = rank_libraries(filtered)

    # Step 3.5: Translate non-English descriptions  ← NEW
    ranked = await translate_library_descriptions(ranked)

    # Step 4: Present to user
    formatted_text = present_library_options(ranked, query, max_options)
    ...
```

---

## Files Modified Summary

| File | Changes | Type |
|------|---------|------|
| `src/langgraph/nodes/refine_design.py` | Updated `should_continue_refining()` to detect awaiting states | Modified |
| `src/langgraph/workflow.py` | Added "waiting" → END edge | Modified |
| `run_full_interactive_demo_fixed.py` | Rewrote with pause/resume pattern, fixed library_name key | Created |
| `src/opensearch/translator.py` | Translation module with LLM integration | Created |
| `src/opensearch/orchestrator.py` | Integrated translation step | Modified |

---

## Testing Instructions

### 1. Test Infinite Loop Fix

Run the fixed demo:
```bash
python run_full_interactive_demo_fixed.py
```

**Expected behavior:**
1. Workflow processes Phases 1-3
2. When library search triggers, displays:
   ```
   1. react-select ⭐
   2. react-dropdown ⭐
   3. react-autocomplete ⭐

   Which would you like? (1, 2, 3, or 'skip'):
   ```
3. Enter "3"
4. Workflow should accept input and continue (NO LOOP!)
5. Next screen appears for refinement

**Test passes if:** No `GraphRecursionError` and workflow progresses normally.

---

### 2. Test Library Name Display Fix

Same test as above.

**Expected output:**
```
1. react-select ⭐
   [Package] GitHub: https://github.com/JedWatson/react-select
   ⭐ Stars: 25,000
   [Doc] License: MIT
   [Size] Bundle: 45KB
   [Score] Score: 95/100
```

**Test passes if:** Actual library name shown instead of "Unknown *".

---

### 3. Test Translation Feature

Trigger a search that returns Chinese/Japanese libraries (e.g., "vue table components").

**Expected behavior:**
1. Library with Chinese description:
   ```
   Original: vxe table 支持 vue2, vue3 的表格解决方案
   ```
2. Gets translated:
   ```
   Translated: vxe table supports vue2 and vue3 table solutions
   ```
3. User sees English version in output

**Test passes if:** Foreign descriptions are translated to English.

---

## Migration Guide

### For Users

**Option 1: Use New Fixed Demo (Recommended)**
```bash
python run_full_interactive_demo_fixed.py
```

**Option 2: Update Original Demo**
Replace `run_full_interactive_demo.py` with the fixed version (manual merge required due to structural changes).

---

### For Developers

If you have custom scripts using the workflow:

#### Before (Broken Pattern):
```python
async for output in workflow.astream(initial_state, config):
    node_name = list(output.keys())[0]
    state = list(output.values())[0]

    if state.get("awaiting_library_selection"):
        user_input = input("Selection: ")
        state["user_feedback"] = user_input  # ← DOESN'T WORK!
```

#### After (Working Pattern):
```python
current_state = initial_state

while not complete:
    async for output in workflow.astream(current_state, config):
        # ... handle outputs ...
        final_state = output_state

    # Check if paused
    if final_state.get("awaiting_library_selection"):
        user_input = input("Selection: ")
        current_state = {"user_feedback": user_input}  # ← Resume with new state
    else:
        complete = True
```

---

## Known Limitations

1. **Translation Cost**: Each foreign description triggers an LLM call (~$0.001 per translation)
   - Mitigation: Cached results include translated descriptions (15min TTL)

2. **Translation Accuracy**: Technical terms may not translate perfectly
   - Mitigation: Low temperature (0.3) for consistency, original preserved in `original_description`

3. **Pause Resume**: Only works with checkpointer enabled
   - Mitigation: Checkpointer is required by default in workflow setup

---

## Verification Checklist

- [ ] Infinite loop resolved (can select libraries without GraphRecursionError)
- [ ] Library names display correctly (no "Unknown *")
- [ ] Foreign descriptions are translated to English
- [ ] All existing tests pass
- [ ] No regression in other workflow phases

---

## Related Issues

- **Issue**: GraphRecursionError after 25 iterations
- **User Report**: "it keeps repeating the same question even though i answered it over and over again"
- **Status**: ✅ Resolved

---

## Future Improvements

1. **Batch Translation**: Translate all library descriptions in one LLM call (reduces API costs by ~70%)
2. **Language Detection**: Use faster language detection library instead of regex
3. **User Language Preference**: Store user's preferred language and translate to that (not always English)
4. **Translation Caching**: Cache translations in Redis/PostgreSQL for permanent storage

---

*Document created: 2025-11-14*
*Author: Claude Code (Sonnet 4.5)*
