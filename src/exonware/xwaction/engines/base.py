#exonware/xwaction/engines/base.py
"""
XWAction Engine Base Classes
Abstract base classes for action engine implementations.
"""

import sys
import inspect
import asyncio
from typing import Any, Callable, Optional, get_type_hints
from .contracts import IActionEngine
from .defs import ActionEngineType
from ..context import ActionContext, ActionResult
from exonware.xwsystem import get_logger
logger = get_logger(__name__)
from pydantic import BaseModel, create_model, Field


class AActionEngineBase(IActionEngine):
    """
    Abstract Action Engine Base
    Provides common functionality for action engine implementations.
    """

    def __init__(self, name: str, engine_type: ActionEngineType, priority: int = 0):
        self._name = name
        self._engine_type = engine_type
        self._priority = priority
        self._metrics = {
            "executions": 0,
            "errors": 0,
            "total_duration": 0.0,
            "setup_time": 0.0
        }
        self._enabled = True
    @property

    def name(self) -> str:
        return self._name
    @property

    def engine_type(self) -> ActionEngineType:
        return self._engine_type
    @property

    def priority(self) -> int:
        return self._priority

    def setup(self, config: dict[str, Any]) -> bool:
        """Default setup implementation."""
        return True

    def teardown(self) -> bool:
        """Default teardown implementation."""
        return True

    def get_metrics(self) -> dict[str, Any]:
        """Get base metrics."""
        return self._metrics.copy()

    def _update_metrics(self, duration: float, success: bool = True):
        """Update execution metrics."""
        self._metrics["executions"] += 1
        self._metrics["total_duration"] += duration
        if not success:
            self._metrics["errors"] += 1

    def _execute_function(self, action: Any, instance: Any, **kwargs) -> Any:
        """
        Execute the action function directly.
        This is a common pattern used by multiple engines to execute
        action functions with proper instance handling.
        Args:
            action: The action object with a 'func' attribute, or a bound method
            instance: Optional entity instance (self in decorated method)
            **kwargs: Function arguments
        Returns:
            Function execution result
        Raises:
            ValueError: If action has no function to execute
        """
        # Check if action itself is a bound method (when action is the method from getattr)
        if hasattr(action, '__self__') and hasattr(action, '__func__'):
            # Action is a bound method - use it directly
            kwargs.pop('self', None)  # Remove 'self' from kwargs if present
            return action(**kwargs)
        # Otherwise, action should have a 'func' attribute
        if not hasattr(action, 'func') or not action.func:
            raise ValueError("Action has no function to execute")
        # Check if func is a bound method (has __self__ attribute)
        # Bound methods already have 'self' bound, so we shouldn't pass instance again
        is_bound_method = hasattr(action.func, '__self__')
        if is_bound_method:
            # For bound methods, don't pass instance - it's already bound
            # Also remove 'self' from kwargs if it exists (shouldn't happen, but safety check)
            kwargs.pop('self', None)
            return action.func(**kwargs)
        elif instance is not None:
            # For unbound methods, pass instance as first argument
            return action.func(instance, **kwargs)
        else:
            # Standalone function, no instance needed
            return action.func(**kwargs)

    async def _execute_function_async(self, action: Any, instance: Any, **kwargs) -> Any:
        """
        Execute the action function asynchronously.
        Handles both sync and async functions transparently. 
        Sync functions are run in a separate thread to avoid blocking the event loop.
        """
        # 1. Resolve the function and instance
        func = getattr(action, 'func', None)
        bound_method = None
        # Case A: 'action' itself is the bound method
        if hasattr(action, '__self__') and hasattr(action, '__func__'):
             func = action.__func__
             bound_method = action
             kwargs.pop('self', None)
        elif not func:
             raise ValueError("Action has no function to execute")
        # Case B: 'action.func' is a bound method
        elif hasattr(func, '__self__'):
             bound_method = func
             kwargs.pop('self', None)
        # 2. Determine execution callable
        to_call = None
        is_coro = False
        if bound_method:
            to_call = lambda: bound_method(**kwargs)
            is_coro = inspect.iscoroutinefunction(bound_method)
        elif instance is not None:
            # Unbound function + instance
            to_call = lambda: func(instance, **kwargs)
            is_coro = inspect.iscoroutinefunction(func)
        else:
            # Plain function
            to_call = lambda: func(**kwargs)
            is_coro = inspect.iscoroutinefunction(func)
        # 3. Execute
        if is_coro:
            # It's an async function, call and await
            if bound_method: return await bound_method(**kwargs)
            if instance: return await func(instance, **kwargs)
            return await func(**kwargs)
        else:
            # It's a sync function, run in thread to be safe
            return await asyncio.to_thread(to_call)

    def _fallback_execution(self, action: Any, context: ActionContext, 
                            instance: Any, **kwargs) -> ActionResult:
        """
        Fallback to native execution when engine-specific execution is not available.
        This is a common pattern used by engines that require external dependencies
        (FastAPI, Celery, Prefect) to fall back to native execution when those
        dependencies are not available or not initialized.
        Args:
            action: The action to execute
            context: Execution context
            instance: The entity instance (self in decorated method)
            **kwargs: Action parameters
        Returns:
            ActionResult from native execution
        """
        from .native import NativeActionEngine
        native_engine = NativeActionEngine()
        return native_engine.execute(action, context, instance, **kwargs)

    def _resolve_type_hints(self, func: Callable) -> dict[str, Any]:
        """
        Safely resolve type hints for a function.
        This utility is useful for engines that need type information for:
        - Serialization/deserialization
        - Validation
        - Documentation generation
        - Model creation (Pydantic, etc.)
        Handles module context to resolve forward references properly.
        Args:
            func: The function to resolve type hints for
        Returns:
            Dictionary mapping parameter names to their resolved type annotations
        """
        try:
            func_module = sys.modules.get(func.__module__) if hasattr(func, '__module__') else None
            globalns = func_module.__dict__ if func_module else None
            return get_type_hints(func, globalns=globalns, include_extras=True)
        except Exception as e:
            logger.debug(f"Could not fully resolve type hints for {func.__name__}: {e}")
            # Fallback: inspect signature for basic annotations
            return {
                k: v.annotation 
                for k, v in inspect.signature(func).parameters.items() 
                if v.annotation != inspect.Parameter.empty
            }

    def _is_pydantic_compatible(self, annotation: Any) -> bool:
        """
        Check if a type is a Data Type (serializable) or a Service Type (ignored).
        """
        if annotation is Any or annotation is inspect.Parameter.empty:
            return True
        # Common service types to exclude from serialization
        non_serializable_patterns = [
            'requests.sessions.Session',
            'requests.Session',
            'sqlalchemy.orm.session.Session',
            'fastapi.requests.Request',
            'fastapi.responses.Response',
            'fastapi.background.BackgroundTasks',
            'starlette.requests.Request',
            'starlette.responses.Response',
            'starlette.background.BackgroundTasks'
        ]
        annotation_str = str(annotation)
        if hasattr(annotation, '__module__') and hasattr(annotation, '__name__'):
            module = getattr(annotation, '__module__', '')
            name = getattr(annotation, '__name__', '')
            if any(pattern in f"{module}.{name}" for pattern in non_serializable_patterns):
                return False
        return True

    def _create_input_model(self, api_name: str, fields: dict[str, Any], 
                           module: Optional[str] = None) -> Optional[Any]:
        """
        Generic helper to create a Pydantic model for input validation.
        Returns None if Pydantic is not installed.
        """
        if not fields:
            return None
        try:
            model_kwargs = {"__module__": module} if module else {}
            RequestModel = create_model(
                f"{api_name}_Input",
                **model_kwargs,
                **fields
            )
            # Attempt rebuild if possible
            if hasattr(RequestModel, 'model_rebuild'):
                try:
                    if module and module in sys.modules:
                         rebuild_globals = sys.modules[module].__dict__.copy()
                         RequestModel.model_rebuild(types_namespace=rebuild_globals)
                    else:
                         RequestModel.model_rebuild()
                except Exception:
                    pass
            return RequestModel
        except Exception as e:
            logger.warning(f"Failed to create input model for {api_name}: {e}")
            return None
