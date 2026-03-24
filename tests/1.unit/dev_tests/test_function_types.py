#!/usr/bin/env python3
"""
Test script to investigate how XWAction handles different function types:
1. Instance methods (bound methods)
2. Static methods
3. Class methods
4. Standalone functions
"""

import inspect
from exonware.xwaction import XWAction, ActionProfile

# Test 1: Instance Method


class SampleClass:
    def __init__(self):
        self.value = "instance"

    @XWAction(operationId="instance_method", profile=ActionProfile.COMMAND)
    def instance_method(self, param: str) -> str:
        """Instance method that requires self."""
        return f"{self.value}: {param}"


# Test 2: Static Method


class SampleClassStatic:
    @staticmethod
    @XWAction(operationId="static_method", profile=ActionProfile.COMMAND)
    def static_method(param: str) -> str:
        """Static method - no self or cls."""
        return f"static: {param}"


# Test 3: Class Method


class SampleClassClass:
    @classmethod
    @XWAction(operationId="class_method", profile=ActionProfile.COMMAND)
    def class_method(cls, param: str) -> str:
        """Class method that requires cls."""
        return f"{cls.__name__}: {param}"


# Test 4: Standalone Function


@XWAction(operationId="standalone_function", profile=ActionProfile.COMMAND)
def standalone_function(param: str) -> str:
    """Standalone function - no self or cls."""
    return f"standalone: {param}"


def investigate_function(func, name: str):
    """Investigate a function's properties."""
    print(f"\n{'='*60}")
    print(f"Investigating: {name}")
    print(f"{'='*60}")
    print(f"Type: {type(func)}")
    print(f"Is function: {inspect.isfunction(func)}")
    print(f"Is method: {inspect.ismethod(func)}")
    print(f"Is bound method: {hasattr(func, '__self__') and hasattr(func, '__func__')}")
    if hasattr(func, "__self__"):
        print(f"Has __self__: {func.__self__}")
    if hasattr(func, "__func__"):
        print(f"Has __func__: {func.__func__}")
    if hasattr(func, "__wrapped__"):
        print(f"Has __wrapped__: {func.__wrapped__}")
    if hasattr(func, "xwaction"):
        print(f"Has xwaction: {func.xwaction}")
    if hasattr(func, "func"):
        print(f"Has func: {func.func}")
    # Get signature
    try:
        sig = inspect.signature(func)
        print(f"Signature: {sig}")
        params = list(sig.parameters.keys())
        print(f"Parameters: {params}")
        if params:
            print(f"First parameter: {params[0]}")
    except Exception as e:
        print(f"Error getting signature: {e}")


# Test all function types
if __name__ == "__main__":
    print("XWAction Function Type Investigation")
    print("=" * 60)

    # Test instance method
    obj = SampleClass()
    instance_method = obj.instance_method
    investigate_function(instance_method, "Instance Method (bound)")

    # Test static method
    static_method = SampleClassStatic.static_method
    investigate_function(static_method, "Static Method")

    # Test class method
    class_method = SampleClassClass.class_method
    investigate_function(class_method, "Class Method (bound)")

    # Test standalone function
    investigate_function(standalone_function, "Standalone Function")

    # Test calling them
    print(f"\n{'='*60}")
    print("Testing Function Calls")
    print(f"{'='*60}")
    try:
        result1 = instance_method("test1")
        print(f"Instance method result: {result1}")
    except Exception as e:
        print(f"Instance method error: {e}")
    try:
        result2 = static_method("test2")
        print(f"Static method result: {result2}")
    except Exception as e:
        print(f"Static method error: {e}")
    try:
        result3 = class_method("test3")
        print(f"Class method result: {result3}")
    except Exception as e:
        print(f"Class method error: {e}")
    try:
        result4 = standalone_function("test4")
        print(f"Standalone function result: {result4}")
    except Exception as e:
        print(f"Standalone function error: {e}")

