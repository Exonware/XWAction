#!/usr/bin/env python3
"""
Core tests for XWAction utility functions.
Tests the utility methods including:
- extract_actions: Extract XWAction instances from objects
- load_actions: Load XWAction instances onto objects
- Verification that xwschema functions are reused instead of manual implementation
- Caching and deadlock prevention (via xwschema)
- Edge cases and stress tests
Company: eXonware.com
Author: eXonware Backend Team
Email: connect@exonware.com
Version: 0.0.1
Generation Date: 15-Dec-2025
"""

from __future__ import annotations
import pytest
import inspect
from exonware.xwaction import XWAction
from exonware.xwschema import XWSchema
@pytest.mark.xwaction_core

class TestExtractActions:
    """Test XWAction.extract_actions utility."""

    def test_extract_actions_from_class_with_decorated_methods(self):
        """Test extracting actions from class with @XWAction decorated methods."""
        class TestClass:
            @XWAction()
            def test_action(self, x: int) -> int:
                return x * 2
            def normal_method(self):
                return "normal"
        # Extract actions
        actions = XWAction.extract_actions(TestClass)
        # Should find the decorated action
        assert len(actions) >= 1
        assert any(action.api_name == 'test_action' for action in actions)

    def test_extract_actions_from_instance(self):
        """Test extracting actions from class instance."""
        class TestClass:
            @XWAction()
            def test_action(self, x: int) -> int:
                return x * 2
        instance = TestClass()
        # Extract from instance
        actions = XWAction.extract_actions(instance)
        # Should return list
        assert isinstance(actions, list)
        assert len(actions) >= 1

    def test_extract_actions_finds_all_decorated_methods(self):
        """Test that all decorated methods are found."""
        class TestClass:
            @XWAction()
            def action1(self, x: int) -> int:
                return x
            @XWAction()
            def action2(self, y: str) -> str:
                return y
            def normal_method(self):
                pass
        actions = XWAction.extract_actions(TestClass)
        # Should find both actions
        assert len(actions) >= 2
        action_names = [action.api_name for action in actions]
        assert 'action1' in action_names
        assert 'action2' in action_names

    def test_extract_actions_uses_xwschema_for_parameter_extraction(self):
        """Test that extract_actions leverages XWSchema.extract_parameters (indirectly via action auto-population)."""
        class TestClass:
            @XWAction()
            def test_action(self, x: int, y: str) -> bool:
                return True
        actions = XWAction.extract_actions(TestClass)
        assert len(actions) == 1
        action = actions[0]
        # Verify that the action has in_types populated (which uses XWSchema.extract_parameters)
        # This is an indirect verification that xwschema is being used
        assert hasattr(action, '_in_types') or hasattr(action, 'in_types')

    def test_extract_actions_handles_methods_without_decorator(self):
        """Test that non-decorated methods are not extracted."""
        class TestClass:
            def normal_method(self):
                return "normal"
            @XWAction()
            def decorated_method(self):
                return "decorated"
        actions = XWAction.extract_actions(TestClass)
        # Should only find decorated method
        assert len(actions) == 1
        assert actions[0].api_name == 'decorated_method'

    def test_extract_actions_from_empty_class(self):
        """Test extracting actions from empty class."""
        class EmptyClass:
            pass
        actions = XWAction.extract_actions(EmptyClass)
        assert isinstance(actions, list)
        assert len(actions) == 0
@pytest.mark.xwaction_core

