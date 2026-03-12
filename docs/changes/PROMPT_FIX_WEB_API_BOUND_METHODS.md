# AI Agent Prompt: Fix XWAction FastAPI Engine Bound Method Execution

## Problem Statement

The `revive_auths` endpoint is failing when called via Web API with the error:
```
XWApiAgent.revive_auths() missing 1 required positional argument: 'self'
```

**Direct code execution works perfectly**, but Web API execution fails. This indicates a problem in how the FastAPI engine handles bound methods (instance methods) when executing XWAction-decorated functions.

## Context & Background

### What Works
- ✅ Direct code execution: `agent.revive_auths(base_path=path, use_storage=False)` works correctly
- ✅ All function types work when called directly (instance methods, static methods, class methods, standalone functions)
- ✅ Server starts successfully and endpoint is registered
- ✅ Authentication configs are loaded correctly from `data/xwauth/`

### What Fails
- ❌ Web API call to `/lmam/revive_auths` returns 400 error: "missing 1 required positional argument: 'self'"
- ❌ The XWAction wrapper function is not receiving `self` when called through FastAPI route handler

### Investigation Findings

1. **Function Type Investigation** (`xwaction/test_function_types.py`):
   - Instance methods (bound): Type `<class 'method'>`, has `__self__` and `__func__`
   - When called directly: `obj.method(**kwargs)` → Python automatically passes `obj` as `self` ✅
   - Signature shows only parameters (not `self`) because `@wraps(func)` preserves original signature

2. **Current Code State**:
   - FastAPI engine detects bound methods correctly: `hasattr(action, '__self__') and hasattr(action, '__func__')`
   - FastAPI engine calls bound method directly: `action(**execution_kwargs)`
   - XWAction wrapper function has logic to detect `self` in `*args` (lines 556-561 in `facade.py`)
   - The wrapper's `self` detection may be too restrictive or not working correctly

3. **Files Modified**:
   - `xwaction/src/exonware/xwaction/engines/fastapi.py` - FastAPI engine registration and execution
   - `xwaction/src/exonware/xwaction/engines/base.py` - Base execution function
   - `xwaction/src/exonware/xwaction/facade.py` - Wrapper function `self` detection (improved but may need more work)

## Root Cause Analysis Required

**You must investigate:**

1. **How bound methods work in Python:**
   - When `obj.method(**kwargs)` is called, Python automatically passes `obj` as first argument to the underlying function
   - The wrapper function receives `*args` where `args[0]` should be `self`
   - Check if the wrapper is correctly receiving `self` in `args[0]`

2. **XWAction wrapper function behavior:**
   - Location: `xwaction/src/exonware/xwaction/facade.py` lines 539-594
   - The wrapper uses `@wraps(func)` which preserves the original function signature
   - The wrapper has detection logic at lines 556-561 that checks if first arg is `self`
   - The wrapper calls `self._execute_wrapper(func, *args, **kwargs)` at line 594
   - **Investigate**: Is `self` being removed from `args` before calling the original function?

3. **FastAPI route handler execution flow:**
   - Location: `xwaction/src/exonware/xwaction/engines/fastapi.py` lines 230-304 (sync) and 291-366 (async)
   - Current approach: Calls `action(**execution_kwargs)` where `action` is a bound method
   - **Investigate**: Is Python's bound method mechanism working correctly when called from FastAPI route handler?

4. **XWApiAgent instance attributes:**
   - Check what attributes `XWApiAgent` instances have
   - The wrapper's `self` detection checks for: `_actions`, `_data`, `_name`, `__dict__`
   - **Investigate**: Does `XWApiAgent` have these attributes? Is detection working?

## Solution Requirements

### Following GUIDE_TEST.md Principles

**⚠️ CRITICAL: You MUST follow the Error Fixing Philosophy from GUIDE_TEST.md:**

1. **Root Cause Analysis is MANDATORY**
   - Never rig tests to pass
   - Never use workarounds or hacks
   - Always fix the root cause
   - Never remove features

2. **Maintain All Features**
   - ✅ Instance methods (bound methods) must work
   - ✅ Static methods must work
   - ✅ Class methods must work
   - ✅ Standalone functions must work
   - ✅ All existing functionality must be preserved

3. **Superior Features (if applicable)**
   - Improve error messages if fixing reveals opportunities
   - Add better logging for debugging
   - Enhance type detection if needed

4. **Forbidden Practices (from GUIDE_TEST.md)**
   - ❌ NEVER use `pass` to ignore errors
   - ❌ NEVER remove features to eliminate bugs
   - ❌ NEVER use generic `except:` to hide errors
   - ❌ NEVER skip root cause analysis
   - ❌ NEVER apply quick hacks or workarounds
   - ❌ NEVER change test expectations to match bugs

## Files to Investigate & Fix

### Primary Files
1. **`xwaction/src/exonware/xwaction/engines/fastapi.py`**
   - Lines 230-304: Sync route handler (`map_arguments_and_execute`)
   - Lines 291-366: Async route handler (`map_arguments_and_execute_async`)
   - Lines 405-636: `register_action` method
   - Current state: Detects bound methods and calls them directly

