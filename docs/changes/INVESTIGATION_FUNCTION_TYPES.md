# XWAction Function Types Investigation

## Summary

Investigation into how XWAction handles different function types:
1. Instance methods (bound methods)
2. Static methods  
3. Class methods
4. Standalone functions

## Findings

### Test Results

All function types work correctly when called directly:

1. **Instance Method (bound)**: ✅ Works
   - Type: `<class 'method'>` (bound method)
   - Has `__self__` and `__func__`
   - When called: `obj.method(**kwargs)` → Python automatically passes `obj` as `self`

2. **Static Method**: ✅ Works
   - Type: `<class 'function'>`
   - No `__self__` or `__func__`
   - When called: `Class.static_method(**kwargs)` → No `self` needed

3. **Class Method (bound)**: ✅ Works
   - Type: `<class 'method'>` (bound method)
   - Has `__self__` (the class) and `__func__`
   - When called: `Class.class_method(**kwargs)` → Python automatically passes `Class` as `cls`

4. **Standalone Function**: ✅ Works
   - Type: `<class 'function'>`
   - No `__self__` or `__func__`
   - When called: `function(**kwargs)` → No `self` needed

### Current Issue

**Problem**: When calling bound methods through FastAPI engine, getting error:
```
XWApiAgent.revive_auths() missing 1 required positional argument: 'self'
```

**Root Cause**: 
- When we call `action(**execution_kwargs)` where `action` is a bound method, Python should automatically pass `self` as the first argument to the wrapper function
- The wrapper function receives `*args` where `args[0]` should be `self`
- The wrapper then calls `self._execute_wrapper(func, *args, **kwargs)` which should pass `self` to the original function
- However, the wrapper's validation logic (lines 556-561) might be interfering with this

**Current Fix Attempts**:
1. ✅ Skip `self` and `cls` parameters in FastAPI request schema generation
2. ✅ Handle bound methods in `_execute_function` 
3. ✅ Call bound methods directly in FastAPI route handlers
4. ⚠️ Improved `self` detection in wrapper function (still investigating)

### Wrapper Function Logic

The XWAction wrapper function:
1. Receives `*args, **kwargs` where `args[0]` is `self` when called as bound method
2. For validation, creates `args_to_map = args[1:]` to skip `self` (line 561)
3. Calls `self._execute_wrapper(func, *args, **kwargs)` with ORIGINAL `args` (line 594)
4. `_execute_wrapper` calls `func(*args, **kwargs)` which should pass `self` correctly

**Issue**: The `self` detection logic at line 559 might be too restrictive and not detecting `XWApiAgent` instances correctly.

### Next Steps

1. ✅ Improve `self` detection to be more permissive (checking for `_name`, `__dict__`, etc.)
2. 🔄 Test if the improved detection works
3. If still failing, investigate if the wrapper is being called correctly as a bound method
4. Consider alternative approach: explicitly pass `self` when calling bound methods

## Code Locations

- **XWAction Decorator**: `xwaction/src/exonware/xwaction/facade.py` (lines 539-594)
- **FastAPI Engine**: `xwaction/src/exonware/xwaction/engines/fastapi.py` (lines 271-290, 330-343)
- **Base Engine**: `xwaction/src/exonware/xwaction/engines/base.py` (lines 70-112)