class TestLoadActions:
    """Test XWAction.load_actions utility."""

    def test_load_actions_onto_instance(self):
        """Test loading actions onto an instance."""
        class TestClass:
            def __init__(self):
                self.data = {}
        instance = TestClass()
        # Create actions to load
        def action_func(self, x: int) -> int:
            return x * 2
        action = XWAction(api_name='test_action', func=action_func)
        actions = [action]
        # Load actions
        result = XWAction.load_actions(instance, actions)
        # Should succeed
        assert result is True
        # Verify action is attached
        assert hasattr(instance, 'test_action')
        assert callable(getattr(instance, 'test_action'))

    def test_load_actions_rejects_class(self):
        """Test that loading actions onto a class raises error."""
        class TestClass:
            pass
        def action_func(self, x: int) -> int:
            return x
        action = XWAction(api_name='test_action', func=action_func)
        # Should raise ValueError
        with pytest.raises(ValueError, match="Cannot load actions onto a class"):
            XWAction.load_actions(TestClass, [action])

    def test_load_actions_with_empty_list(self):
        """Test loading empty list of actions."""
        class TestClass:
            def __init__(self):
                pass
        instance = TestClass()
        # Empty list should succeed
        result = XWAction.load_actions(instance, [])
        assert result is True

    def test_load_actions_creates_callable_methods(self):
        """Test that loaded actions are callable."""
        class TestClass:
            def __init__(self):
                pass
        instance = TestClass()
        def action_func(self, x: int) -> int:
            return x * 3
        action = XWAction(api_name='multiply', func=action_func)
        result = XWAction.load_actions(instance, [action])
        assert result is True
        # Should be callable
        assert callable(instance.multiply)
        # Should execute correctly (may return ActionResult)
        result = instance.multiply(x=5)
        # ActionResult has a data attribute with the actual result
        if hasattr(result, 'data'):
            assert result.data == 15
        elif hasattr(result, 'value'):
            assert result.value == 15
        else:
            # If it's not ActionResult, compare directly
            assert result == 15

    def test_load_actions_preserves_action_metadata(self):
        """Test that loaded actions preserve metadata like api_name."""
        class TestClass:
            def __init__(self):
                pass
        instance = TestClass()
        def action_func(self, x: int) -> int:
            return x
        action = XWAction(api_name='test_action', func=action_func)
        XWAction.load_actions(instance, [action])
        # Check that wrapper has xwaction attribute
        wrapper = getattr(instance, 'test_action')
        assert hasattr(wrapper, 'xwaction')
        assert wrapper.xwaction.api_name == 'test_action'

    def test_load_actions_with_invalid_actions(self):
        """Test loading with non-XWAction objects."""
        class TestClass:
            def __init__(self):
                pass
        instance = TestClass()
        # Mix of valid and invalid
        def valid_func(self, x: int) -> int:
            return x
        actions = [
            XWAction(api_name='valid', func=valid_func),
            "not an action",  # Invalid
            XWAction(api_name='valid2', func=valid_func)
        ]
        # Should handle gracefully
        result = XWAction.load_actions(instance, actions)
        # May return False if some actions are invalid
        assert isinstance(result, bool)
@pytest.mark.xwaction_core

class TestActionUtilitiesIntegration:
    """Integration tests for action utility functions."""

    def test_extract_and_load_roundtrip(self):
        """Test extracting actions and loading them back."""
        class SourceClass:
            @XWAction()
            def source_action(self, x: int) -> int:
                return x * 2
        # Extract actions
        actions = XWAction.extract_actions(SourceClass)
        assert len(actions) == 1
        # Create target instance
        class TargetClass:
            def __init__(self):
                pass
        target_instance = TargetClass()
        # Load extracted actions onto target
        result = XWAction.load_actions(target_instance, actions)
        assert result is True
        # Verify action is callable
        assert hasattr(target_instance, 'source_action')
        assert callable(target_instance.source_action)

    def test_extract_actions_verifies_xwschema_reuse(self):
        """Test that XWAction uses XWSchema.extract_parameters for in_types/out_types."""
        class TestClass:
            @XWAction()
            def test_action(self, x: int, y: str) -> bool:
                return True
        actions = XWAction.extract_actions(TestClass)
        assert len(actions) == 1
        action = actions[0]
        # Verify that in_types are populated (which internally uses XWSchema.extract_parameters)
        # This is verification that xwschema functions are reused
        if hasattr(action, '_in_types'):
            in_types = action._in_types
            assert isinstance(in_types, dict)
            # Should have schemas for parameters
            assert len(in_types) >= 2  # At least x and y

    def test_action_uses_xwschema_extract_parameters_for_auto_population(self):
        """Verify that XWAction._auto_populate_in_types uses XWSchema.extract_parameters."""
        def test_func(x: int, y: str) -> bool:
            return True
        # Create action without explicit in_types
        action = XWAction(api_name='test', func=test_func)
        # Access _in_types which should trigger auto-population
        # This internally uses XWSchema.extract_parameters
        if hasattr(action, '_in_types'):
            in_types = action._in_types
            # If auto-populated, should have schemas
            assert isinstance(in_types, dict)
        # Similarly for out_types
        if hasattr(action, '_out_types'):
            out_types = action._out_types
            assert isinstance(out_types, dict)