2. **`xwaction/src/exonware/xwaction/facade.py`**
   - Lines 539-594: Wrapper function that handles `*args, **kwargs`
   - Lines 556-561: `self` detection logic (recently improved)
   - Lines 1023-1042: `_execute_wrapper` method
   - **Key question**: Is `self` being passed correctly to the original function?

3. **`xwaction/src/exonware/xwaction/engines/base.py`**
   - Lines 70-112: `_execute_function` method
   - Handles bound methods, unbound methods, and standalone functions

### Test Files
1. **`karizma_agent/test_revive_api.py`** - Web API test (currently failing)
2. **`karizma_agent/test_revive_direct.py`** - Direct code test (works correctly)
3. **`xwaction/test_function_types.py`** - Function type investigation script

## Expected Solution Approach

### Step 1: Deep Investigation
1. Add detailed logging to trace execution flow:
   - Log when bound method is detected
   - Log `args` and `kwargs` received by wrapper function
   - Log what's passed to original function
   - Log signature inspection results

2. Create a minimal reproduction:
   - Create a simple test class with `@XWAction` decorated instance method
   - Test calling it directly vs through FastAPI
   - Compare the execution paths

3. Inspect the actual execution:
   - Use Python's `inspect` module to check function signatures
   - Check if `self` is in `args` when wrapper is called
   - Verify bound method attributes (`__self__`, `__func__`)

### Step 2: Root Cause Identification
Based on investigation, identify the exact point where `self` is lost:
- Is it in the FastAPI route handler?
- Is it in the XWAction wrapper function?
- Is it in the signature detection logic?
- Is it in the argument mapping?

### Step 3: Fix Implementation
1. **Fix the root cause** (not symptoms):
   - If wrapper removes `self` incorrectly → Fix wrapper logic
   - If route handler doesn't pass `self` → Fix route handler
   - If signature detection is wrong → Fix detection
   - If argument mapping is broken → Fix mapping

2. **Ensure all function types still work**:
   - Test instance methods
   - Test static methods
   - Test class methods
   - Test standalone functions

3. **Add comprehensive tests**:
   - Unit test for each function type
   - Integration test for Web API execution
   - Test edge cases (nested decorators, complex signatures, etc.)

### Step 4: Verification
1. Run direct code test: `python karizma_agent/test_revive_direct.py` → Should still pass ✅
2. Run Web API test: `python karizma_agent/test_revive_api.py` → Should now pass ✅
3. Run function type investigation: `python xwaction/test_function_types.py` → Should all work ✅
4. Test other endpoints to ensure no regressions

## Code References

### Key Code Sections

**FastAPI Engine - Route Handler (Sync):**
```python
# Location: xwaction/src/exonware/xwaction/engines/fastapi.py:230-304
def map_arguments_and_execute(args: tuple, kwargs: dict):
    # ... argument extraction ...
    execution_kwargs = {**body_kwargs, **path_kwargs}
    
    # 4. Check if action is a bound method
    is_bound = hasattr(action, '__self__') and hasattr(action, '__func__')
    
    if is_bound:
        # Current approach: Call bound method directly
        try:
            result_data = action(**execution_kwargs)
            return result_data
        except Exception as e:
            # Error: missing 1 required positional argument: 'self'
```

**XWAction Wrapper Function:**
```python
# Location: xwaction/src/exonware/xwaction/facade.py:539-594
@wraps(func)
def wrapper(*args, **kwargs):
    # ... validation logic ...
    
    # Handle bound methods: if first arg looks like 'self'
    if args and param_names and param_names[0] in ('self', 'cls'):
        param_names = param_names[1:]  # Skip 'self' from param names
        # Check if first arg is actually 'self'
        if args and hasattr(args[0], '__class__'):
            is_likely_instance = (
                hasattr(args[0], '_actions') or 
                hasattr(args[0], '_data') or 
                hasattr(args[0], '_name') or
                hasattr(args[0], '__dict__') or
                not inspect.isclass(args[0])
            )
            if is_likely_instance:
                args_to_map = args[1:]  # Skip 'self' from args
    
    # ... validation ...
    return self._execute_wrapper(func, *args, **kwargs)  # Line 594
```

**Execute Wrapper:**
```python
# Location: xwaction/src/exonware/xwaction/facade.py:1023-1042
def _execute_wrapper(self, func: Callable, *args, **kwargs):
    # ...
    result = func(*args, **kwargs)  # Line 1039
    return result
```

## Test Files

### Web API Test (Currently Failing)
**File:** `karizma_agent/test_revive_api.py`
- Tests: `POST http://localhost:8000/lmam/revive_auths`
- Payload: `{"base_path": "...", "use_storage": false}`
- Expected: 200 OK with revive result
- Actual: 400 Bad Request with "missing 1 required positional argument: 'self'"

### Direct Code Test (Working)
**File:** `karizma_agent/test_revive_direct.py`
- Tests: `agent.load_all_auth_configs(base_path)` directly
- Expected: Success with reloaded configs
- Actual: ✅ Works correctly