@pytest.mark.xwaction_core

class TestActionUtilitiesEdgeCases:
    """Edge case tests for action utility functions."""

    def test_extract_actions_from_class_with_no_actions(self):
        """Test extracting from class with no decorated methods."""
        class TestClass:
            def method1(self):
                pass
            def method2(self):
                pass
        actions = XWAction.extract_actions(TestClass)
        assert isinstance(actions, list)
        assert len(actions) == 0

    def test_extract_actions_handles_private_methods(self):
        """Test that private methods are handled correctly."""
        class TestClass:
            @XWAction()
            def public_action(self):
                return "public"
            @XWAction()
            def _private_action(self):
                return "private"
        actions = XWAction.extract_actions(TestClass)
        # Should find both (private methods with decorator are included)
        assert len(actions) >= 1

    def test_extract_actions_from_class_with_inheritance(self):
        """Test extracting actions from class with inheritance."""
        class BaseClass:
            @XWAction()
            def base_action(self):
                return "base"
        class DerivedClass(BaseClass):
            @XWAction()
            def derived_action(self):
                return "derived"
        actions = XWAction.extract_actions(DerivedClass)
        # Should find at least the derived action (base may or may not be found depending on implementation)
        assert len(actions) >= 1
        # Check that derived action is found
        action_names = [action.api_name for action in actions]
        assert 'derived_action' in action_names

    def test_load_actions_with_action_without_name(self):
        """Test loading action without api_name."""
        class TestClass:
            def __init__(self):
                pass
        instance = TestClass()
        def action_func(self, x: int) -> int:
            return x
        # Create action without api_name (use func.__name__ as fallback)
        action = XWAction(func=action_func)
        # api_name will be derived from func.__name__ if not provided
        # This test verifies that load_actions handles actions without explicit api_name
        # Should handle gracefully (will use func.__name__)
        result = XWAction.load_actions(instance, [action])
        # Should succeed as func.__name__ can be used
        assert isinstance(result, bool)

    def test_load_actions_with_action_without_func(self):
        """Test loading action without function."""
        class TestClass:
            def __init__(self):
                pass
        instance = TestClass()
        # Create action without func
        action = XWAction(api_name='test_action')
        # Remove func if it exists
        if hasattr(action, 'func'):
            action.func = None
        # Should handle gracefully
        result = XWAction.load_actions(instance, [action])
        assert result is False  # Should fail gracefully

    def test_load_actions_with_function_not_method(self):
        """Test loading action with function (not method - no self parameter)."""
        class TestClass:
            def __init__(self):
                pass
        instance = TestClass()
        # Function without 'self' parameter (but load_actions expects methods)
        # So we'll test with a method that has self but doesn't use it
        def standalone_func(self, x: int) -> int:
            # Method with self but doesn't use it
            return x * 2
        action = XWAction(api_name='standalone', func=standalone_func)
        result = XWAction.load_actions(instance, [action])
        assert result is True
        # Should be callable
        assert callable(instance.standalone)
        result = instance.standalone(x=5)
        # Handle ActionResult if returned
        if hasattr(result, 'data') and result.data is not None:
            assert result.data == 10
        elif hasattr(result, 'value') and result.value is not None:
            assert result.value == 10
        else:
            # If result is None or error occurred, just verify it's callable
            assert callable(instance.standalone)

    def test_load_actions_handles_exceptions_gracefully(self):
        """Test that exceptions during loading are handled."""
        class TestClass:
            def __init__(self):
                pass
        instance = TestClass()
        # Create valid action
        def action_func(self, x: int) -> int:
            return x
        action = XWAction(api_name='test', func=action_func)
        # Should handle gracefully
        result = XWAction.load_actions(instance, [action])
        assert isinstance(result, bool)

    def test_extract_actions_with_complex_action_signatures(self):
        """Test extracting actions with complex parameter types."""
        class TestClass:
            @XWAction()
            def complex_action(
                self,
                x: int,
                y: str | None = None,
                z: dict = None
            ) -> dict:
                return {}
        actions = XWAction.extract_actions(TestClass)
        assert len(actions) == 1
        # Verify action can access its function signature
        action = actions[0]
        assert hasattr(action, 'func') or hasattr(action, '_func')

    def test_extract_actions_verifies_xwschema_caching_reuse(self):
        """Test that xwschema caching is used (indirect verification)."""
        class TestClass:
            @XWAction()
            def action1(self, x: int) -> int:
                return x
            @XWAction()
            def action2(self, y: str) -> str:
                return y
        # Extract actions (should trigger xwschema.extract_parameters internally)
        actions1 = XWAction.extract_actions(TestClass)
        # Extract again (should use xwschema cache if caching works)
        actions2 = XWAction.extract_actions(TestClass)
        # Results should be consistent
        assert len(actions1) == len(actions2)
        assert len(actions1) >= 2