### Function Type Investigation
**File:** `xwaction/test_function_types.py`
- Tests all function types (instance, static, class, standalone)
- All work correctly when called directly

## Success Criteria

### Must Pass
1. ✅ `python karizma_agent/test_revive_api.py` → Returns 200 OK with valid result
2. ✅ `python karizma_agent/test_revive_direct.py` → Still works (no regression)
3. ✅ `python xwaction/test_function_types.py` → All function types work
4. ✅ Other XWAction endpoints still work (no regressions)

### Must Maintain
1. ✅ All existing features work (instance, static, class, standalone functions)
2. ✅ No breaking changes to API
3. ✅ Error messages are clear and helpful
4. ✅ Code follows eXonware standards

### Should Improve (If Opportunity)
1. Better error messages if fixing reveals issues
2. Better logging for debugging
3. More robust type detection
4. Comprehensive test coverage

## Debugging Tools & Techniques

### Add Logging
```python
import logging
logger = logging.getLogger(__name__)

# In wrapper function:
logger.debug(f"Wrapper called with args={args}, kwargs={kwargs}")
logger.debug(f"First arg type: {type(args[0]) if args else 'None'}")
logger.debug(f"First arg attributes: {dir(args[0]) if args else 'None'}")
logger.debug(f"Function signature: {inspect.signature(func)}")
logger.debug(f"About to call func with args={args}, kwargs={kwargs}")
```

### Use Python Debugger
```python
import pdb; pdb.set_trace()  # Breakpoint in wrapper function
```

### Inspect Function Signatures
```python
import inspect
sig = inspect.signature(func)
print(f"Function: {func.__name__}")
print(f"Parameters: {list(sig.parameters.keys())}")
print(f"First param: {list(sig.parameters.keys())[0] if sig.parameters else 'None'}")
```

## Investigation Checklist

Before implementing a fix, verify:

- [ ] Understand how Python bound methods work
- [ ] Understand how `@wraps(func)` affects function signatures
- [ ] Trace the exact execution path from FastAPI route → wrapper → original function
- [ ] Verify `self` is in `args[0]` when wrapper is called
- [ ] Check if wrapper's `self` detection logic is working
- [ ] Verify `_execute_wrapper` receives correct arguments
- [ ] Test with minimal reproduction case
- [ ] Check if issue is specific to `revive_auths` or affects all instance methods
- [ ] Verify no regressions in other function types

## Expected Deliverables

1. **Root Cause Analysis Document**
   - What is the exact problem?
   - Where does `self` get lost?
   - Why does direct call work but Web API call fail?

2. **Fixed Code**
   - All modified files with clear comments
   - Explanation of the fix
   - Why this fix addresses the root cause

3. **Comprehensive Tests**
   - Test for each function type (instance, static, class, standalone)
   - Integration test for Web API execution
   - Regression tests to prevent future issues

4. **Verification Results**
   - All tests pass
   - No regressions
   - Performance not degraded

## Important Notes

1. **Do NOT** remove the `self` parameter from function signatures
2. **Do NOT** change how bound methods work in Python
3. **Do NOT** bypass the wrapper function
4. **Do NOT** use workarounds or hacks
5. **DO** fix the root cause properly
6. **DO** maintain all existing features
7. **DO** add comprehensive tests
8. **DO** document the fix clearly

## Related Files & Documentation

- **Investigation Document:** `xwaction/INVESTIGATION_FUNCTION_TYPES.md`
- **Test Guide:** `docs/guides/GUIDE_TEST.md` (especially Error Fixing Philosophy section)
- **Test Scripts:**
  - `karizma_agent/test_revive_api.py` (failing)
  - `karizma_agent/test_revive_direct.py` (working)
  - `xwaction/test_function_types.py` (investigation)

## Starting Point

Begin by:
1. Reading `xwaction/src/exonware/xwaction/facade.py` lines 539-594 (wrapper function)
2. Reading `xwaction/src/exonware/xwaction/engines/fastapi.py` lines 230-304 (route handler)
3. Running `python xwaction/test_function_types.py` to understand function types
4. Adding detailed logging to trace execution flow
5. Creating a minimal reproduction case

## Success Message Format

When you've solved it, provide:

```
✅ ROOT CAUSE IDENTIFIED: [Brief description]

✅ SOLUTION IMPLEMENTED: [What was fixed]

✅ VERIFICATION:
- Direct code test: ✅ PASSED
- Web API test: ✅ PASSED  
- Function type tests: ✅ ALL PASSED
- Regression tests: ✅ NO REGRESSIONS

✅ FILES MODIFIED:
- [list of files with line numbers]

✅ TESTS ADDED:
- [list of new tests]

✅ FEATURES MAINTAINED:
- ✅ Instance methods work
- ✅ Static methods work
- ✅ Class methods work
- ✅ Standalone functions work
```

---

**Remember: Fix the root cause, maintain all features, add comprehensive tests, and document everything clearly. Follow GUIDE_TEST.md principles strictly - no workarounds, no hacks, no feature removal.**