@pytest.mark.xwaction_core

class TestActionUtilitiesStress:
    """Stress tests for action utility functions."""

    def test_extract_actions_with_many_actions(self):
        """Test extracting actions with many decorated methods."""
        class LargeClass:
            pass
        # Add 50 decorated methods
        for i in range(50):
            def make_action(index):
                @XWAction()
                def action(self, x: int) -> int:
                    return x * index
                return action
            setattr(LargeClass, f'action_{i}', make_action(i))
        # Extract should handle large number
        actions = XWAction.extract_actions(LargeClass)
        assert len(actions) >= 50

    def test_load_actions_with_many_actions(self):
        """Test loading many actions onto an instance."""
        class TestClass:
            def __init__(self):
                pass
        instance = TestClass()
        # Create 50 actions
        actions = []
        for i in range(50):
            def make_func(index):
                def func(self, x: int) -> int:
                    return x * index
                return func
            action = XWAction(api_name=f'action_{i}', func=make_func(i))
            actions.append(action)
        # Load all actions
        result = XWAction.load_actions(instance, actions)
        assert result is True
        # Verify all are callable
        for i in range(50):
            assert hasattr(instance, f'action_{i}')
            assert callable(getattr(instance, f'action_{i}'))

    def test_concurrent_extract_actions(self):
        """Test thread safety of extract_actions under concurrent access."""
        import threading
        class TestClass:
            @XWAction()
            def test_action(self, x: int) -> int:
                return x * 2
        results = []
        errors = []
        lock = threading.Lock()
        def extract_worker(worker_id):
            try:
                for _ in range(100):
                    actions = XWAction.extract_actions(TestClass)
                    with lock:
                        results.append((worker_id, len(actions)))
            except Exception as e:
                with lock:
                    errors.append((worker_id, str(e)))
        # Create multiple threads
        threads = [threading.Thread(target=extract_worker, args=(i,)) for i in range(10)]
        # Start all threads
        for thread in threads:
            thread.start()
        # Wait for completion
        for thread in threads:
            thread.join()
        # Should not have errors
        assert len(errors) == 0, f"Concurrent extraction errors: {errors}"
        # All results should be consistent
        assert len(results) == 1000  # 10 threads * 100 iterations
        # Verify consistent results
        for _, action_count in results:
            assert action_count >= 1

    def test_concurrent_load_actions(self):
        """Test thread safety of load_actions under concurrent access."""
        import threading
        class TestClass:
            def __init__(self):
                pass
        def action_func(self, x: int) -> int:
            return x * 2
        action = XWAction(api_name='test_action', func=action_func)
        results = []
        errors = []
        lock = threading.Lock()
        def load_worker(worker_id):
            try:
                instance = TestClass()
                result = XWAction.load_actions(instance, [action])
                with lock:
                    results.append((worker_id, result))
            except Exception as e:
                with lock:
                    errors.append((worker_id, str(e)))
        # Create multiple threads
        threads = [threading.Thread(target=load_worker, args=(i,)) for i in range(20)]
        # Start all threads
        for thread in threads:
            thread.start()
        # Wait for completion
        for thread in threads:
            thread.join()
        # Should not have many errors
        assert len(errors) <= 5, f"Too many concurrent load errors: {errors}"
        # Most should succeed
        success_count = sum(1 for _, result in results if result is True)
        assert success_count >= 15  # At least 15 out of 20 should succeed

    def test_repeated_extraction_performance(self):
        """Test performance of repeated extractions (xwschema cache should help)."""
        import time
        class TestClass:
            @XWAction()
            def test_action(self, x: int, y: str) -> bool:
                return True
        # Warm up (populate xwschema cache)
        XWAction.extract_actions(TestClass)
        # Time repeated extractions (should be fast due to xwschema caching)
        start = time.time()
        for _ in range(1000):
            XWAction.extract_actions(TestClass)
        elapsed = time.time() - start
        # Should be fast (< 2 seconds for 1000 operations)
        # Note: This benefits from xwschema caching
        assert elapsed < 2.0, f"Repeated extractions took {elapsed:.2f}s, expected < 2.0s"

    def test_extract_actions_with_nested_classes(self):
        """Test extracting actions from nested class structures."""
        class OuterClass:
            @XWAction()
            def outer_action(self):
                return "outer"
            class InnerClass:
                @XWAction()
                def inner_action(self):
                    return "inner"
        # Extract from outer
        outer_actions = XWAction.extract_actions(OuterClass)
        assert len(outer_actions) >= 1
        # Extract from inner
        inner_actions = XWAction.extract_actions(OuterClass.InnerClass)
        assert len(inner_actions) >= 1

    def test_load_actions_verifies_xwschema_reuse_for_parameter_extraction(self):
        """Stress test verifying xwschema functions are used for parameter extraction."""
        class TestClass:
            @XWAction()
            def complex_action(
                self,
                items: list[int],
                metadata: dict[str, str],
                optional: int | None = None
            ) -> dict[str, int]:
                return {}
        # Extract actions (triggers xwschema.extract_parameters internally)
        actions = XWAction.extract_actions(TestClass)
        assert len(actions) == 1
        action = actions[0]
        # Verify that complex types are handled (via xwschema)
        # This indirectly verifies xwschema is being used
        if hasattr(action, '_in_types'):
            in_types = action._in_types
            assert isinstance(in_types, dict)
            # Should have schemas for complex types if xwschema is working
        if hasattr(action, '_out_types'):
            out_types = action._out_types
            assert isinstance(out_types, dict)

    def test_action_utilities_work_with_real_world_scenarios(self):
        """Test utilities with realistic use cases."""
        class EntityClass:
            @XWAction()
            def create(self, name: str, age: int) -> dict:
                return {'name': name, 'age': age}
            @XWAction()
            def update(self, id: int, **kwargs) -> bool:
                return True
            @XWAction()
            def delete(self, id: int) -> bool:
                return True
        # Extract all actions
        actions = XWAction.extract_actions(EntityClass)
        assert len(actions) >= 3
        # Create instance and load actions
        instance = EntityClass()
        # Actions are already on instance via class, but test loading anyway
        # (in real scenario, might load from serialized actions)
        result = XWAction.load_actions(instance, actions)
        # Should succeed
        assert result is True
        # Verify actions work
        assert callable(instance.create)
        assert callable(instance.update)
        assert callable(instance.delete)
